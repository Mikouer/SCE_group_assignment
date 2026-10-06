import json
from dataclasses import replace
from pathlib import Path

import pytest

from md2xwiki.cli import main
from md2xwiki.client import RemotePage
from md2xwiki.config import MANIFEST, PageMapping
from md2xwiki.errors import PublishError
from md2xwiki.references import Reference
from md2xwiki.renderer import compile_tree
from md2xwiki.sync import Publisher

from conftest import response


def writes(session):
    return [c for c in session.calls if c[0] != "GET"]


def publish(config, client, tmp_path, **options):
    publisher = Publisher(compile_tree(config), client, tmp_path / "output")
    plan = publisher.preflight(**options)
    publisher.apply(plan)
    return publisher


def test_single_test_page_roundtrip_and_unchanged_rerun(temporary_config, wiki, tmp_path):
    client, session = wiki
    publisher = publish(temporary_config, client, tmp_path)
    root = temporary_config.roots[0].reference
    assert set(session.pages) == {root}
    assert len(session.assets) == 3
    state = json.loads(session.assets[(root, MANIFEST)])
    assert state["pending"] is None
    assert state["pages"][0]["hash"] == publisher.build.pages[0].hash
    count = len(writes(session))
    plan = publisher.preflight()
    assert plan.operations == []
    publisher.apply(plan)
    assert len(writes(session)) == count
    assert all(root.endpoint in url for method, url, kwargs in writes(session))


def test_preflight_is_readonly_even_without_manifests(temporary_config, wiki, tmp_path):
    client, session = wiki
    publisher = Publisher(compile_tree(temporary_config), client, tmp_path)
    plan = publisher.preflight()
    assert len(plan.operations) == 3
    assert not writes(session)


def test_explicit_test_destination_can_adopt_existing_page_with_backup(temporary_config, wiki, tmp_path):
    client, session = wiki
    root = temporary_config.roots[0].reference
    session.pages[root] = RemotePage("Unowned", "xwiki/2.1", "Existing")
    publisher = Publisher(compile_tree(temporary_config), client, tmp_path)
    plan = publisher.preflight()
    assert root in plan.backups
    assert not writes(session)
    publisher.apply(plan)
    assert list((tmp_path / "backups").glob("*.xml"))
    with pytest.raises(PublishError, match="existed before"):
        publisher.cleanup()


def test_manual_page_edit_and_explicit_overwrite_backup(temporary_config, wiki, tmp_path):
    client, session = wiki
    publisher = publish(temporary_config, client, tmp_path)
    root = temporary_config.roots[0].reference
    edited = RemotePage("Human edit", "xwiki/2.1", "Do not silently replace")
    session.pages[root] = edited
    count = len(writes(session))
    with pytest.raises(PublishError, match="Manual edit"):
        publisher.preflight()
    assert len(writes(session)) == count
    plan = publisher.preflight(overwrite=True)
    publisher.apply(plan)
    backups = list((publisher.output / "backups").glob("*.xml"))
    assert len(backups) == 1
    assert b"Do not silently replace" in backups[0].read_bytes()
    assert session.pages[root].hash == publisher.build.pages[0].hash


def test_manual_attachment_edit_fails(temporary_config, wiki, tmp_path):
    client, session = wiki
    publisher = publish(temporary_config, client, tmp_path)
    root = temporary_config.roots[0].reference
    asset = next(name for ref, name in session.assets if name != MANIFEST)
    session.assets[(root, asset)] = b"manual"
    with pytest.raises(PublishError, match="Manual attachment"):
        publisher.preflight()


@pytest.mark.parametrize("change", ["corrupt", "deployment", "boundary", "root"])
def test_manifest_corruption_and_identity_scope_rejected(temporary_config, wiki, tmp_path, change):
    client, session = wiki
    publisher = publish(temporary_config, client, tmp_path)
    root = temporary_config.roots[0].reference
    state = json.loads(session.assets[(root, MANIFEST)])
    if change == "corrupt":
        raw = b"not json"
    else:
        if change == "deployment":
            state["deployment_id"] = "another-publisher"
        elif change == "boundary":
            state["pages"][0]["spaces"] = ["0. Introduction"]
        else:
            state["root"] = ["Main"]
        raw = json.dumps(state).encode()
    session.assets[(root, MANIFEST)] = raw
    count = len(writes(session))
    with pytest.raises(PublishError):
        publisher.preflight()
    assert len(writes(session)) == count


def test_failed_manifest_save_after_page_create_recovers_locally(temporary_config, wiki, tmp_path):
    client, session = wiki
    publisher = Publisher(compile_tree(temporary_config), client, tmp_path)
    def fail(method, endpoint, kwargs):
        if method == "PUT" and endpoint.endswith("/attachments/" + MANIFEST):
            return response(403)
    session.fail = fail
    with pytest.raises(PublishError, match="403"):
        publisher.apply(publisher.preflight())
    root = temporary_config.roots[0].reference
    assert root in session.pages
    assert (tmp_path / "bootstrap.json").exists()
    assert (root, MANIFEST) not in session.assets
    session.fail = None
    publisher.apply(publisher.preflight())
    assert not publisher.preflight().operations
    publisher.cleanup()
    assert root not in session.pages


def test_explicit_existing_page_is_not_claimed_as_created(temporary_config, wiki, tmp_path):
    client, session = wiki
    build = compile_tree(temporary_config)
    root = temporary_config.roots[0].reference
    session.pages[root] = RemotePage(build.pages[0].title, "xwiki/2.1", build.pages[0].content)
    plan = Publisher(build, client, tmp_path).preflight()
    assert not plan.states[root].created_root
    assert not writes(session)


def test_fresh_run_cannot_take_over_test_page_and_explains_resume(
        temporary_config, wiki, tmp_path):
    client, session = wiki
    publish(temporary_config, client, tmp_path)
    config = replace(temporary_config, deployment_id="md2xwiki-test-" + "f" * 32)
    publisher = Publisher(compile_tree(config), client, tmp_path / "another-output")
    count = len(writes(session))
    with pytest.raises(PublishError, match="Resume the original test run directory"):
        publisher.preflight()
    assert len(writes(session)) == count


def test_journal_recovers_successful_asset_write_before_baseline_save(temporary_config, wiki, tmp_path):
    client, session = wiki
    publisher = Publisher(compile_tree(temporary_config), client, tmp_path)
    manifest_puts = 0
    def fail(method, endpoint, kwargs):
        nonlocal manifest_puts
        if method == "PUT" and endpoint.endswith("/attachments/" + MANIFEST):
            manifest_puts += 1
            if manifest_puts == 3:
                return response(403)
    session.fail = fail
    with pytest.raises(PublishError):
        publisher.apply(publisher.preflight())
    root = temporary_config.roots[0].reference
    state = json.loads(session.assets[(root, MANIFEST)])
    assert state["pending"]["kind"] == "attachment"
    assert len(session.assets) == 2
    session.fail = None
    publisher.apply(publisher.preflight())
    assert not publisher.preflight().operations


@pytest.mark.parametrize("blocker", ["page_edit", "asset_edit", "unmanaged_asset", "descendant",
                                   "objects", "comments", "translations"])
def test_cleanup_fail_closed(temporary_config, wiki, tmp_path, blocker):
    client, session = wiki
    publisher = publish(temporary_config, client, tmp_path)
    root = temporary_config.roots[0].reference
    if blocker == "page_edit":
        session.pages[root] = RemotePage("Human", "xwiki/2.1", "modified")
    elif blocker == "asset_edit":
        key = next(key for key in session.assets if key[1] != MANIFEST)
        session.assets[key] = b"modified"
    elif blocker == "unmanaged_asset":
        session.assets[(root, "human.txt")] = b"manual"
    elif blocker == "descendant":
        session.pages[Reference(root.wiki, (*root.spaces, "human"))] = RemotePage(
            "Human", "xwiki/2.1", "unmanaged"
        )
    else:
        session.annotations[(root, blocker)] = [("manual", "annotation")]
    count = len(writes(session))
    with pytest.raises(PublishError):
        publisher.cleanup()
    assert root in session.pages
    assert len(writes(session)) == count


def test_production_adoption_backups_and_scope(production_config, production_wiki, tmp_path):
    client, session = production_wiki
    untouched = Reference(production_config.wiki, ("0. Introduction",))
    before = session.pages[untouched]
    publisher = publish(production_config, client, tmp_path)
    assert session.pages[untouched] == before
    assert len(list((publisher.output / "backups").glob("*.xml"))) == 3
    assert not publisher.preflight().operations
    assert not any("/spaces/0." in url for method, url, kwargs in writes(session))
    with pytest.raises(PublishError, match="restricted"):
        publisher.cleanup()


def test_unmanaged_child_collision_aborts_before_root_writes(production_config, production_wiki, tmp_path):
    client, session = production_wiki
    source = production_config.source / "1-foundation/child.md"
    source.write_text("# Child\n")
    child = Reference(production_config.wiki, ("Main", "child"))
    session.pages[child] = RemotePage("Existing", "xwiki/2.1", "Manual")
    publisher = Publisher(compile_tree(production_config), client, tmp_path)
    with pytest.raises(PublishError, match="collision"):
        publisher.preflight()
    assert not writes(session)
    mapping = PageMapping(Path("1-foundation/child.md"), child, None, True)
    config = replace(production_config, pages=(mapping,))
    publisher = publish(config, client, tmp_path)
    assert len(list((publisher.output / "backups").glob("*.xml"))) == 4


def test_prune_off_reports_then_opt_in_deletes_owned_children(production_config, production_wiki, tmp_path):
    client, session = production_wiki
    parent = production_config.source / "1-foundation/group/index.md"
    parent.parent.mkdir()
    parent.write_text("# Group\n")
    leaf = parent.parent / "leaf.md"
    leaf.write_text("# Leaf\n")
    publish(production_config, client, tmp_path)
    leaf.unlink()
    parent.unlink()
    publisher = Publisher(compile_tree(production_config), client, tmp_path / "output")
    plan = publisher.preflight()
    assert len(plan.pending_removals) == 2
    assert not plan.operations
    publisher.apply(plan)
    group_ref = Reference(production_config.wiki, ("Main", "group"))
    leaf_ref = Reference(production_config.wiki, ("Main", "group", "leaf"))
    assert group_ref in session.pages and leaf_ref in session.pages
    publisher.apply(publisher.preflight(prune=True))
    assert group_ref not in session.pages and leaf_ref not in session.pages
    deletes = [url for method, url, kwargs in session.calls if method == "DELETE"]
    assert "/spaces/leaf/" in deletes[0]
    assert all(root.reference in session.pages for root in production_config.roots)
    assert all("skipRecycleBin" not in url for url in deletes)


@pytest.mark.parametrize("blocker", ["modified", "descendant", "attachment"])
def test_prune_never_deletes_unmanaged_or_modified_resources(
        production_config, production_wiki, tmp_path, blocker):
    client, session = production_wiki
    child = production_config.source / "1-foundation/child.md"
    child.write_text("# Child\n")
    publish(production_config, client, tmp_path)
    child.unlink()
    child_ref = Reference(production_config.wiki, ("Main", "child"))
    if blocker == "modified":
        session.pages[child_ref] = RemotePage("Human", "xwiki/2.1", "edited")
    elif blocker == "descendant":
        session.pages[Reference(child_ref.wiki, (*child_ref.spaces, "human"))] = RemotePage(
            "Human", "xwiki/2.1", "Unmanaged"
        )
    else:
        session.assets[(child_ref, "human.txt")] = b"manual"
    publisher = Publisher(compile_tree(production_config), client, tmp_path / "output")
    count = len(writes(session))
    with pytest.raises(PublishError):
        publisher.preflight(prune=True, overwrite=True)
    assert len(writes(session)) == count


def test_removed_asset_remains_owned_until_pruned(temporary_config, wiki, tmp_path):
    client, session = wiki
    publisher = publish(temporary_config, client, tmp_path)
    root = temporary_config.roots[0].reference
    index = temporary_config.source / "index.md"
    index.write_text("---\npageName: test\n---\n# New\n")
    publisher = publish(temporary_config, client, tmp_path)
    state = json.loads(session.assets[(root, MANIFEST)])
    assert len(state["pages"][0]["attachments"]) == 2
    publisher.apply(publisher.preflight(prune=True))
    assert set(name for ref, name in session.assets) == {MANIFEST}


def test_header_only_page_retains_owned_attachments_even_with_prune(
        temporary_config, wiki, tmp_path):
    client, session = wiki
    publish(temporary_config, client, tmp_path)
    before_pages = dict(session.pages)
    before_assets = dict(session.assets)
    (temporary_config.source / "index.md").write_text("---\npageName: test\n---\n")
    publisher = Publisher(compile_tree(temporary_config), client, tmp_path / "output")
    count = len(writes(session))
    plan = publisher.preflight(prune=True)
    assert not plan.operations
    assert not plan.pending_removals
    publisher.apply(plan)
    assert session.pages == before_pages
    assert session.assets == before_assets
    assert len(writes(session)) == count


def test_compile_failure_prevents_authentication_or_any_network(
        temporary_config, wiki, monkeypatch, tmp_path):
    index = temporary_config.source / "index.md"
    index.write_text("[broken](missing.md)")
    monkeypatch.setattr("md2xwiki.cli.Client", lambda config: pytest.fail("Must not connect"))
    monkeypatch.setattr("sys.argv", ["md2xwiki", "pipeline", "--config",
                                    str(temporary_config.path), "--output", str(tmp_path)])
    assert main() == 1
    assert json.loads((tmp_path / "summary.json").read_bytes())["status"] == "failed"


@pytest.mark.parametrize("prune_args", [[], ["--prune"]])
def test_real_pipeline_command_uses_shared_client_and_verifies_idempotence(
        temporary_config, wiki, monkeypatch, tmp_path, prune_args):
    client, session = wiki
    monkeypatch.setattr("md2xwiki.cli.Client", lambda config: client)
    monkeypatch.setattr("sys.argv", ["md2xwiki", "pipeline", "--config",
                                    str(temporary_config.path), "--output", str(tmp_path), *prune_args])
    assert main() == 0
    assert json.loads((tmp_path / "summary.json").read_bytes())["status"] == "verified"
    assert json.loads((tmp_path / "build.json").read_bytes())["pages"][0]["source"] == "index.md"
