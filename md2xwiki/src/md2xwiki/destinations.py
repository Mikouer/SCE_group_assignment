from pathlib import Path

from .config import Config, Root
from .metadata import read_index, read_markdown
from .model import digest
from .references import Reference, WikiLocation


def tree_config(folder: Path, project_root: str, deployment_id: str | None = None) -> Config:
    folder = folder.resolve()
    location = WikiLocation.parse(project_root, project=True)
    page, _ = read_index(folder, folder)
    metadata = read_markdown(page)
    reference = Reference(location.wiki, (*location.spaces, metadata.name))
    return Config(
        folder / ".md2xwiki-cli.toml", location.base_url, location.wiki, folder,
        deployment_id or "md2xwiki-tree-" + digest(reference.document.encode())[:24],
        "production", (Root(Path("."), reference, metadata.name),), (), "yaml",
    )


def file_config(file: Path, destination: str, deployment_id: str | None = None) -> Config:
    file = file.resolve()
    location = WikiLocation.parse(destination)
    metadata = read_markdown(file)
    return Config(
        file.parent / ".md2xwiki-cli.toml", location.base_url, location.wiki, file.parent,
        deployment_id or "md2xwiki-file-" + digest(location.reference.document.encode())[:24],
        "production", (Root(Path("."), location.reference, metadata.name),), (), "file",
        Path(file.name),
    )
