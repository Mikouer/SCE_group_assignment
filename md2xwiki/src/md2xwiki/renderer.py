import mimetypes
import re
from urllib.parse import unquote, urlsplit

from markdown_it.token import Token

from .config import MANIFEST, Config
from .errors import PublishError
from .model import Attachment, Build, Page, digest, ensure_xml_text
from .references import component
from .tree import discover, plain

# Escaping every punctuation character keeps Markdown text from becoming wiki syntax.
PUNCTUATION = set(r"""~\*_/{}[]()<>=|#%:;!^"'-+.@$?,&""")


def escape(text: str) -> str:
    return "".join("~" + c if c in PUNCTUATION else c for c in text)


def parameter(value: str) -> str:
    return value.replace("\\", "\\\\").replace('"', '\\"')


def link_parameter(value: str) -> str:
    return target(parameter(value))


def target(value: str) -> str:
    return value.replace("~", "~~").replace("]", "~]").replace("|", "~|")


class Renderer:
    def __init__(self, build: Build, page: Page):
        self.build = build
        self.page = page
        self.line = 1
        self.heading = 0

    def error(self, message: str) -> PublishError:
        return PublishError(f"{self.page.source}:{self.line}: {message}")

    def resolve(self, href: str, image: bool = False) -> str:
        parsed = urlsplit(href)
        if parsed.scheme:
            if parsed.scheme.lower() not in {"http", "https", "mailto"}:
                raise self.error(f"Unsupported or unsafe link scheme: {parsed.scheme}")
            if image and parsed.scheme.lower() == "mailto":
                raise self.error("mailto is not an image URL")
            if parsed.scheme.lower() in {"http", "https"} and not parsed.netloc:
                raise self.error(f"Invalid URL: {href}")
            return target(href)
        if parsed.netloc or parsed.path.startswith("/") or parsed.query:
            raise self.error(f"Use a relative source path or an explicit HTTPS URL: {href}")
        source = self.build.config.source.resolve()
        decoded_path = unquote(parsed.path)
        if any(ord(c) < 32 for c in decoded_path):
            raise self.error("Control characters are not valid in local link paths")
        path = source / self.page.source if not decoded_path else (
            source / self.page.source.parent / decoded_path
        )
        resolved = path.resolve()
        if not resolved.is_relative_to(source):
            raise self.error(f"Link escapes the source tree: {href}")
        # Reject symlinks even when they resolve back inside the source tree.
        cursor = path
        while cursor != source and cursor.is_relative_to(source):
            if cursor.is_symlink():
                raise self.error(f"Symlink link target: {href}")
            cursor = cursor.parent
        relative = resolved.relative_to(source)
        by_source = self.build.by_source
        page = by_source.get(relative) or by_source.get(relative / "index.md")
        if page:
            if image:
                raise self.error(f"Image links to a Markdown page: {href}")
            anchor = unquote(parsed.fragment)
            if anchor and anchor not in page.anchors:
                raise self.error(f"Unknown heading #{anchor} in {relative}")
            result = "doc:" + target(page.reference.document)
            if anchor:
                result += '||anchor="' + parameter(anchor) + '"'
            return result
        if parsed.fragment:
            raise self.error(f"Fragments are only supported on managed Markdown pages: {href}")
        if relative.suffix.lower() == ".md" or not resolved.is_file():
            raise self.error(f"Missing or unmanaged link target: {href}")
        name = digest(relative.as_posix().encode())[:16] + "-" + resolved.name
        if name == MANIFEST or resolved.name == MANIFEST:
            raise self.error("The ownership manifest name is reserved")
        existing = self.page.attachments.get(name)
        if existing and existing.source != relative:
            raise self.error(f"Attachment name collision: {href}")
        mime = mimetypes.guess_type(resolved.name)[0] or "application/octet-stream"
        self.page.attachments[name] = Attachment(name, relative, resolved.read_bytes(), mime)
        return "attach:" + target(self.page.reference.document + "@" + component(name))

    def inline(self, tokens: list[Token]) -> str:
        result = []
        i = 0
        styles = {"em": "//", "strong": "**", "s": "--"}
        while i < len(tokens):
            t = tokens[i]
            if t.type == "text":
                result.append(escape(t.content))
            elif t.type == "unsupported_math":
                raise self.error("Math extensions are unsupported; use ordinary text or code")
            elif t.type in {"softbreak", "hardbreak"}:
                result.append("\n" if t.type == "softbreak" else "\\\\\n")
            elif t.type == "code_inline":
                result.append("##" + escape(t.content.replace("\n", " ")) + "##")
            elif t.type.endswith(("_open", "_close")) and t.type.rsplit("_", 1)[0] in styles:
                result.append(styles[t.type.rsplit("_", 1)[0]])
            elif t.type == "link_open":
                j = i + 1
                while j < len(tokens) and tokens[j].type != "link_close":
                    j += 1
                if j == len(tokens):
                    raise self.error("Unclosed link")
                destination = self.resolve(t.attrGet("href") or "")
                label = self.inline(tokens[i + 1:j])
                link_title = t.attrGet("title")
                if link_title:
                    destination += (" " if "||" in destination else "||") + (
                        'title="' + link_parameter(link_title) + '"'
                    )
                result.append("[[" + label + ">>" + destination + "]]")
                i = j
            elif t.type == "image":
                destination = self.resolve(t.attrGet("src") or "", image=True)
                attributes = 'alt="' + link_parameter(plain(t.children or [])) + '"'
                if t.attrGet("title"):
                    attributes += ' title="' + link_parameter(t.attrGet("title") or "") + '"'
                if destination.startswith("attach:"):
                    destination = destination[len("attach:"):]
                result.append("[[image:" + destination + "||" + attributes + "]]")
            else:
                raise self.error(f"Unsupported inline syntax: {t.type}")
            i += 1
        return "".join(result)

    def code(self, token: Token) -> str:
        language = token.info.strip().split()[0] if token.info.strip() else ""
        if language.lower() in {"mermaid", "math", "latex", "tex"}:
            raise self.error(f"Unsupported fenced extension: {language}")
        if language and not re.fullmatch(r"[A-Za-z0-9_+-]+", language):
            raise self.error(f"Unsupported code language identifier: {language!r}")
        body = token.content.removesuffix("\n")
        # Macro-looking code uses verbatim, not a macro whose closing delimiter
        # could be supplied by the source. Split verbatim's own delimiter too.
        if "{{" in body:
            return ("\n\n##" + escape("}}}") + "##\n\n").join(
                "{{{\n" + chunk + "\n}}}" for chunk in body.split("}}}")
            )
        opening = "{{code" + (f' language="{language}"' if language else "") + "}}\n"
        return opening + body + "\n{{/code}}"

    def blocks(self, tokens: list[Token], start: int = 0, stop: str | None = None) -> tuple[str, int]:
        output: list[str] = []
        i = start
        while i < len(tokens):
            t = tokens[i]
            if t.type == stop:
                return "\n\n".join(output), i + 1
            if t.map:
                self.line = t.map[0] + 1 + self.page.source_line_offset
            if t.type in {"paragraph_open", "heading_open"}:
                text = self.inline(tokens[i + 1].children or [])
                if t.type == "heading_open":
                    level = "=" * int(t.tag[1])
                    anchor = self.page.heading_ids[self.heading]
                    self.heading += 1
                    text = '{{id name="' + parameter(anchor) + '" /}}\n' + (
                        f"{level} {text} {level}"
                    )
                output.append(text)
                i += 3
            elif t.type in {"fence", "code_block"}:
                output.append(self.code(t))
                i += 1
            elif t.type == "hr":
                output.append("----")
                i += 1
            elif t.type == "blockquote_open":
                body, i = self.blocks(tokens, i + 1, "blockquote_close")
                output.append(">(((\n" + body + "\n)))")
            elif t.type in {"bullet_list_open", "ordered_list_open"}:
                ordered = t.type == "ordered_list_open"
                opening_type = t.type
                close = "ordered_list_close" if ordered else "bullet_list_close"
                start_number = t.attrGet("start") or "1"
                marker = "1." if ordered else "*"
                entries = []
                i += 1
                while i < len(tokens) and tokens[i].type != close:
                    if tokens[i].type != "list_item_open":
                        raise self.error(f"Malformed {opening_type}")
                    body, i = self.blocks(tokens, i + 1, "list_item_close")
                    entries.append(marker + " (((\n" + body + "\n)))")
                if i >= len(tokens):
                    raise self.error("Unclosed list")
                i += 1
                prefix = f'(% start="{start_number}" %)\n' if ordered and start_number != "1" else ""
                output.append(prefix + "\n".join(entries))
            elif t.type == "table_open":
                rows = []
                i += 1
                cells = []
                while i < len(tokens) and tokens[i].type != "table_close":
                    cell = tokens[i]
                    if cell.type == "tr_open":
                        cells = []
                    elif cell.type in {"th_open", "td_open"}:
                        style = cell.attrGet("style")
                        prefix = "|=" if cell.type == "th_open" else "|"
                        if style:
                            prefix += f'(% style="{parameter(style)}" %)'
                        cells.append(prefix + "(((\n" + self.inline(tokens[i + 1].children or [])
                                     + "\n)))")
                        i += 2
                    elif cell.type == "tr_close":
                        rows.append("".join(cells))
                    elif cell.type not in {"thead_open", "thead_close", "tbody_open", "tbody_close"}:
                        raise self.error(f"Unsupported table syntax: {cell.type}")
                    i += 1
                if i >= len(tokens):
                    raise self.error("Unclosed table")
                i += 1
                output.append("\n".join(rows))
            else:
                raise self.error(f"Unsupported block syntax: {t.type} (HTML/macros are not supported)")
        if stop:
            raise self.error(f"Missing closing block {stop}")
        return "\n\n".join(output), i

    def render(self) -> str:
        if self.page.preserve_content:
            return ""
        if self.page.generated:
            children = [p for p in self.build.pages if p.reference.spaces[:-1]
                        == self.page.reference.spaces]
            return "= " + escape(self.page.title) + " =\n\n" + "\n".join(
                "* [[" + escape(p.title) + ">>doc:" + target(p.reference.document) + "]]"
                for p in children
            ) + "\n"
        return self.blocks(self.page.tokens)[0] + "\n"


def compile_tree(config: Config) -> Build:
    build = discover(config)
    for page in build.pages:
        page.content = Renderer(build, page).render()
        ensure_xml_text(page.title + page.content, str(page.source))
    return build
