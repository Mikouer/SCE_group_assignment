import xml.etree.ElementTree as ET

import pytest
import requests

from md2xwiki.client import Client, NS, RemotePage, xml
from md2xwiki.errors import PublishError
from md2xwiki.references import Reference

from conftest import WikiSession, page_response, response, xml_body


def test_authenticated_probe_and_request_shape(wiki, temporary_config):
    client, session = wiki
    assert client.identity == "xwiki:XWiki.Publisher"
    assert session.auth == ("Publisher", "not-a-real-password")
    ref = temporary_config.roots[0].reference
    client.put_page(ref, RemotePage("T", "xwiki/2.1", "<&>"), None)
    puts = [c for c in session.calls if c[0] == "PUT"]
    assert len(puts) == 1
    kwargs = puts[0][2]
    assert kwargs["timeout"] == (5, 30)
    assert kwargs["allow_redirects"] is False
    assert kwargs["headers"]["XWiki-Form-Token"] == "token"
    body = ET.fromstring(kwargs["data"])
    assert body.find(f"{{{NS}}}content").text == "<&>"
    assert client.get_page(ref).content == "<&>"

def test_empty_optional_expected_identity_falls_back_to_username(temporary_config, monkeypatch):
    monkeypatch.setenv("XWIKI_USERNAME", "Publisher")
    monkeypatch.setenv("XWIKI_PASSWORD", "test")
    monkeypatch.setenv("XWIKI_EXPECTED_USER", "")
    session = WikiSession(temporary_config)
    assert Client(temporary_config, session).probe() == "18.7.0"


@pytest.mark.parametrize("title", [
    "Communication & Interaction", 'Quotes "and" <tags>',
    "Literal &amp; stays literal", "**Unrendered wiki title**", "",
])
def test_page_roundtrip_verifies_stored_title_not_rendered_title(wiki, title):
    client, session = wiki
    ref = session.config.roots[0].reference
    desired = RemotePage(title, "xwiki/2.1", "Keep literal &amp; content\n")
    client.put_page(ref, desired, None)
    assert client.get_page(ref) == desired
    assert client.page_hash(ref) == desired.hash
    count = len([call for call in session.calls if call[0] == "PUT"])
    client.put_page(ref, desired, desired.hash)
    assert len([call for call in session.calls if call[0] == "PUT"]) == count


def test_empty_raw_title_is_not_replaced_with_derived_display_title(wiki):
    client, session = wiki
    ref = session.config.roots[0].reference
    session.fail = lambda *args: response(body=xml_body("page", [
        ("title", "Derived from the heading"), ("rawTitle", ""),
        ("syntax", "xwiki/2.1"), ("content", "= Heading =\n"),
    ]))
    assert client.get_page(ref) == RemotePage("", "xwiki/2.1", "= Heading =\n")


def test_page_without_raw_title_fails_instead_of_using_rendered_title(wiki):
    client, session = wiki
    session.fail = lambda *args: response(body=xml_body("page", [
        ("title", "Rendered &amp; title"), ("syntax", "xwiki/2.1"), ("content", "Body"),
    ]))
    with pytest.raises(PublishError, match="missing rawTitle"):
        client.get_page(session.config.roots[0].reference)


@pytest.mark.parametrize("field", ["title", "syntax", "content"])
def test_readback_rejects_changes_to_stored_page_fields(wiki, field):
    client, session = wiki
    ref = session.config.roots[0].reference
    desired = RemotePage("Communication & Interaction", "xwiki/2.1", "Body")
    fields = dict(title=desired.title, syntax=desired.syntax, content=desired.content)
    fields[field] = "Changed remotely"
    changed = RemotePage(**fields)
    def fail(method, endpoint, kwargs):
        if method == "PUT":
            session.pages[ref] = changed
            return page_response(changed, 201)
    session.fail = fail
    with pytest.raises(PublishError, match="Read-back mismatch") as error:
        client.put_page(ref, desired, None)
    assert desired.hash in str(error.value)
    assert changed.hash in str(error.value)
    assert len([call for call in session.calls if call[0] == "PUT"]) == 1


@pytest.mark.parametrize("status", [401, 403, 302])
def test_auth_errors_redirects_fail_without_retries(wiki, status):
    client, session = wiki
    session.fail = lambda *args: response(status)
    count = len(session.calls)
    with pytest.raises(PublishError):
        client.get_page(session.config.roots[0].reference)
    assert len(session.calls) == count + 1


def test_specific_token_failure_retries_once(wiki):
    client, session = wiki
    attempts = 0
    def fail(method, endpoint, kwargs):
        nonlocal attempts
        attempts += 1
        if attempts == 1:
            result = response(403, b"Invalid or missing form token.", "text/plain")
            result.headers["XWiki-Form-Token"] = "fresh"
            return result
        assert kwargs["headers"]["XWiki-Form-Token"] == "fresh"
        return response(404)
    session.fail = fail
    assert client.get_page(session.config.roots[0].reference) is None
    assert attempts == 2


def test_repeated_invalid_token_stops(wiki):
    client, session = wiki
    session.fail = lambda *args: response(403, b"Invalid or missing form token.", "text/plain")
    count = len(session.calls)
    with pytest.raises(PublishError):
        client.get_page(session.config.roots[0].reference)
    assert len(session.calls) == count + 2


@pytest.mark.parametrize("body,mime", [
    (b"<html>Login</html>", "text/html"), (b"<page", "application/xml"),
    (b'<page xmlns="wrong"/>', "application/xml"),
    (b'<!DOCTYPE page [<!ENTITY secret "x">]><page/>', "application/xml"),
])
def test_html_malformed_xml_and_entities_are_not_success(wiki, body, mime):
    client, session = wiki
    session.fail = lambda *args: response(200, body, mime)
    with pytest.raises(PublishError):
        client.get_page(session.config.roots[0].reference)


@pytest.mark.parametrize("identity", ["xwiki:XWiki.Guest", "", "xwiki:XWiki.SomeoneElse"])
def test_wrong_identity_is_rejected(temporary_config, monkeypatch, identity):
    monkeypatch.setenv("XWIKI_USERNAME", "Publisher")
    monkeypatch.setenv("XWIKI_PASSWORD", "test")
    session = WikiSession(temporary_config)
    def fail(method, endpoint, kwargs):
        if not endpoint.startswith("/wikis/"):
            return None
        result = response(body=xml_body("wiki", [("id", temporary_config.wiki)]))
        result.headers["xwiki-user"] = identity
        return result
    session.fail = fail
    with pytest.raises(PublishError, match="identity|xwiki-user"):
        Client(temporary_config, session).probe()


@pytest.mark.parametrize("status", [429, 500, 502, 503, 504])
def test_bounded_transient_read_retry(wiki, status):
    client, session = wiki
    count = 0
    def fail(*args):
        nonlocal count
        count += 1
        return response(status) if count < 3 else response(404)
    session.fail = fail
    assert client.get_page(session.config.roots[0].reference) is None
    assert count == 3


def test_timeout_after_successful_write_is_reconciled(wiki):
    client, session = wiki
    ref = session.config.roots[0].reference
    desired = RemotePage("Test", "xwiki/2.1", "content")
    def fail(method, endpoint, kwargs):
        if method == "PUT":
            session.pages[ref] = desired
            raise requests.ReadTimeout("timed out after write")
    session.fail = fail
    client.put_page(ref, desired, None)
    assert len([c for c in session.calls if c[0] == "PUT"]) == 1


def test_timeout_before_write_is_retried_after_readback(wiki):
    client, session = wiki
    ref = session.config.roots[0].reference
    attempts = 0
    def fail(method, endpoint, kwargs):
        nonlocal attempts
        if method == "PUT":
            attempts += 1
            if attempts == 1:
                raise requests.ReadTimeout("no write")
    session.fail = fail
    client.put_page(ref, RemotePage("T", "xwiki/2.1", "C"), None)
    assert attempts == 2


def test_drift_before_mutation_prevents_put(wiki):
    client, session = wiki
    ref = session.config.roots[0].reference
    session.pages[ref] = RemotePage("Manual", "xwiki/2.1", "edit")
    with pytest.raises(PublishError, match="drift"):
        client.put_page(ref, RemotePage("T", "xwiki/2.1", "C"), None)
    assert not [c for c in session.calls if c[0] == "PUT"]


def test_children_are_paginated_by_nested_references(wiki):
    client, session = wiki
    root = session.config.roots[0].reference
    for i in range(101):
        session.pages[Reference(root.wiki, (*root.spaces, f"a. {i}"))] = RemotePage(
            str(i), "xwiki/2.1", ""
        )
    result = client.children(root)
    assert len(result) == 101
    urls = [url for method, url, kwargs in session.calls if "/children?" in url]
    assert len(urls) == 2
    assert all("hierarchy=nestedpages" in url and "number=100" in url for url in urls)
    assert "start=100" in urls[-1]


def test_attachment_pagination(wiki):
    client, session = wiki
    root = session.config.roots[0].reference
    for i in range(101):
        session.assets[(root, f"{i}.txt")] = b"data"
    assert len(client.attachments(root)) == 101


def test_tls_errors_are_actionable_not_retried(wiki):
    client, session = wiki
    def fail(*args):
        raise requests.exceptions.SSLError("untrusted CA")
    session.fail = fail
    count = len(session.calls)
    with pytest.raises(PublishError, match="TLS verification failed"):
        client.get_page(session.config.roots[0].reference)
    assert len(session.calls) == count + 1


def test_default_language_is_not_an_extra_translation(wiki):
    client, session = wiki
    ref = session.config.roots[0].reference
    session.pages[ref] = RemotePage("Test", "xwiki/2.1", "content")
    def fail(method, endpoint, kwargs):
        if endpoint.endswith("/translations"):
            return response(body=(
                b'<translations xmlns="http://www.xwiki.org" default="en">'
                b'<translation language="en"/></translations>'
            ))
    session.fail = fail
    assert not client.has_annotations(ref)
