from __future__ import annotations

from pathlib import Path
import re
import shutil
import subprocess
import sys


_DEFAULT_PREFIX = "_v"
_DEFAULT_PADDING = 3


class VersionFormat:

    def __init__(self, prefix: str = _DEFAULT_PREFIX, padding: int = _DEFAULT_PADDING, suffix: str = ""):
        self.prefix = prefix or ""
        try:
            digits = int(padding)
        except (TypeError, ValueError):
            digits = _DEFAULT_PADDING
        self.padding = min(6, max(1, digits))
        self.suffix = suffix or ""

    def apply(self, stem: str, index: int) -> str:
        return f"{stem}{self.prefix}{index:0{self.padding}d}{self.suffix}"

    def index_of(self, name_stem: str, base_stem: str) -> int | None:
        pattern = (
            "^" + re.escape(base_stem) + re.escape(self.prefix) + r"(\d+)" + re.escape(self.suffix) + "$"
        )
        match = re.match(pattern, name_stem)
        if not match:
            return None
        return int(match.group(1))


def check_directory(path: str | Path, build: bool = True) -> bool:
    if isinstance(path, str):
        path = Path(path)
    if path.suffix:
        path = path.parent

    if not path.exists():
        if build:
            path.mkdir(parents=True, exist_ok=True)
        else:
            return False

    return path.exists()


def search_exe(exe_name: str) -> Path | None:
    found = shutil.which(exe_name)
    if found:
        return Path(found)

    return None


def version_base_stem(path: Path, fmt: VersionFormat | None = None) -> str:
    fmt = fmt or VersionFormat()
    stem = path.stem
    if not fmt.prefix:
        return stem
    prefix_at = stem.rfind(fmt.prefix)
    if prefix_at <= 0:
        return stem
    base = stem[:prefix_at]
    if fmt.index_of(stem, base) is None:
        return stem
    return base


def list_versions(path: Path, fmt: VersionFormat | None = None) -> list[tuple[int, Path]]:
    fmt = fmt or VersionFormat()
    stem = version_base_stem(path, fmt)
    parent = path.parent
    found = []
    if not parent.exists():
        return found
    suffix = path.suffix.lower()
    for child in parent.iterdir():
        if not child.is_file() or child.suffix.lower() != suffix:
            continue
        index = fmt.index_of(child.stem, stem)
        if index is not None:
            found.append((index, child))
    found.sort(key=lambda item: item[0])
    return found


def next_versioned_path(path: Path, fmt: VersionFormat | None = None) -> Path:
    fmt = fmt or VersionFormat()
    stem = version_base_stem(path, fmt)
    versions = list_versions(path, fmt)
    next_index = versions[-1][0] + 1 if versions else 1
    return path.parent / f"{fmt.apply(stem, next_index)}{path.suffix}"


def latest_version(path: Path, fmt: VersionFormat | None = None) -> Path | None:
    fmt = fmt or VersionFormat()
    versions = list_versions(path, fmt)
    if versions:
        return versions[-1][1]
    if path.exists():
        return path
    return None


def no_window_flags() -> int:
    if sys.platform != "win32":
        return 0
    return getattr(subprocess, "CREATE_NO_WINDOW", 0x08000000)


def relative_label(path: Path, root: Path | None, fallback: str | None = None) -> str:
    if root:
        try:
            return path.resolve().relative_to(root.resolve()).as_posix()
        except ValueError:
            pass
    if fallback is not None:
        return fallback
    return path.name


def clip_key(value: str | Path) -> str:
    return str(value).replace("\\", "/").lstrip("./")


def same_clip(left: str | Path, right: str | Path) -> bool:
    return clip_key(left) == clip_key(right)


def match_clip(key: str, name: str, path: Path) -> bool:
    wanted = clip_key(key)
    label = clip_key(name)
    posix = path.as_posix()
    return wanted == label or posix.endswith("/" + wanted) or posix.endswith(wanted)


def find_clip(key: str, clips: list) -> tuple | None:
    for item in clips:
        if match_clip(key, item[0], item[1]):
            return item
    return None
