import shutil
from pathlib import Path
from urllib.parse import unquote, urlsplit
import xml.etree.ElementTree as ET

import pytest
import requests

from md2xwiki.cli import prepare_test
from md2xwiki.client import Client, NS, RemotePage
from md2xwiki.config import Config, load_config
from md2xwiki.references import Reference


@pytest.fixture
def temporary_config(tmp_path):
    fixture = Path(__file__).parent / "fixtures/smoke"
    prepare_test(tmp_path / "runs", fixture, "https://wiki.example/xwiki")
    run = Path((tmp_path / "runs/latest-test.txt").read_text().strip())
    return load_config(run / "xwiki.toml")


@pytest.fixture
def production_config(tmp_path):
    (tmp_path / "xwiki.toml").write_text(
        '[xwiki]\nbase_url="https://wiki.example/xwiki"\nwiki="sce2026group05"\n'
        'source="docs/xwiki"\ndeployment_id="sce2026group05-markdown"\n'
        '[[roots]]\nsource="1-foundation"\nspaces=["Main"]\ntitle="1. Foundation"\n'
        '[[roots]]\nsource="2-specification"\nspaces=["2. Specification"]\ntitle="2. Specification"\n'
        '[[roots]]\nsource="3-evaluation"\nspaces=["3. Evaluation"]\ntitle="3. Evaluation"\n'
    )
    for name in ("1-foundation", "2-specification", "3-evaluation"):
        directory = tmp_path / "docs/xwiki" / name
        directory.mkdir(parents=True)
        (directory / "index.md").write_text("# " + name + "\n")
    return load_config(tmp_path / "xwiki.toml")


def response(status=200, body=b"", mime="application/xml"):
    result = requests.Response()
    result.status_code = status
    result._content = body
    result.headers.update({"Content-Type": mime, "xwiki-user": "xwiki:XWiki.Publisher",
                           "XWiki-Form-Token": "token"})
    return result


def xml_body(name, values=()):
    element = ET.Element(f"{{{NS}}}{name}")
    for key, value in values:
        ET.SubElement(element, f"{{{NS}}}{key}").text = value
    return ET.tostring(element)


class WikiSession:
    """In-memory REST transport exercising the real client, not a fake publisher."""

    def __init__(self, config: Config):
        self.config = config
        self.headers = {}
        self.auth = None
        self.pages: dict[Reference, RemotePage] = {}
        self.assets: dict[tuple[Reference, str], bytes] = {}
        self.calls = []
        self.fail = None
        self.closed = False
        self.annotations = {}

    def close(self):
        self.closed = True

    def request(self, method, url, **kwargs):
        self.calls.append((method, url, kwargs))
        path = urlsplit(url).path
        prefix = urlsplit(self.config.base_url).path + "/rest"
        endpoint = path[len(prefix):]
        if self.fail:
            result = self.fail(method, endpoint, kwargs)
            if result is not None:
                return result
        if endpoint == "/":
            return response(body=xml_body("xwiki", [("version", "18.7.0")]))
        if endpoint == "/syntaxes":
            return response(body=xml_body("syntaxes", [("syntax", "xwiki/2.1")]))
        if endpoint == "/wikis/" + self.config.wiki:
            return response(body=xml_body("wiki", [("id", self.config.wiki)]))
        parts = endpoint.strip("/").split("/")
        spaces = []
        i = 2
        while parts[i] == "spaces":
            spaces.append(unquote(parts[i + 1]))
            i += 2
        assert parts[i] == "pages"
        reference = Reference(unquote(parts[1]), tuple(spaces), unquote(parts[i + 1]))
        tail = parts[i + 2:]
        if tail and tail[0] in {"objects", "comments", "translations"}:
            name = tail[0]
            return response(body=xml_body(name, self.annotations.get((reference, name), [])))
        if tail == ["children"]:
            root = ET.Element(f"{{{NS}}}pages")
            children = sorted(
                [r for r in self.pages if r.spaces[:-1] == reference.spaces],
                key=lambda r: r.document,
            )
            from urllib.parse import parse_qs
            start = int(parse_qs(urlsplit(url).query)["start"][0])
            for child in children[start:start + 100]:
                item = ET.SubElement(root, f"{{{NS}}}pageSummary")
                ET.SubElement(item, f"{{{NS}}}link", {
                    "rel": NS + "/rel/page",
                    "href": self.config.base_url + "/rest" + child.endpoint,
                })
            return response(body=ET.tostring(root))
        if tail == ["attachments"]:
            root = ET.Element(f"{{{NS}}}attachments")
            names = sorted(name for ref, name in self.assets if ref == reference)
            from urllib.parse import parse_qs
            start = int(parse_qs(urlsplit(url).query)["start"][0])
            for name in names[start:start + 100]:
                item = ET.SubElement(root, f"{{{NS}}}attachment")
                ET.SubElement(item, f"{{{NS}}}name").text = name
            return response(body=ET.tostring(root))
        if tail and tail[0] == "attachments":
            name = unquote(tail[1])
            key = (reference, name)
            if method == "GET":
                return response(200, self.assets[key], "application/octet-stream") if key in (
                    self.assets
                ) else response(404)
            if method == "PUT":
                if reference not in self.pages:
                    return response(404)
                code = 202 if key in self.assets else 201
                self.assets[key] = kwargs["data"]
                return response(code, xml_body("attachment", [("name", name)]))
            if method == "DELETE":
                self.assets.pop(key, None)
                return response(204)
        if method == "GET":
            return response(200, self.pages[reference].body()) if reference in (
                self.pages
            ) else response(404)
        if method == "PUT":
            root = ET.fromstring(kwargs["data"])
            assert {e.tag for e in root} == {
                f"{{{NS}}}title", f"{{{NS}}}syntax", f"{{{NS}}}content"
            }
            code = 202 if reference in self.pages else 201
            self.pages[reference] = RemotePage(*(
                root.find(f"{{{NS}}}{name}").text or "" for name in ("title", "syntax", "content")
            ))
            return response(code, self.pages[reference].body())
        if method == "DELETE":
            self.pages.pop(reference, None)
            self.assets = {key: value for key, value in self.assets.items() if key[0] != reference}
            return response(204)
        raise AssertionError((method, endpoint))


@pytest.fixture
def wiki(temporary_config, monkeypatch):
    monkeypatch.setenv("XWIKI_USERNAME", "Publisher")
    monkeypatch.setenv("XWIKI_PASSWORD", "not-a-real-password")
    monkeypatch.delenv("XWIKI_EXPECTED_USER", raising=False)
    monkeypatch.setattr("md2xwiki.client.time.sleep", lambda seconds: None)
    session = WikiSession(temporary_config)
    client = Client(temporary_config, session)
    client.probe()
    return client, session


@pytest.fixture
def production_wiki(production_config, monkeypatch):
    monkeypatch.setenv("XWIKI_USERNAME", "Publisher")
    monkeypatch.setenv("XWIKI_PASSWORD", "not-a-real-password")
    monkeypatch.delenv("XWIKI_EXPECTED_USER", raising=False)
    monkeypatch.setattr("md2xwiki.client.time.sleep", lambda seconds: None)
    session = WikiSession(production_config)
    for root in production_config.roots:
        session.pages[root.reference] = RemotePage(root.title, "xwiki/2.1", "Existing content\n")
    session.pages[Reference(production_config.wiki, ("0. Introduction",))] = RemotePage(
        "Introduction", "xwiki/2.1", "Do not modify"
    )
    client = Client(production_config, session)
    client.probe()
    return client, session
