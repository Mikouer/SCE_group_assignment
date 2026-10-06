import json
from html import escape
import subprocess
import sys
from pathlib import Path

import pytest
import requests

from md2xwiki.client import Client, PublicMetadataAuth, RemotePage
from md2xwiki.cli import main
from md2xwiki.config import MANIFEST, load_config
from md2xwiki.destinations import file_config, tree_config
from md2xwiki.errors import PublishError
from md2xwiki.references import Reference
from md2xwiki.model import page_hash
from md2xwiki.renderer import compile_tree
from md2xwiki.sync import Operation, Publisher, encode

from conftest import WikiSession, response, xml_body

PROJECT = "https://wiki.example/xwiki/wiki/course/view"


def page(path, name, body=""):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(f"---\npageName: {name}\n---\n{body}", encoding="utf-8")
    return path


def node(folder, file, children=()):
    folder.mkdir(parents=True, exist_ok=True)
    folder.joinpath("index.yaml").write_text(
        f"pageText: {file}\nchildren:\n" + "".join(f"  - {c}\n" for c in children)
        if children else f"pageText: {file}\nchildren: []\n"
    )


def client_for(config, monkeypatch):
    monkeypatch.setenv("XWIKI_USERNAME", "Publisher")
    monkeypatch.setenv("XWIKI_PASSWORD", "test-only")
    monkeypatch.delenv("XWIKI_EXPECTED_USER", raising=False)
    session = WikiSession(config)
    client = Client(config, session)
    client.probe()
    return client, session


def test_yaml_tree_uses_headers_not_filenames_or_folders(tmp_path):
    root = tmp_path / "arbitrary-folder"
    node(root, "not-the-page-name.md", ["different-leaf.md", "branch-folder"])
    page(root / "not-the-page-name.md", "3. Evaluation",
         "# Overview\n[leaf](different-leaf.md) [branch](branch-folder/)\n")
    page(root / "different-leaf.md", "a. Artifacts", "# Artifacts\n")
    branch = root / "branch-folder"
    node(branch, "whatever.md", ["leaf.md"])
    page(branch / "whatever.md", "b. Reports")
    page(branch / "leaf.md", "Report 01", "# Report\n")
    page(root / "unlisted.md", "Must not publish", "# Unlisted\n")
    build = compile_tree(tree_config(root, PROJECT))
    assert {p.reference.spaces for p in build.pages} == {
        ("3. Evaluation",), ("3. Evaluation", "a. Artifacts"),
        ("3. Evaluation", "b. Reports"), ("3. Evaluation", "b. Reports", "Report 01"),
    }
    assert all("pageName" not in p.content for p in build.pages)
    assert r"doc:course:3\. Evaluation.a\. Artifacts.WebHome" in build.pages[0].content
    assert r"doc:course:3\. Evaluation.b\. Reports.WebHome" in build.pages[0].content
    assert build.by_source[Path("branch-folder")].preserve_content


@pytest.mark.parametrize("name", ["Main", "Foundation", "2. Specification", "3. Evaluation", "Other"])
def test_no_foundation_special_case(tmp_path, name):
    node(tmp_path, "page.md")
    page(tmp_path / "page.md", name, "# Example\n")
    assert compile_tree(tree_config(tmp_path, PROJECT)).pages[0].reference.spaces == (name,)


def test_project_root_prefix_is_respected(tmp_path):
    node(tmp_path, "root.md")
    page(tmp_path / "root.md", "Nested")
    build = compile_tree(tree_config(tmp_path, PROJECT + "/Existing%20parent/"))
    assert build.pages[0].reference.spaces == ("Existing parent", "Nested")


def test_file_destination_is_authoritative(tmp_path):
    file = page(tmp_path / "unrelated-file-name.md", "Unrelated metadata", "# Example\n")
    url = PROJECT + "/3.%20Evaluation/a.%20Prototype/a.1.Artifact%20AT-01/"
    build = compile_tree(file_config(file, url))
    assert len(build.pages) == 1
    assert build.pages[0].reference.spaces == (
        "3. Evaluation", "a. Prototype", "a.1.Artifact AT-01"
    )
    assert build.pages[0].reference.endpoint.endswith(
        "/spaces/3.%20Evaluation/spaces/a.%20Prototype/spaces/a.1.Artifact%20AT-01/pages/WebHome"
    )


def test_header_only_existing_page_is_completely_untouched(tmp_path, monkeypatch):
    file = page(tmp_path / "container.md", "Metadata name")
    config = file_config(file, PROJECT + "/Provided/")
    client, session = client_for(config, monkeypatch)
    ref = config.roots[0].reference
    before = RemotePage("Human title", "xwiki/2.0", "Keep this content\n")
    session.pages[ref] = before
    publisher = Publisher(compile_tree(config), client, tmp_path / "output")
    plan = publisher.preflight()
    assert not plan.operations
    publisher.apply(plan)
    assert session.pages[ref] == before
    assert not any(method == "PUT" and url.endswith(ref.endpoint)
                   for method, url, kwargs in session.calls)
    session.pages[ref] = RemotePage("Updated human title", "xwiki/2.0", "Human edit\n")
    assert not publisher.preflight().operations


def test_header_only_missing_page_is_created_empty(tmp_path, monkeypatch):
    file = page(tmp_path / "container.md", "Container")
    config = file_config(file, PROJECT + "/Container/")
    client, session = client_for(config, monkeypatch)
    publisher = Publisher(compile_tree(config), client, tmp_path / "output")
    publisher.apply(publisher.preflight())
    ref = config.roots[0].reference
    assert session.pages[ref] == RemotePage("Container", "xwiki/2.1", "")
    assert not publisher.preflight().operations


def test_legacy_pending_escaped_title_recovers_without_rewriting_page(tmp_path, monkeypatch):
    file = page(tmp_path / "concept.md", "Communication & Interaction", "# Replacement\n")
    config = file_config(file, PROJECT + "/Concept/")
    client, session = client_for(config, monkeypatch)
    ref = config.roots[0].reference
    original = RemotePage("Communication & Interaction", "xwiki/2.1", "Original content\n")
    session.pages[ref] = original
    publisher = Publisher(compile_tree(config), client, tmp_path / "output")
    plan = publisher.preflight()
    state = plan.states[ref]
    compiled = publisher.build.pages[0]
    # The old client used the display title in both its payload and pending hashes.
    stored = RemotePage(escape(original.title), compiled.syntax, compiled.content)
    state.pending = Operation("page", ref,
                              page_hash(escape(original.title), original.syntax, original.content),
                              stored.hash)
    session.assets[(ref, MANIFEST)] = encode(state.json(config))
    session.pages[ref] = stored
    resumed = Publisher(compile_tree(config), client, tmp_path / "resumed")
    recovery = resumed.preflight()
    assert not recovery.operations
    assert recovery.states[ref].pending is None
    assert recovery.states[ref].pages[ref].hash == stored.hash
    resumed.apply(recovery)
    assert session.pages[ref] == stored
    assert not any(method == "PUT" and url.endswith(ref.endpoint)
                   for method, url, kwargs in session.calls)
    verification = resumed.preflight()
    assert not verification.operations
    assert not any(state.dirty for state in verification.states.values())


def test_preserved_empty_raw_title_refreshes_legacy_display_title_baseline(
        tmp_path, monkeypatch):
    file = page(tmp_path / "overview.md", "Container")
    config = file_config(file, PROJECT + "/Container/")
    client, session = client_for(config, monkeypatch)
    ref = config.roots[0].reference
    stored = RemotePage("", "xwiki/2.1", "= Existing overview =\n")
    session.pages[ref] = stored
    publisher = Publisher(compile_tree(config), client, tmp_path / "output")
    initial = publisher.preflight()
    initial.states[ref].pages[ref].hash = page_hash(
        "Existing overview", stored.syntax, stored.content)
    session.assets[(ref, MANIFEST)] = encode(initial.states[ref].json(config))
    recovery = publisher.preflight()
    assert not recovery.operations
    assert recovery.states[ref].pages[ref].hash == stored.hash
    assert recovery.states[ref].dirty
    publisher.apply(recovery)
    assert session.pages[ref] == stored
    assert not any(method == "PUT" and url.endswith(ref.endpoint)
                   for method, url, kwargs in session.calls)
    assert not any(state.dirty for state in publisher.preflight().states.values())


def test_push_tree_creates_missing_root_and_children_and_preserves_titles(tmp_path, monkeypatch):
    node(tmp_path, "overview.md", ["child.md"])
    page(tmp_path / "overview.md", "Root", "# Root\n")
    page(tmp_path / "child.md", "Child", "# Body\n")
    config = tree_config(tmp_path, PROJECT)
    client, session = client_for(config, monkeypatch)
    other = Reference(config.wiki, ("Unmanaged",))
    session.pages[other] = RemotePage("Other", "xwiki/2.1", "Do not touch")
    publisher = Publisher(compile_tree(config), client, tmp_path / "output")
    publisher.apply(publisher.preflight())
    assert {ref.spaces for ref in session.pages} == {("Root",), ("Root", "Child"), ("Unmanaged",)}
    assert (tmp_path / "output/bootstrap.json").exists()
    assert not publisher.preflight().operations


def test_config_derives_all_roots_from_headers(tmp_path):
    for directory, name in [("one", "Main"), ("two", "2. Specification"), ("three", "3. Evaluation")]:
        node(tmp_path / "docs" / directory, "whatever.md")
        page(tmp_path / "docs" / directory / "whatever.md", name)
    config_path = tmp_path / "xwiki.toml"
    config_path.write_text(
        f'[xwiki]\nproject_root="{PROJECT}"\nsource="docs"\nlayout="yaml"\n'
        'deployment_id="course-markdown"\n'
        '[[roots]]\nsource="one"\n[[roots]]\nsource="two"\n[[roots]]\nsource="three"\n'
    )
    config = load_config(config_path)
    assert {root.reference.spaces for root in config.roots} == {
        ("Main",), ("2. Specification",), ("3. Evaluation",)
    }
    assert len(compile_tree(config).pages) == 3


def test_yaml_multi_root_creation_recovers_with_distinct_bootstrap_journals(
        tmp_path, monkeypatch):
    for directory in ("one", "two"):
        node(tmp_path / "docs" / directory, "root.md")
        page(tmp_path / "docs" / directory / "root.md", directory, "# New root\n")
    config_path = tmp_path / "xwiki.toml"
    config_path.write_text(
        f'[xwiki]\nproject_root="{PROJECT}"\nsource="docs"\nlayout="yaml"\n'
        'deployment_id="multi-root"\n'
        '[[roots]]\nsource="one"\n[[roots]]\nsource="two"\n'
    )
    config = load_config(config_path)
    client, session = client_for(config, monkeypatch)
    publisher = Publisher(compile_tree(config), client, tmp_path / "output")
    def fail(method, endpoint, kwargs):
        if method == "PUT" and endpoint.endswith("/attachments/.md2xwiki-manifest.json"):
            return response(403)
    session.fail = fail
    with pytest.raises(PublishError, match="403"):
        publisher.apply(publisher.preflight())
    assert len(session.pages) == 1
    session.fail = None
    publisher.apply(publisher.preflight())
    assert {ref.spaces for ref in session.pages} == {("one",), ("two",)}
    assert len(list((publisher.output / "bootstrap").glob("*.json"))) == 2
    plan = publisher.preflight()
    assert not plan.operations
    assert not any(state.dirty for state in plan.states.values())


@pytest.mark.parametrize("contents", [
    "# Missing header\n", "---\ntitle: Missing name\n---\n",
    "---\npageName: one\npageName: two\n---\n",
    "---\npageName: ../escape\n---\n", "---\npageName: Name\n",
])
def test_invalid_front_matter_fails_offline(tmp_path, contents):
    file = tmp_path / "page.md"
    file.write_text(contents)
    with pytest.raises(PublishError):
        file_config(file, PROJECT + "/Target/")


@pytest.mark.parametrize("contents", [
    "pageText: ''\n", "pageText: page.md\nchildren: [../outside]\n",
    "pageText: page.md\nchildren: [missing.md]\n",
    "pageText: page.md\nchildren: [child, child]\n",
    "pageText: page.md\nchildren: [page.md]\n",
    "pageText: page.md\nunknown: true\n",
])
def test_invalid_yaml_tree_fails_offline(tmp_path, contents):
    page(tmp_path / "page.md", "Root", "# Root\n")
    (tmp_path / "index.yaml").write_text(contents)
    with pytest.raises(PublishError):
        compile_tree(tree_config(tmp_path, PROJECT))


def test_missing_branch_index_is_an_error(tmp_path):
    node(tmp_path, "root.md", ["child"])
    page(tmp_path / "root.md", "Root")
    (tmp_path / "child").mkdir()
    with pytest.raises(PublishError, match="index.yaml"):
        compile_tree(tree_config(tmp_path, PROJECT))


def test_duplicate_destination_names_fail_offline(tmp_path):
    node(tmp_path, "root.md", ["one.md", "two.md"])
    page(tmp_path / "root.md", "Root")
    page(tmp_path / "one.md", "Duplicate")
    page(tmp_path / "two.md", "Duplicate")
    with pytest.raises(PublishError, match="Duplicate"):
        compile_tree(tree_config(tmp_path, PROJECT))


def test_source_line_number_includes_front_matter(tmp_path):
    file = page(tmp_path / "page.md", "Target", "# Example\n[bad](missing.md)\n")
    with pytest.raises(PublishError, match="page.md:5:"):
        compile_tree(file_config(file, PROJECT + "/Target/"))


def test_probe_does_not_use_main_wiki_identity(tmp_path, monkeypatch):
    file = page(tmp_path / "page.md", "Target")
    config = file_config(file, PROJECT + "/Target/")
    monkeypatch.setenv("XWIKI_USERNAME", "Publisher")
    monkeypatch.setenv("XWIKI_PASSWORD", "test-only")
    monkeypatch.delenv("XWIKI_EXPECTED_USER", raising=False)
    session = WikiSession(config)
    def fail(method, endpoint, kwargs):
        if endpoint == "/":
            assert isinstance(kwargs["auth"], PublicMetadataAuth)
            result = response(body=xml_body("xwiki", [("version", "18.7.0")]))
            result.headers.pop("xwiki-user")
            return result
        if endpoint == "/wikis/course":
            assert kwargs["auth"] == ("Publisher", "test-only")
            result = response(body=xml_body("wiki", [("id", "course")]))
            result.headers["xwiki-user"] = "course:XWiki.Publisher"
            return result
    session.fail = fail
    client = Client(config, session)
    assert client.probe() == "18.7.0"
    assert client.identity == "course:XWiki.Publisher"


def test_public_discovery_removes_authorization_header():
    prepared = requests.Request("GET", "https://wiki.example",
                                headers={"Authorization": "not-a-real-token"}).prepare()
    PublicMetadataAuth()(prepared)
    assert "Authorization" not in prepared.headers


def test_cli_prune_is_available_only_for_tree_and_configured_sync():
    for command in ("push-tree", "sync", "pipeline"):
        result = subprocess.run([sys.executable, "-m", "md2xwiki.cli", command, "--help"],
                                check=True, capture_output=True, text=True)
        assert "--prune" in result.stdout
    result = subprocess.run([sys.executable, "-m", "md2xwiki.cli", "push-file", "--help"],
                            check=True, capture_output=True, text=True)
    assert "--prune" not in result.stdout


def test_push_file_rejects_prune_before_connecting(monkeypatch, tmp_path):
    monkeypatch.setattr("sys.argv", ["md2xwiki", "push-file", "--file",
                                    str(tmp_path / "page.md"), "--destination",
                                    PROJECT + "/Target/", "--prune"])
    monkeypatch.setattr("md2xwiki.cli.Client", lambda config: pytest.fail("Must not connect"))
    with pytest.raises(SystemExit) as error:
        main()
    assert error.value.code == 2


@pytest.mark.parametrize("command", ["push-tree", "push-file"])
def test_push_commands_execute_shared_publishing_and_verification(
        tmp_path, monkeypatch, command):
    folder = tmp_path / "tree"
    file = page(folder / "overview.md", "Root", "# Replacement\n")
    if command == "push-tree":
        node(folder, file.name, ["child.md"])
        page(folder / "child.md", "Child", "# Child\n")
        config = tree_config(folder, PROJECT)
        arguments = ["--root", str(folder), "--project-root", PROJECT]
    else:
        config = file_config(file, PROJECT + "/Exact%20destination/")
        arguments = ["--file", str(file), "--destination", PROJECT + "/Exact%20destination/"]
    client, session = client_for(config, monkeypatch)
    root = config.roots[0].reference
    session.pages[root] = RemotePage("Keep existing title", "xwiki/2.1", "Replace this")
    unrelated = Reference(config.wiki, (*root.spaces, "Unrelated"))
    before = RemotePage("Human child", "xwiki/2.1", "Do not change")
    session.pages[unrelated] = before
    monkeypatch.setattr("md2xwiki.cli.Client", lambda config: client)
    output = tmp_path / "output"
    monkeypatch.setattr("sys.argv", ["md2xwiki", command, *arguments, "--output", str(output)])
    assert main() == 0
    summary = json.loads((output / "summary.json").read_bytes())
    assert summary["status"] == "verified"
    assert summary["verification"]["operations"] == []
    assert session.pages[root].title == "Keep existing title"
    assert "Replacement" in session.pages[root].content
    assert session.pages[unrelated] == before
    assert list((output / "backups").glob("*.xml"))
    assert not any(method == "DELETE" for method, url, kwargs in session.calls)


def test_missing_identity_explains_guest_not_expected_user_override(tmp_path, monkeypatch):
    file = page(tmp_path / "page.md", "Target")
    config = file_config(file, PROJECT + "/Target/")
    monkeypatch.setenv("XWIKI_USERNAME", "Publisher")
    monkeypatch.setenv("XWIKI_PASSWORD", "test-only")
    monkeypatch.delenv("XWIKI_EXPECTED_USER", raising=False)
    session = WikiSession(config)
    def fail(method, endpoint, kwargs):
        if endpoint == "/wikis/course":
            result = response(body=xml_body("wiki", [("id", "course")]))
            result.headers.pop("xwiki-user")
            return result
    session.fail = fail
    with pytest.raises(PublishError, match="REST treated the request as Guest") as error:
        Client(config, session).probe()
    assert "cannot fix an unauthenticated request" in str(error.value)
    assert not any(method != "GET" for method, url, kwargs in session.calls)


def test_legacy_uuid_configuration_remains_readable(tmp_path):
    name = "md2xwiki-test-" + "a" * 32
    config_path = tmp_path / "xwiki.toml"
    config_path.write_text(
        '[xwiki]\nbase_url="https://wiki.example/xwiki"\nwiki="sce2026group05"\n'
        f'source="source"\ndeployment_id="{name}"\nmode="temporary"\n'
        f'[[roots]]\nsource="."\nspaces=["Main","{name}"]\n'
    )
    assert load_config(config_path).roots[0].reference.spaces == ("Main", name)
