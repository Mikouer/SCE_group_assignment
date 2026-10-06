import hashlib
import json
import re
from dataclasses import dataclass, field
from pathlib import Path

from markdown_it.token import Token

from .config import Config
from .errors import PublishError
from .references import Reference


def digest(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def page_hash(title: str, syntax: str, content: str) -> str:
    return digest(json.dumps([title, syntax, content], ensure_ascii=False).encode())

def ensure_xml_text(value: str, location: str) -> None:
    match = re.search(r"[\x00-\x08\x0b\x0c\x0e-\x1f\ud800-\udfff\ufffe\uffff]", value)
    if match:
        line = value.count("\n", 0, match.start()) + 1
        raise PublishError(f"{location}:{line}: characters forbidden in XML 1.0")


@dataclass(frozen=True)
class Attachment:
    name: str
    source: Path
    data: bytes
    mime: str

    @property
    def hash(self) -> str:
        return digest(self.data)


@dataclass
class Page:
    source: Path
    reference: Reference
    title: str
    tokens: list[Token]
    generated: bool = False
    adopt_existing: bool = False
    anchors: set[str] = field(default_factory=set)
    heading_ids: list[str] = field(default_factory=list)
    attachments: dict[str, Attachment] = field(default_factory=dict)
    content: str = ""
    preserve_content: bool = False
    preserve_title: bool = False
    source_line_offset: int = 0
    syntax: str = "xwiki/2.1"

    @property
    def hash(self) -> str:
        return page_hash(self.title, self.syntax, self.content)


@dataclass
class Build:
    config: Config
    pages: list[Page]
    aliases: dict[Path, Page] = field(default_factory=dict)

    @property
    def by_source(self) -> dict[Path, Page]:
        return {p.source: p for p in self.pages} | self.aliases
