from dataclasses import dataclass
from urllib.parse import quote, unquote, urlsplit

from .errors import PublishError


def component(value: str) -> str:
    return "".join("\\" + c if c in "\\.:@^" else c for c in value)


def valid_segment(value: object) -> str:
    if not isinstance(value, str) or not value or value in {".", ".."}:
        raise PublishError("Reference segments must be nonempty strings, not '.' or '..'")
    if any(ord(c) < 32 or c in "/?#" for c in value):
        raise PublishError(f"Invalid reference segment: {value!r}")
    return value


@dataclass(frozen=True)
class Reference:
    wiki: str
    spaces: tuple[str, ...]
    page: str = "WebHome"

    def __post_init__(self) -> None:
        valid_segment(self.wiki)
        valid_segment(self.page)
        if not self.spaces:
            raise PublishError("A page must have at least one space")
        for space in self.spaces:
            valid_segment(space)

    @property
    def document(self) -> str:
        return component(self.wiki) + ":" + ".".join(
            component(s) for s in (*self.spaces, self.page)
        )

    @property
    def endpoint(self) -> str:
        return "/wikis/" + quote(self.wiki, safe="") + "".join(
            "/spaces/" + quote(s, safe="") for s in self.spaces
        ) + "/pages/" + quote(self.page, safe="")

    def attachment_endpoint(self, name: str) -> str:
        return self.endpoint + "/attachments/" + quote(valid_segment(name), safe="")

    def view_url(self, base_url: str) -> str:
        return base_url + "/wiki/" + quote(self.wiki, safe="") + "/view/" + "/".join(
            quote(s, safe="") for s in (*self.spaces, self.page)
        )

    def within(self, root: "Reference") -> bool:
        return self.wiki == root.wiki and self.spaces[:len(root.spaces)] == root.spaces


@dataclass(frozen=True)
class WikiLocation:
    base_url: str
    wiki: str
    spaces: tuple[str, ...]

    @classmethod
    def parse(cls, url: str, *, project: bool = False) -> "WikiLocation":
        parsed = urlsplit(url)
        if (parsed.scheme != "https" or not parsed.hostname or parsed.username
                or parsed.password or parsed.query or parsed.fragment):
            raise PublishError("Destination must be an HTTPS XWiki view URL without credentials or query")
        parts = parsed.path.rstrip("/").split("/")
        try:
            marker = parts.index("wiki")
        except ValueError as exc:
            raise PublishError("Destination must contain /wiki/WIKI/view") from exc
        if len(parts) < marker + 3 or parts[marker + 2] != "view":
            raise PublishError("Destination must contain /wiki/WIKI/view")
        wiki = valid_segment(unquote(parts[marker + 1]))
        segments = tuple(valid_segment(unquote(p)) for p in parts[marker + 3:])
        if segments and segments[-1] == "WebHome":
            segments = segments[:-1]
        if not project and not segments:
            raise PublishError("A file destination must include a page after /view/")
        base = parsed.scheme + "://" + parsed.netloc + "/".join(parts[:marker])
        return cls(base.rstrip("/"), wiki, segments)

    @property
    def reference(self) -> Reference:
        return Reference(self.wiki, self.spaces)
