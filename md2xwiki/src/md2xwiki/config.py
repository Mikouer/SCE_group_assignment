import re
import tomllib
from dataclasses import dataclass
from pathlib import Path
from urllib.parse import urlsplit

from .errors import PublishError
from .metadata import read_index, read_markdown
from .paths import relative_path
from .references import Reference, WikiLocation, valid_segment

MANIFEST = ".md2xwiki-manifest.json"
TEST_NAME = re.compile(r"md2xwiki-test-[0-9a-f]{32}\Z")
TEST_SPACES = ("test",)


def spaces(value: object) -> tuple[str, ...]:
    if not isinstance(value, list) or not value:
        raise PublishError("spaces must be a nonempty array of raw space segments")
    return tuple(valid_segment(v) for v in value)


@dataclass(frozen=True)
class Root:
    source: Path
    reference: Reference
    title: str | None


@dataclass(frozen=True)
class PageMapping:
    source: Path
    reference: Reference
    title: str | None
    adopt_existing: bool


@dataclass(frozen=True)
class Config:
    path: Path
    base_url: str
    wiki: str
    source: Path
    deployment_id: str
    mode: str
    roots: tuple[Root, ...]
    pages: tuple[PageMapping, ...]
    layout: str = "markdown"
    single_file: Path | None = None

    @property
    def temporary(self) -> bool:
        return self.mode == "temporary"

    def root_for(self, reference: Reference) -> Root:
        matches = [r for r in self.roots if reference.within(r.reference)]
        if len(matches) != 1 or reference.page != "WebHome":
            raise PublishError(f"Reference outside managed roots: {reference.document}")
        return matches[0]


def title(value: object) -> str | None:
    if value is not None and (not isinstance(value, str) or not value.strip()):
        raise PublishError("title must be a nonempty string")
    return value


def load_config(path: Path) -> Config:
    path = path.resolve()
    try:
        data = tomllib.loads(path.read_text(encoding="utf-8"))
        settings = data["xwiki"]
        layout = settings.get("layout", "markdown")
        location = WikiLocation.parse(settings["project_root"], project=True) if (
            layout == "yaml"
        ) else WikiLocation.parse(settings["destination"]) if layout == "file" else None
        base_url = location.base_url if location else settings["base_url"].rstrip("/")
        wiki = location.wiki if location else valid_segment(settings["wiki"])
        source = path.parent / relative_path(settings["source"])
        deployment_id = valid_segment(settings["deployment_id"])
        mode = settings.get("mode", "production")
        if settings.get("syntax", "xwiki/2.1") != "xwiki/2.1":
            raise PublishError("Only xwiki/2.1 is supported")
        parsed = urlsplit(base_url)
        if (parsed.scheme != "https" or not parsed.hostname or parsed.username
                or parsed.password or parsed.query or parsed.fragment):
            raise PublishError("base_url must be HTTPS without credentials, query or fragment")
        if layout == "yaml":
            roots_list = []
            for r in data["roots"]:
                root_source = relative_path(r["source"])
                page_file, _ = read_index(source / root_source, source)
                metadata = read_markdown(page_file)
                roots_list.append(Root(root_source, Reference(
                    wiki, (*location.spaces, metadata.name)
                ), metadata.name))
            roots = tuple(roots_list)
        elif layout == "file":
            roots = (Root(Path("."), location.reference, None),)
        elif layout == "markdown":
            roots = tuple(
                Root(relative_path(r["source"]), Reference(wiki, spaces(r["spaces"])),
                     title(r.get("title")))
                for r in data["roots"]
            )
        else:
            raise PublishError("layout must be yaml, file or legacy markdown")
        single_file = relative_path(settings["file"]) if layout == "file" else None
        mappings = []
        for page in data.get("pages", []):
            adopt = page.get("adopt_existing", False)
            if not isinstance(adopt, bool):
                raise PublishError("adopt_existing must be a boolean")
            mappings.append(PageMapping(
                relative_path(page["source"]), Reference(wiki, spaces(page["spaces"])),
                title(page.get("title")), adopt,
            ))
    except (OSError, tomllib.TOMLDecodeError, KeyError, TypeError, AttributeError) as exc:
        raise PublishError(f"Invalid configuration {path}: {exc}") from exc
    if not roots:
        raise PublishError("At least one root is required")
    if mode == "temporary":
        legacy = len(roots) == 1 and roots[0].reference.spaces == ("Main", deployment_id)
        if (wiki != "sce2026group05" or len(roots) != 1 or mappings
                or not TEST_NAME.fullmatch(deployment_id)
                or (roots[0].reference.spaces != TEST_SPACES and not legacy)):
            raise PublishError("Temporary mode targets only test (or an older UUID run) with no mappings")
    elif mode != "production":
        raise PublishError("mode must be production or temporary")
    if layout != "markdown" and mappings:
        raise PublishError("YAML and single-file layouts take destinations from metadata/URLs, not [[pages]]")
    if len({r.source for r in roots}) != len(roots):
        raise PublishError("Duplicate source roots")
    for i, root in enumerate(roots):
        for other in roots[i + 1:]:
            if (root.source.is_relative_to(other.source)
                    or other.source.is_relative_to(root.source)
                    or root.reference.within(other.reference)
                    or other.reference.within(root.reference)):
                raise PublishError("Source and destination roots must not overlap")
    config = Config(path, base_url, wiki, source, deployment_id, mode, roots, tuple(mappings),
                    layout, single_file)
    if len({m.source for m in config.pages}) != len(config.pages):
        raise PublishError("Duplicate page mappings")
    for mapping in config.pages:
        root = config.root_for(mapping.reference)
        if not mapping.source.is_relative_to(root.source):
            raise PublishError(f"Mapping crosses its configured root: {mapping.source}")
    return config
