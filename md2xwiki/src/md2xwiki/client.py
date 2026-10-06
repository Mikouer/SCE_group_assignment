import os
import time
import xml.etree.ElementTree as ET
from dataclasses import dataclass
from typing import Callable
from urllib.parse import quote

import requests

from .config import Config
from .errors import PublishError
from .model import digest, page_hash
from .references import Reference

NS = "http://www.xwiki.org"
ET.register_namespace("", NS)
TRANSIENT = {429, 500, 502, 503, 504}


class PublicMetadataAuth(requests.auth.AuthBase):
    def __call__(self, request: requests.PreparedRequest) -> requests.PreparedRequest:
        request.headers.pop("Authorization", None)
        return request


def xml(response: requests.Response, name: str) -> ET.Element:
    if "xml" not in response.headers.get("Content-Type", "").lower():
        raise PublishError(f"Expected REST XML {name}, not HTML/login or another content type")
    if b"<!DOCTYPE" in response.content.upper() or b"<!ENTITY" in response.content.upper():
        raise PublishError("DTD/entity declarations are not accepted in REST XML")
    try:
        element = ET.fromstring(response.content)
    except ET.ParseError as exc:
        raise PublishError(f"Malformed REST XML {name}") from exc
    if element.tag != f"{{{NS}}}{name}":
        raise PublishError(f"Expected REST XML {name}, got {element.tag}")
    return element


def text(element: ET.Element, name: str) -> str:
    child = element.find(f"{{{NS}}}{name}")
    if child is None:
        raise PublishError(f"REST XML is missing {name}")
    return child.text or ""


@dataclass(frozen=True)
class RemotePage:
    title: str
    syntax: str
    content: str

    @property
    def hash(self) -> str:
        return page_hash(self.title, self.syntax, self.content)

    def body(self) -> bytes:
        element = ET.Element(f"{{{NS}}}page")
        for name, value in (
            ("title", self.title), ("syntax", self.syntax), ("content", self.content)
        ):
            ET.SubElement(element, f"{{{NS}}}{name}").text = value
        return ET.tostring(element, encoding="utf-8", xml_declaration=True)


class Client:
    def __init__(self, config: Config, session: requests.Session | None = None):
        self.config = config
        self.base = config.base_url + "/rest"
        self.session = session or requests.Session()
        username = os.environ.get("XWIKI_USERNAME")
        password = os.environ.get("XWIKI_PASSWORD")
        if not username or not password:
            raise PublishError("Set XWIKI_USERNAME and XWIKI_PASSWORD as runtime environment variables")
        self.session.auth = (username, password)
        self.session.headers["Accept"] = "application/xml"
        self.expected_user = os.environ.get("XWIKI_EXPECTED_USER") or username
        self.identity: str | None = None
        self.token: str | None = None

    def close(self) -> None:
        self.session.close()

    def request(self, method: str, endpoint: str, *, data: bytes | None = None,
                mime: str = "application/xml", missing: bool = False,
                retry_reads: bool = True, public_metadata: bool = False) -> requests.Response:
        if public_metadata and (method != "GET" or endpoint not in {"/", "/syntaxes"}):
            raise PublishError("Only read-only server metadata can use anonymous discovery")
        token_retry = False
        attempts = 3 if method == "GET" and retry_reads else 1
        for attempt in range(attempts):
            while True:
                headers = {"Content-Type": mime}
                if self.token:
                    headers["XWiki-Form-Token"] = self.token
                try:
                    response = self.session.request(
                        method, self.base + endpoint, data=data, headers=headers,
                        timeout=(5, 30), allow_redirects=False,
                        auth=PublicMetadataAuth() if public_metadata else self.session.auth,
                    )
                except requests.RequestException as exc:
                    if isinstance(exc, requests.exceptions.SSLError):
                        raise PublishError(f"{method} {endpoint}: TLS verification failed; "
                                           "configure an approved CA bundle, never disable TLS") from exc
                    if isinstance(exc, (requests.Timeout, requests.ConnectionError)):
                        if attempt + 1 < attempts:
                            time.sleep(2 ** attempt)
                            break
                        raise TransportError(f"{method} {endpoint}: connection/timeout failure") from exc
                    raise PublishError(f"{method} {endpoint}: HTTP transport failure") from exc
                self.token = response.headers.get("XWiki-Form-Token", self.token)
                identity = response.headers.get("xwiki-user")
                if self.identity and not public_metadata and identity != self.identity:
                    raise PublishError("Authenticated REST identity changed or disappeared")
                if (response.status_code == 403
                        and response.content.strip() == b"Invalid or missing form token."
                        and not token_retry and self.token):
                    token_retry = True
                    continue
                if response.status_code in TRANSIENT:
                    if attempt + 1 < attempts:
                        time.sleep(2 ** attempt)
                        break
                    raise TransportError(f"{method} {endpoint}: HTTP {response.status_code}")
                if 300 <= response.status_code < 400 and response.status_code != 304:
                    raise PublishError(f"{method} {endpoint}: redirect refused (possible SSO/login)")
                if response.status_code == 404 and missing:
                    return response
                expected = {"GET": {200}, "PUT": {201, 202, 304}, "DELETE": {204}}
                if response.status_code not in expected[method]:
                    raise PublishError(f"{method} {endpoint}: HTTP {response.status_code}")
                return response
        raise PublishError(f"{method} {endpoint}: retry budget exhausted")

    def probe(self) -> str:
        root = xml(self.request("GET", "/", public_metadata=True), "xwiki")
        syntaxes = xml(self.request("GET", "/syntaxes", public_metadata=True), "syntaxes")
        if not any(e.text == "xwiki/2.1" for e in syntaxes.iter()):
            raise PublishError("Server does not advertise xwiki/2.1")
        endpoint = "/wikis/" + quote(self.config.wiki, safe="")
        response = self.request("GET", endpoint)
        xml(response, "wiki")
        identity = response.headers.get("xwiki-user", "").strip()
        expected = self.expected_user
        matches = identity == expected or (
            ":" not in expected and identity.split(":")[-1] == (
                expected if expected.startswith("XWiki.") else "XWiki." + expected
            )
        )
        if not identity or identity.split(":")[-1] in {"XWiki.Guest", "XWiki.XWikiGuest"}:
            raise PublishError(
                f"GET {endpoint}: no authenticated xwiki-user (REST treated the request as Guest). "
                "Check the username/password, account access to this wiki and Basic authentication. "
                "Enter the actual username, without Markdown escape backslashes. "
                "XWIKI_EXPECTED_USER cannot fix an unauthenticated request."
            )
        if not matches:
            raise PublishError(
                f"GET {endpoint}: authenticated xwiki-user={identity!r}, expected {expected!r}. "
                "If this is your service account's actual reference, set XWIKI_EXPECTED_USER "
                "to that exact reference; otherwise correct the account."
            )
        self.identity = identity
        return text(root, "version")

    def get_page(self, reference: Reference) -> RemotePage | None:
        response = self.request("GET", reference.endpoint, missing=True)
        if response.status_code == 404:
            return None
        page = xml(response, "page")
        return RemotePage(text(page, "rawTitle"), text(page, "syntax"), text(page, "content"))

    def get_attachment(self, reference: Reference, name: str) -> bytes | None:
        response = self.request("GET", reference.attachment_endpoint(name), missing=True)
        if response.status_code == 404:
            return None
        if "text/html" in response.headers.get("Content-Type", "").lower():
            raise PublishError("Attachment download returned HTML/login instead of attachment bytes")
        return response.content

    def mutate(self, method: str, endpoint: str, read_hash: Callable[[], str | None],
               before: str | None, after: str | None, *, data: bytes | None = None,
               mime: str = "application/xml") -> None:
        for attempt in range(3):
            current = read_hash()
            if current == after:
                return
            if current != before:
                raise PublishError(f"Remote drift immediately before {method} {endpoint}")
            try:
                response = self.request(method, endpoint, data=data, mime=mime)
                if response.status_code not in {204, 304}:
                    xml(response, "page" if "/attachments/" not in endpoint else "attachment")
            except TransportError:
                current = read_hash()
                if current == after:
                    return
                if current != before:
                    raise PublishError(f"Ambiguous write changed {endpoint}; refusing retry")
                if attempt == 2:
                    raise
                time.sleep(2 ** attempt)
                continue
            actual = read_hash()
            if actual != after:
                raise PublishError(f"Read-back mismatch after {method} {endpoint}; "
                                   f"expected hash {after}, got {actual}")
            return

    def page_hash(self, reference: Reference) -> str | None:
        page = self.get_page(reference)
        return page.hash if page else None

    def attachment_hash(self, reference: Reference, name: str) -> str | None:
        data = self.get_attachment(reference, name)
        return digest(data) if data is not None else None

    def put_page(self, reference: Reference, page: RemotePage, before: str | None) -> None:
        self.mutate("PUT", reference.endpoint, lambda: self.page_hash(reference),
                    before, page.hash, data=page.body())

    def put_attachment(self, reference: Reference, name: str, data: bytes,
                       mime: str, before: str | None) -> None:
        self.mutate("PUT", reference.attachment_endpoint(name),
                    lambda: self.attachment_hash(reference, name), before, digest(data),
                    data=data, mime=mime)

    def delete_attachment(self, reference: Reference, name: str, before: str) -> None:
        self.mutate("DELETE", reference.attachment_endpoint(name),
                    lambda: self.attachment_hash(reference, name), before, None)

    def delete_page(self, reference: Reference, before: str) -> None:
        self.mutate("DELETE", reference.endpoint, lambda: self.page_hash(reference), before, None)

    def attachments(self, reference: Reference) -> set[str]:
        found: set[str] = set()
        start = 0
        while True:
            response = self.request("GET", reference.endpoint + f"/attachments?start={start}&number=100")
            root = xml(response, "attachments")
            if any(e.tag not in {f"{{{NS}}}attachment", f"{{{NS}}}link"} for e in root):
                raise PublishError("Unexpected attachment inventory shape")
            elements = root.findall(f"{{{NS}}}attachment")
            names = [text(e, "name") for e in elements]
            if len(set(names)) != len(names) or found.intersection(names):
                raise PublishError("Attachment pagination repeated resources")
            found.update(names)
            if len(elements) < 100:
                return found
            start += 100
            if start > 100000:
                raise PublishError("Attachment inventory exceeded safe pagination limit")

    def children(self, reference: Reference) -> list[Reference]:
        result = []
        seen = set()
        start = 0
        while True:
            response = self.request("GET", reference.endpoint
                                    + f"/children?hierarchy=nestedpages&start={start}&number=100")
            root = xml(response, "pages")
            if any(e.tag not in {f"{{{NS}}}pageSummary", f"{{{NS}}}link"} for e in root):
                raise PublishError("Unexpected child inventory shape")
            elements = root.findall(f"{{{NS}}}pageSummary")
            for element in elements:
                # Parse REST href segments rather than splitting escaped display names.
                from urllib.parse import unquote, urlsplit
                links = element.findall(f"{{{NS}}}link")
                href = next((e.get("href", "") for e in links
                             if e.get("rel") == NS + "/rel/page"), "")
                parsed = urlsplit(href)
                if parsed.netloc != urlsplit(self.base).netloc:
                    raise PublishError("Child inventory returned another server's reference")
                path = parsed.path
                prefix = urlsplit(self.base).path + "/wikis/"
                if not path.startswith(prefix):
                    raise PublishError("Child inventory returned an invalid REST reference")
                parts = path[len(prefix):].split("/")
                if (len(parts) < 5 or len(parts) % 2 != 1 or parts[-2] != "pages"
                        or any(parts[i] != "spaces" for i in range(1, len(parts) - 2, 2))):
                    raise PublishError("Child inventory returned an invalid nested page endpoint")
                child = Reference(unquote(parts[0]), tuple(
                    unquote(parts[i]) for i in range(2, len(parts) - 2, 2)
                ), unquote(parts[-1]))
                if not child.within(reference) or child == reference or child in seen:
                    raise PublishError("Child inventory escaped scope or repeated a page")
                seen.add(child)
                result.append(child)
            if len(elements) < 100:
                return result
            start += 100
            if start > 100000:
                raise PublishError("Child inventory exceeded safe pagination limit")

    def has_annotations(self, reference: Reference) -> bool:
        for resource in ("objects", "comments", "translations"):
            response = self.request("GET", reference.endpoint + "/" + resource
                                    + "?start=0&number=1")
            root = xml(response, resource)
            members = [e for e in root if e.tag != f"{{{NS}}}link"]
            if resource == "translations":
                members = [e for e in members if not (
                    e.tag == f"{{{NS}}}translation" and "default" in root.attrib
                    and e.get("language") == root.get("default")
                )]
            if members:
                return True
        page = xml(self.request("GET", reference.endpoint + "?class=true"), "page")
        class_element = page.find(f"{{{NS}}}class")
        return class_element is not None and class_element.find(f"{{{NS}}}property") is not None


class TransportError(PublishError):
    """A transient/ambiguous request; mutations require read-back before retry."""
