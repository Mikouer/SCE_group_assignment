import re
import unicodedata
from pathlib import Path

from markdown_it import MarkdownIt
from markdown_it.rules_block import StateBlock, html_block
from markdown_it.rules_inline import StateInline
from markdown_it.token import Token

from .config import Config
from .errors import PublishError
from .model import Build, Page, ensure_xml_text
from .metadata import read_markdown, read_tree, WikiTreeNode
from .paths import inside
from .references import Reference

LINE_BREAK = re.compile(r"<br[ \t\r\n]*/?>", re.IGNORECASE)


def parser() -> MarkdownIt:
    md = MarkdownIt("commonmark", {"html": True}).enable(["table", "strikethrough"])
    # Let the resolver reject bad schemes rather than CommonMark silently treating
    # a disallowed link as ordinary text.
    md.validateLink = lambda href: True

    def line_break(state: StateInline, silent: bool) -> bool:
        match = LINE_BREAK.match(state.src, state.pos)
        if match is None:
            return False
        if not silent:
            state.push("hardbreak", "br", 0)
        state.pos = match.end()
        return True

    def other_html_block(state: StateBlock, start: int, end: int, silent: bool) -> bool:
        # A leading <br> must reach the inline parser, not swallow a paragraph as HTML.
        if LINE_BREAK.match(state.src, state.bMarks[start] + state.tShift[start]):
            return False
        return html_block(state, start, end, silent)

    md.inline.ruler.before("html_inline", "line_break", line_break)
    md.block.ruler.at("html_block", other_html_block,
                      {"alt": ["paragraph", "reference", "blockquote"]})

    def unsupported_math(state: StateInline, silent: bool) -> bool:
        remaining = state.src[state.pos:]
        match = re.match(
            r"\$\$|\\\(.+?\\\)|\\\[.+?\\\]|(?<!\w)\$[^$`\n]+\$(?!\w)",
            remaining,
        )
        if not match:
            return False
        if not silent:
            state.push("unsupported_math", "", 0).content = match.group()
        state.pos += len(match.group())
        return True

    md.inline.ruler.before("escape", "unsupported_math", unsupported_math)
    return md


def plain(tokens: list[Token]) -> str:
    return "".join(
        t.content if t.type in {"text", "code_inline"} else
        plain(t.children or []) if t.type == "image" else
        " " if t.type in {"softbreak", "hardbreak"} else ""
        for t in tokens
    )


def slug(value: str) -> str:
    value = value.lower()
    value = "".join(c for c in value if c in "_-" or c.isspace()
                    or unicodedata.category(c)[0] in {"L", "N", "M"})
    return re.sub(r"\s", "-", value)


def assign_anchors(page: Page) -> None:
    counts: dict[str, int] = {}
    used: set[str] = set()
    for i, token in enumerate(page.tokens):
        if token.type == "heading_open":
            base = slug(plain(page.tokens[i + 1].children or []))
            n = counts.get(base, 0)
            anchor = base if n == 0 else f"{base}-{n}"
            while anchor in used:
                n += 1
                anchor = f"{base}-{n}"
            counts[base] = n + 1
            used.add(anchor)
            page.heading_ids.append(anchor)
    page.anchors = used


def discover(config: Config) -> Build:
    cursor = config.source
    while cursor != config.path.parent and cursor.is_relative_to(config.path.parent):
        if cursor.is_symlink():
            raise PublishError(f"Symlink source directory: {cursor}")
        cursor = cursor.parent
    source = config.source.resolve()
    if not source.is_dir():
        raise PublishError(f"Missing source tree: {config.source}")
    if config.layout != "markdown":
        return discover_explicit(config)
    mappings = {m.source: m for m in config.pages}
    pages: list[Page] = []
    seen_sources: set[Path] = set()
    seen_refs: set[Reference] = set()
    md = parser()
    for root in config.roots:
        root_path = source / root.source
        if not (root_path / "index.md").is_file():
            raise PublishError(f"Every root requires index.md: {root_path}")
        if not root_path.resolve().is_relative_to(source):
            raise PublishError(f"Source root escapes source tree: {root_path}")
        if root_path.is_symlink():
            raise PublishError(f"Symlink source root: {root_path}")
        files = []
        for item in root_path.rglob("*"):
            if item.is_symlink():
                raise PublishError(f"Symlinks are not supported in source trees: {item}")
            if item.is_file() and item.suffix.lower() == ".md":
                relative = item.relative_to(source)
                if "assets" not in item.relative_to(root_path).parts:
                    files.append(relative)
        directories = {root.source}
        for file in files:
            directory = file.parent
            while directory.is_relative_to(root.source):
                directories.add(directory)
                if directory == root.source:
                    break
                directory = directory.parent
        candidates = [(f, False) for f in sorted(files)]
        candidates += [(d / "index.md", True) for d in sorted(directories)
                       if d / "index.md" not in files]
        for file, generated in candidates:
            mapping = mappings.get(file)
            relative = file.relative_to(root.source)
            child_parts = relative.parent.parts if file.name == "index.md" else (
                *relative.parent.parts, file.stem
            )
            reference = mapping.reference if mapping else Reference(
                config.wiki, (*root.reference.spaces, *child_parts)
            )
            config.root_for(reference)
            if reference in seen_refs or file in seen_sources:
                raise PublishError(f"Ambiguous page mapping (topic.md vs topic/index.md): {file}")
            if reference == root.reference and file != root.source / "index.md":
                raise PublishError(f"Only the root index can map to its root: {file}")
            if file == root.source / "index.md" and reference != root.reference:
                raise PublishError(f"The root index must map to its configured root: {file}")
            seen_refs.add(reference)
            seen_sources.add(file)
            text = "" if generated else (source / file).read_text(encoding="utf-8")
            ensure_xml_text(text, str(file))
            offset = 0
            if text.startswith("---\n") and re.search(r"^pageName:", text, re.MULTILINE):
                metadata = read_markdown(source / file)
                text, offset = metadata.body, metadata.header_lines
            tokens = md.parse(text)
            first_h1 = next(
                (plain(tokens[i + 1].children or []) for i, t in enumerate(tokens)
                 if t.type == "heading_open" and t.tag == "h1"), None
            )
            override = mapping.title if mapping else (
                root.title if reference == root.reference else None
            )
            fallback = (file.parent.name if file.name == "index.md" else file.stem)
            page = Page(file, reference, override or first_h1 or fallback, tokens,
                        generated, bool(mapping and mapping.adopt_existing))
            page.source_line_offset = offset
            assign_anchors(page)
            pages.append(page)
    unknown = set(mappings) - seen_sources
    if unknown:
        raise PublishError(f"Mappings have no source page: {', '.join(map(str, sorted(unknown)))}")
    if config.temporary and len(pages) != 1:
        raise PublishError("The live test must compile exactly one Markdown page")
    return Build(config, sorted(pages, key=lambda p: (len(p.reference.spaces), p.reference.document)))


def discover_explicit(config: Config) -> Build:
    source = config.source.resolve()
    pages = []
    aliases = {}
    seen_files = set()
    seen_refs = set()
    md = parser()

    def add(path: Path, reference: Reference) -> Page:
        inside(path, source)
        file = path.resolve().relative_to(source)
        if file in seen_files or reference in seen_refs:
            raise PublishError(f"Duplicate source or destination page: {path}")
        seen_files.add(file)
        seen_refs.add(reference)
        metadata = read_markdown(path)
        if config.layout == "yaml" and metadata.name != reference.spaces[-1]:
            raise PublishError(f"{path}: pageName changed while compiling; rerun with stable sources")
        ensure_xml_text(metadata.body, str(file))
        tokens = md.parse(metadata.body)
        page = Page(file, reference, metadata.name, tokens, adopt_existing=True,
                    preserve_content=metadata.preserve_content, preserve_title=True,
                    source_line_offset=metadata.header_lines)
        assign_anchors(page)
        pages.append(page)
        return page

    def visit(node: WikiTreeNode, reference: Reference) -> None:
        page = add(node.page_text, reference)
        aliases[node.folder.relative_to(source)] = page
        for leaf in node.children_text:
            name = read_markdown(leaf).name
            add(leaf, Reference(config.wiki, (*reference.spaces, name)))
        for child in node.children:
            name = read_markdown(child.page_text).name
            visit(child, Reference(config.wiki, (*reference.spaces, name)))

    for root in config.roots:
        if config.layout == "file":
            if config.single_file is None:
                raise PublishError("Single-file publishing requires a source file")
            add(source / config.single_file, root.reference)
        else:
            node = read_tree(source / root.source, source)
            visit(node, root.reference)
    if config.temporary and len(pages) != 1:
        raise PublishError("The live test must compile exactly one Markdown page")
    return Build(config, sorted(pages, key=lambda p: (len(p.reference.spaces), p.reference.document)),
                 aliases)
