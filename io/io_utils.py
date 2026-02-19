from __future__ import annotations
from pathlib import Path


def increment_file_path(path: str | Path) -> Path:
    if isinstance(path, str):
        path = Path(path)

    i = 1
    while path.exists():
        new_path = path.parent / f"{path.stem}_{i}{path.suffix}"
        if not new_path.exists():
            return new_path
        i += 1
    
    return path


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