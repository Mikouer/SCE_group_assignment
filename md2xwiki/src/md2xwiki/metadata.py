from dataclasses import dataclass
from pathlib import Path

import yaml

from .errors import PublishError
from .paths import inside, relative_path
from .references import valid_segment


class UniqueLoader(yaml.SafeLoader):
    pass


def unique_mapping(loader: UniqueLoader, node: yaml.MappingNode) -> dict:
    result = {}
    for key_node, value_node in node.value:
        key = loader.construct_object(key_node)
        if not isinstance(key, str) or key in result:
            raise PublishError("YAML keys must be unique strings")
        result[key] = loader.construct_object(value_node)
    return result


UniqueLoader.add_constructor(yaml.resolver.BaseResolver.DEFAULT_MAPPING_TAG, unique_mapping)


def mapping(text: str, location: Path) -> dict:
    try:
        value = yaml.load(text, Loader=UniqueLoader)
    except PublishError as exc:
        raise PublishError(f"{location}: {exc}") from exc
    except yaml.YAMLError as exc:
        raise PublishError(f"{location}: invalid YAML: {exc}") from exc
    if not isinstance(value, dict):
        raise PublishError(f"{location}: expected a YAML mapping")
    return value


@dataclass(frozen=True)
class MarkdownPage:
    name: str
    body: str
    header_lines: int

    @property
    def preserve_content(self) -> bool:
        return not self.body.strip()


def read_markdown(path: Path) -> MarkdownPage:
    text = path.read_text(encoding="utf-8-sig")
    lines = text.splitlines(keepends=True)
    if not lines or lines[0].strip() != "---":
        raise PublishError(f"{path}: every page needs YAML front matter with pageName")
    end = next((i for i in range(1, len(lines)) if lines[i].strip() == "---"), None)
    if end is None:
        raise PublishError(f"{path}: front matter has no closing ---")
    data = mapping("".join(lines[1:end]), path)
    name = valid_segment(data.get("pageName"))
    if name != name.strip():
        raise PublishError(f"{path}: pageName must not have leading/trailing whitespace")
    return MarkdownPage(name, "".join(lines[end + 1:]), end + 1)


@dataclass(frozen=True)
class WikiTreeNode:
    folder: Path
    page_text: Path
    children_text: tuple[Path, ...]
    children: tuple["WikiTreeNode", ...]


def read_index(folder: Path, boundary: Path) -> tuple[Path, tuple[Path, ...]]:
    index = inside(folder / "index.yaml", boundary)
    if not index.is_file():
        raise PublishError(f"Every tree node requires index.yaml: {folder}")
    data = mapping(index.read_text(encoding="utf-8-sig"), index)
    if set(data) - {"pageText", "children"}:
        raise PublishError(f"{index}: supported keys are pageText and children")
    if not data.get("pageText"):
        raise PublishError(f"{index}: pageText must point to a Markdown file; "
                           "use a header-only file to preserve existing content")
    page = inside(folder / relative_path(data["pageText"]), boundary)
    if not page.is_file() or page.suffix.lower() != ".md":
        raise PublishError(f"{index}: pageText must be an existing Markdown file")
    children = data.get("children", [])
    if not isinstance(children, list):
        raise PublishError(f"{index}: children must be a list of Markdown files or folders")
    paths = tuple(inside(folder / relative_path(child), boundary) for child in children)
    if len(set(p.resolve() for p in paths)) != len(paths):
        raise PublishError(f"{index}: duplicate children")
    return page, paths


def read_tree(folder: Path, boundary: Path) -> WikiTreeNode:
    seen_folders: set[Path] = set()
    seen_files: set[Path] = set()

    def visit(directory: Path) -> WikiTreeNode:
        resolved = directory.resolve()
        if resolved in seen_folders:
            raise PublishError(f"Repeated/cyclic tree folder: {directory}")
        seen_folders.add(resolved)
        page, paths = read_index(directory, boundary)
        if page.resolve() in seen_files:
            raise PublishError(f"A Markdown file cannot represent multiple pages: {page}")
        seen_files.add(page.resolve())
        leaves = []
        branches = []
        for path in paths:
            if path.is_dir():
                branches.append(visit(path))
            elif path.is_file() and path.suffix.lower() == ".md":
                if path.resolve() in seen_files:
                    raise PublishError(f"A Markdown file cannot represent multiple pages: {path}")
                seen_files.add(path.resolve())
                leaves.append(path)
            else:
                raise PublishError(f"Child must be an existing Markdown file or tree folder: {path}")
        return WikiTreeNode(directory, page, tuple(leaves), tuple(branches))

    return visit(folder)
