from pathlib import Path

from .errors import PublishError


def relative_path(value: object) -> Path:
    if not isinstance(value, str) or not value:
        raise PublishError("Source paths must be nonempty relative paths")
    path = Path(value)
    if path.is_absolute() or ".." in path.parts or "\\" in value:
        raise PublishError(f"Source path must stay inside its source tree: {value!r}")
    return path


def inside(path: Path, boundary: Path) -> Path:
    boundary = boundary.resolve()
    if not path.resolve().is_relative_to(boundary):
        raise PublishError(f"Source path escapes its tree: {path}")
    cursor = path
    while cursor.is_relative_to(boundary) and cursor != boundary:
        if cursor.is_symlink():
            raise PublishError(f"Symlink source path: {cursor}")
        cursor = cursor.parent
    return path
