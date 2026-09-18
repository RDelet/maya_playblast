from __future__ import annotations

import json
from pathlib import Path

from .constants import ROOT_PATH
from .settings import prefs_dir


def _presets_dir() -> Path:
    folder = prefs_dir() / f"{ROOT_PATH.name}_presets"
    folder.mkdir(parents=True, exist_ok=True)
    return folder


def _preset_file(name: str) -> Path:
    safe = "".join(ch if ch.isalnum() or ch in "-_ " else "_" for ch in name).strip()
    if not safe:
        raise ValueError("Preset name is empty")
    return _presets_dir() / f"{safe}.json"


def list_presets() -> list[str]:
    names = [path.stem for path in _presets_dir().glob("*.json")]
    names.sort(key=str.lower)
    return names


def save_preset(name: str, data: dict):
    path = _preset_file(name)
    path.write_text(json.dumps(data, indent=2), encoding="utf-8")


def load_preset(name: str) -> dict:
    path = _preset_file(name)
    if not path.exists():
        raise FileNotFoundError(f"Preset '{name}' was not found")
    return json.loads(path.read_text(encoding="utf-8"))
