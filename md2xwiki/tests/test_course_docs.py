import json
import re
from pathlib import Path
from urllib.parse import unquote, urlsplit

import pytest

from md2xwiki.config import load_config
from md2xwiki.metadata import read_markdown
from md2xwiki.renderer import compile_tree

REPO = Path(__file__).resolve().parents[2]
CODE = re.compile(
    r"(?<![\w-])(?:UC\d{2}-F\d+-(?:PR|CL)\d+|"
    r"(?:SA|ST|PS|HV|VT|HFC|M|EM|TECH|DS|HP|RP|OS|OBJ|TDP|IDP|AT|ER)-\d{2}|"
    r"UC\d{2}|F\d+)(?![\w-])"
)
PROTECTED = re.compile(r"\[[^\]]*\]\([^)]+\)|`[^`]*`")


@pytest.fixture(scope="module")
def course():
    return compile_tree(load_config(REPO / "xwiki.toml"))


def test_all_existing_wiki_destinations_are_preserved(course):
    snapshot = json.loads((Path(__file__).parent / "fixtures/course-wiki-paths.json").read_text())
    existing = {tuple(spaces) for spaces in snapshot["spaces"]}
    destinations = {page.reference.spaces for page in course.pages}
    assert existing <= destinations
    assert course.config.wiki == snapshot["wiki"]
    assert {root.reference.spaces for root in course.config.roots} == {
        ("Main",), ("2. Specification",), ("3. Evaluation",)
    }


def test_each_entity_has_its_own_page_and_definition(course):
    expected = {
        *(f"SA-{n:02}" for n in range(1, 4)),
        *(f"ST-{n:02}" for n in range(1, 5)),
        *(f"HV-{n:02}" for n in range(1, 5)),
        *(f"M-{n:02}" for n in range(1, 4)),
        *(f"HFC-{n:02}" for n in range(1, 3)),
        *(f"EM-{n:02}" for n in range(1, 3)),
        *(f"TECH-{n:02}" for n in range(1, 3)),
        *(f"OBJ-{n:02}" for n in range(1, 3)),
        "PS-01", "VT-01", "DS-01", "HP-01", "RP-01", "OS-01",
        "TDP-01", "IDP-01", "UC01", "F1", "F2", "F3", "AT-01", "ER-01",
        "UC01-F1-PR1", "UC01-F2-PR2", "UC01-F3-PR3",
        "UC01-F1-CL1", "UC01-F2-CL2", "UC01-F2-CL3", "UC01-F3-CL4",
    }
    entities = [page for page in course.pages if CODE.fullmatch(page.source.stem)]
    assert {page.source.stem for page in entities} == expected
    assert len(entities) == len(expected)
    for page in entities:
        body = read_markdown(course.config.source / page.source).body
        assert f"| ID | {page.source.stem}" in body
        assert not page.preserve_content


def test_entity_mentions_are_relative_links_not_dangling_codes(course):
    for page in course.pages:
        body = read_markdown(course.config.source / page.source).body
        for line in body.splitlines():
            if line.startswith("#") or line.startswith("| ID |"):
                continue
            assert not CODE.search(PROTECTED.sub("", line)), (page.source, line)


def test_identifier_links_resolve_to_the_correct_case_and_wiki_document(course):
    entities = {page.source.stem: page for page in course.pages if CODE.fullmatch(page.source.stem)}
    checked = set()
    for page in course.pages:
        for token in page.tokens:
            children = token.children or []
            for i, child in enumerate(children):
                if child.type != "link_open" or i + 1 >= len(children):
                    continue
                label = children[i + 1].content
                if label not in entities:
                    continue
                href = child.attrGet("href")
                parsed = urlsplit(href)
                assert not parsed.scheme and not parsed.netloc
                target = (course.config.source / page.source.parent / unquote(parsed.path)).resolve()
                expected = entities[label]
                assert target == (course.config.source / expected.source).resolve()
                assert ">>doc:" + expected.reference.document in page.content
                checked.add(label)
    assert {"ST-04", "HV-01", "HV-02", "HFC-02", "UC01-F2-CL3", "AT-01"} <= checked


def test_no_example_or_removed_stakeholder_content_is_imported(course):
    for page in course.pages:
        body = read_markdown(course.config.source / page.source).body
        assert not re.search(r"\b(?:Anke|Marieke|Leon|Mari|Maria|ST-05)\b", body)
    hanz = next(page for page in course.pages if page.source.stem == "ST-04")
    assert hanz.reference.spaces == ("Main", "sdf", "Stakeholders", "ST-04: Hanz")
    assert "Hanz" in hanz.content


def test_existing_overviews_remain_header_only_and_graph_is_deferred(course):
    for page in course.pages:
        if page.source.name in {
            "Foundation.md", "Specification.md", "Evaluation.md", "OperationalDemands.md",
            "SituatedActivities.md", "Stakeholders.md", "ProblemScenarios.md", "HumanFactors.md",
            "HumanValues.md", "ValueTensions.md", "HumanFactorConcepts.md", "Measures.md",
            "EvaluationMethods.md", "Technology.md", "DesignScenarios.md", "Personas.md",
            "HumanPersonas.md", "RobotProfiles.md", "UseCases.md", "TeamDesignPatterns.md",
            "InteractionDesignPatterns.md", "ObjectiveStories.md", "Artifacts.md",
            "EvaluationReports.md", "Evidence.md",
        }:
            assert page.preserve_content
            assert page.content == ""
        assert not any("traceability" in space.lower() for space in page.reference.spaces)


def test_evaluation_gaps_are_explicit_and_source_diagram_is_attached(course):
    report = next(page for page in course.pages if page.source.stem == "ER-01")
    assert "Not Started" in read_markdown(course.config.source / report.source).body
    summary = next(page for page in course.pages
                   if page.source.name == "VerificationAndValidationSummary.md")
    assert read_markdown(course.config.source / summary.source).body.count("Not assessed") == 7
    assert not any(re.fullmatch(r"EV-\d{2}", page.source.stem) for page in course.pages)
    pattern = next(page for page in course.pages if page.source.stem == "TDP-01")
    assert len(pattern.attachments) == 1
    assert next(iter(pattern.attachments.values())).mime == "image/png"
