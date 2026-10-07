from dataclasses import replace
from pathlib import Path

import pytest

from md2xwiki.config import PageMapping, load_config
from md2xwiki.errors import PublishError
from md2xwiki.references import Reference
from md2xwiki.renderer import compile_tree, escape


def source(config, content, relative="index.md"):
    path = config.source / relative
    path.parent.mkdir(parents=True, exist_ok=True)
    header = "---\npageName: test\n---\n" if config.layout == "file" else ""
    path.write_text(header + content, encoding="utf-8")
    return path


def test_smoke_exact_shapes(temporary_config):
    build = compile_tree(temporary_config)
    assert len(build.pages) == 1
    page = build.pages[0]
    assert '{{id name="duplicate-1" /}}' in page.content
    assert '||anchor="duplicate-1"]]' in page.content
    assert "**Bold**" in page.content
    assert "//italic//" in page.content
    assert "--struck through--" in page.content
    assert '|=(((\nFeature\n)))|=(((\nExpected result\n)))' in page.content
    assert "* (((\nNested item\n)))" in page.content
    assert "{{code language=\"python\"}}\nprint(" in page.content
    assert "{{velocity}}" not in page.content
    assert "~{~{velocity~}~}" in page.content
    assert "café" in page.content
    assert len(page.attachments) == 2
    assert "[[image:sce2026group05:test.WebHome@" in page.content
    assert "pageName" not in page.content
    assert 'alt="Test graphic" title="Uploaded image"' in page.content
    assert all(len(name.split("-")[0]) == 16 for name in page.attachments)


def test_dots_spaces_unicode_reference_encoding():
    ref = Reference("sce2026group05", ("2. Specification", "a2. Personas", "café"))
    assert ref.document == r"sce2026group05:2\. Specification.a2\. Personas.café.WebHome"
    assert ref.endpoint.endswith("/spaces/2.%20Specification/spaces/a2.%20Personas/spaces/caf%C3%A9/pages/WebHome")
    assert ref.view_url("https://wiki.example/xwiki").startswith(
        "https://wiki.example/xwiki/wiki/sce2026group05/view/2.%20Specification/"
    )


def test_cross_tree_links_and_mapping(production_config):
    source(production_config, "# Foundation\n[Personas](../2-specification/personas/index.md#primary-user)\n",
           "1-foundation/index.md")
    source(production_config, "# Personas\n## Primary user\n", "2-specification/personas/index.md")
    mapping = PageMapping(Path("2-specification/personas/index.md"), Reference(
        production_config.wiki, ("2. Specification", "a2. Personas")
    ), "a2. Personas and Profiles", True)
    build = compile_tree(replace(production_config, pages=(mapping,)))
    assert r'[[Personas>>doc:sce2026group05:2\. Specification.a2\. Personas.WebHome||anchor="primary-user"]]' in (
        build.by_source[Path("1-foundation/index.md")].content
    )


def test_duplicate_heading_suffix_collision(temporary_config):
    source(temporary_config, "# A\n## A\n## A-1\n## A\n## café\n[unicode](#caf%C3%A9)\n")
    page = compile_tree(temporary_config).pages[0]
    assert page.heading_ids == ["a", "a-1", "a-1-1", "a-2", "café"]


@pytest.mark.parametrize("tag", ["<br>", "<br/>", "<br />", "<BR>", "<Br />"])
def test_html_line_breaks_use_native_xwiki_breaks(temporary_config, tag):
    source(temporary_config,
           f"First{tag}Second\n\n"
           f"| Field | Meaning |\n| --- | --- |\n"
           f"| Criteria | Served{tag}{tag}Violated |\n")
    content = compile_tree(temporary_config).pages[0].content
    assert "First\\\\\nSecond" in content
    assert "|(((\nServed\\\\\n\\\\\nViolated\n)))" in content
    assert "<br" not in content.lower()


@pytest.mark.parametrize("content,expected", [
    ("<br>\nFollowing text\n", "\\\\\n\nFollowing text\n"),
    ("<br/>Following text\n", "\\\\\nFollowing text\n"),
    ("<br>\n<br />\nFollowing text\n", "\\\\\n\n\\\\\n\nFollowing text\n"),
    ("> <br>\n> Following text\n", ">(((\n\\\\\n\nFollowing text\n)))"),
    ("- <br>Following text\n", "* (((\n\\\\\nFollowing text\n)))"),
])
def test_leading_line_breaks_do_not_consume_following_markdown(
        temporary_config, content, expected):
    source(temporary_config, content)
    assert expected in compile_tree(temporary_config).pages[0].content


def test_heading_line_breaks_use_spaces_in_anchor_names(temporary_config):
    source(temporary_config, "# First<br>Second\n[heading](#first-second)\n")
    page = compile_tree(temporary_config).pages[0]
    assert page.heading_ids == ["first-second"]
    assert "= First\\\\\nSecond =" in page.content
    assert '||anchor="first-second"]]' in page.content


def test_line_break_tags_in_code_and_escaped_text_remain_literal(temporary_config):
    source(temporary_config, "`<br>` and \\<br>\n\n```text\n<br><br />\n```\n")
    content = compile_tree(temporary_config).pages[0].content
    assert "##~<br~>## and ~<br~>" in content
    assert '{{code language="text"}}\n<br><br />\n{{/code}}' in content
    assert "\\\\\n" not in content


@pytest.mark.parametrize("content", [
    'First<br class="gap">Second', 'First<br onclick="alert(1)">Second',
    'First<br style="display:none">Second', 'First</br>Second',
    '<br class="gap">\nFollowing text', "<br><script>alert(1)</script>",
    "<br>\n<div>Still unsupported</div>", "First<span>Second</span>",
    "<!-- Still unsupported -->",
])
def test_line_break_support_does_not_allow_other_html(temporary_config, content):
    source(temporary_config, content)
    with pytest.raises(PublishError, match=r"index.md:.*Unsupported"):
        compile_tree(temporary_config)


@pytest.mark.parametrize("content", [
    "[bad](missing.md)", "[bad](#missing)", "[bad](../../../outside.txt)",
    "[bad](/absolute.md)", "[bad](index.md?query=x)",
    "![bad](index.md)", "<div>html</div>", "```mermaid\nA-->B\n```",
    "```math\nx\n```", "Inline $x^2$ math",
    "$$\nx^2\n$$", r"Math \(x^2\)", "[bad](javascript:alert(1))",
    "[bad](ftp://example.org/file)", "![bad](data:image/png;base64,AAAA)",
])
def test_unsupported_and_invalid_fail_before_writes(temporary_config, content):
    source(temporary_config, content)
    with pytest.raises(PublishError, match=r"index.md:"):
        compile_tree(temporary_config)


def test_literal_currency_inline_code_and_fence_are_allowed(temporary_config):
    source(temporary_config, "# Prices\n$5 or $10; `$$ math $$`.\n\n```text\n$x$\n{{/code}}\n{{velocity}}literal{{/velocity}}\n```\n")
    page = compile_tree(temporary_config).pages[0]
    assert "~$5 or ~$10" in page.content
    assert "{{{\n" in page.content
    assert "{{/code}}" in page.content
    assert '{{code language="text"}}' not in page.content


def test_generated_navigation_and_collision(production_config):
    source(production_config, "# Deep\n", "1-foundation/group/deep.md")
    build = compile_tree(production_config)
    navigation = build.by_source[Path("1-foundation/group/index.md")]
    assert navigation.generated
    assert "[[Deep>>doc:sce2026group05:Main.group.deep.WebHome]]" in navigation.content
    source(production_config, "# Group\n", "1-foundation/group.md")
    with pytest.raises(PublishError, match="Ambiguous"):
        compile_tree(production_config)


def test_percent_encoded_directory_link(production_config):
    source(production_config, "# A\n[space](a%20b/)\n", "1-foundation/index.md")
    source(production_config, "# Space\n", "1-foundation/a b/index.md")
    assert "Main.a b.WebHome" in compile_tree(production_config).by_source[
        Path("1-foundation/index.md")
    ].content


def test_assets_do_not_become_pages(temporary_config):
    source(temporary_config, "Not a page", "assets/not-a-page.md")
    assert len(compile_tree(temporary_config).pages) == 1


def test_symlink_asset_and_page_rejected(temporary_config, tmp_path):
    outside = tmp_path / "outside.txt"
    outside.write_text("outside")
    (temporary_config.source / "assets/link.txt").symlink_to(outside)
    source(temporary_config, "# Test\n[asset](assets/link.txt)\n")
    with pytest.raises(PublishError, match="Symlink|symlink|escapes"):
        compile_tree(temporary_config)


def test_missing_root_aborts_whole_compilation(production_config):
    (production_config.source / "3-evaluation/index.md").unlink()
    with pytest.raises(PublishError, match="requires index.md"):
        compile_tree(production_config)


def test_temporary_test_cannot_point_elsewhere(temporary_config):
    text = temporary_config.path.read_text().replace("/view/test/", "/view/0.%20Introduction/")
    temporary_config.path.write_text(text)
    with pytest.raises(PublishError, match="Temporary mode"):
        load_config(temporary_config.path)


def test_attachment_basename_collisions_get_distinct_names(temporary_config):
    source(temporary_config, "# A\n[a](assets/one/x.txt) [b](assets/two/x.txt)\n")
    source(temporary_config, "one", "assets/one/x.txt")
    source(temporary_config, "two", "assets/two/x.txt")
    assets = compile_tree(temporary_config).pages[0].attachments
    assert len(assets) == 2
    assert all(name.endswith("-x.txt") for name in assets)


def test_non_one_ordered_list_start_preserved(temporary_config):
    source(temporary_config, "# List\n3. Third\n4. Fourth\n")
    assert '(% start="3" %)\n1. (((\nThird\n)))\n1. (((\nFourth\n)))' in (
        compile_tree(temporary_config).pages[0].content
    )

def test_escaped_math_delimiters_remain_literal(temporary_config):
    source(temporary_config, r"# Literal" + "\n" + r"\$x\$ and \$\$\$" + "\n")
    assert "~$x~$" in compile_tree(temporary_config).pages[0].content


def test_symlink_source_directory_rejected(temporary_config):
    original = temporary_config.source
    link = original.parent / "link"
    link.symlink_to(original, target_is_directory=True)
    with pytest.raises(PublishError, match="Symlink source"):
        compile_tree(replace(temporary_config, source=link))


@pytest.mark.parametrize("content", ["# Invalid\nNUL \x00\n", "# Invalid\n[bad](assets/%00.txt)"])
def test_control_characters_fail_before_any_publish(temporary_config, content):
    source(temporary_config, content)
    with pytest.raises(PublishError, match="XML 1.0|Control characters"):
        compile_tree(temporary_config)
