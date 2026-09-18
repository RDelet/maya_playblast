from __future__ import annotations

import json
from pathlib import Path

from . import io_utils


DOC_NAME = "maya_playblast.json"
DEFAULT_COLOR = "#e0a020"


def notes_path(video: Path) -> Path:
    return Path(video).with_suffix(".json")


class Annotation:

    def __init__(
            self,
            ann_id: int,
            clip: str,
            start: int,
            duration: int,
            strokes: list | None = None,
            color: str = DEFAULT_COLOR):
        self.id = int(ann_id)
        self.clip = str(clip)
        self.start = max(0, int(start))
        self.duration = max(1, int(duration))
        self.strokes = list(strokes or [])
        self.color = str(color or DEFAULT_COLOR)

    def covers(self, frame: int) -> bool:
        return self.start <= frame < self.start + self.duration

    def to_notes(self) -> dict:
        return {
            "start": self.start,
            "duration": self.duration,
            "color": self.color,
            "strokes": self.strokes
        }


class SequenceDoc:

    def __init__(self):
        self.clips: list[str] = []
        self.annotations: list[Annotation] = []
        self._next_id = 1
        self._path: Path | None = None
        self._legacy: list[dict] = []

    def load(self, path: Path) -> bool:
        self._path = path
        self._legacy = []
        if not path or not path.exists():
            return False
        try:
            data = json.loads(path.read_text(encoding="utf-8"))
        except (OSError, ValueError, TypeError):
            return False
        if not isinstance(data, dict):
            return False
        clips = data.get("clips") or []
        self.clips = []
        for item in clips:
            if isinstance(item, dict) and item.get("path"):
                self.clips.append(str(item["path"]))
            elif isinstance(item, str):
                self.clips.append(item)
        for item in data.get("annotations") or []:
            if isinstance(item, dict) and item.get("clip"):
                self._legacy.append(item)
        self.annotations = []
        self._next_id = 1
        return True

    def save(self, path: Path | None = None):
        path = path or self._path
        if not path:
            return
        self._path = path
        path.parent.mkdir(parents=True, exist_ok=True)
        payload = {
            "clips": [{"path": clip} for clip in self.clips]
        }
        path.write_text(json.dumps(payload, indent=2), encoding="utf-8")

    def set_path(self, path: Path | None):
        self._path = path

    def bind_playlist(self, clips: list[tuple[str, Path]]):
        migrated = self.migrate_legacy(clips)
        self.annotations = []
        self._next_id = 1
        for name, path in clips:
            self._read_sidecar(name, path)
        if migrated:
            self.save()

    def save_notes(self, clip_key: str, video: Path):
        anns = [ann for ann in self.annotations if io_utils.same_clip(ann.clip, clip_key)]
        path = notes_path(video)
        if not anns:
            if path.exists():
                try:
                    path.unlink()
                except OSError:
                    pass
            return
        payload = {"annotations": [ann.to_notes() for ann in anns]}
        path.write_text(json.dumps(payload, indent=2), encoding="utf-8")

    def migrate_legacy(self, clips: list[tuple[str, Path]]) -> bool:
        if not self._legacy:
            return False
        grouped: dict[Path, list[dict]] = {}
        for item in self._legacy:
            clip = str(item.get("clip") or "")
            video = self._video_for(clip, clips)
            if video is None:
                continue
            grouped.setdefault(video, []).append(item)
        for video, items in grouped.items():
            path = notes_path(video)
            if path.exists():
                continue
            payload = {
                "annotations": [
                    {
                        "start": item.get("start") or 0,
                        "duration": item.get("duration") or 1,
                        "color": item.get("color") or DEFAULT_COLOR,
                        "strokes": item.get("strokes") or []
                    }
                    for item in items
                ]
            }
            try:
                path.write_text(json.dumps(payload, indent=2), encoding="utf-8")
            except OSError:
                pass
        self._legacy = []
        return True

    def covering(self, clip: str, frame: int) -> Annotation | None:
        found = None
        for ann in self.annotations:
            if not io_utils.same_clip(ann.clip, clip):
                continue
            if ann.covers(frame):
                found = ann
        return found

    def strokes_at(self, clip: str, frame: int) -> list:
        ann = self.covering(clip, frame)
        if ann is None:
            return []
        return list(ann.strokes)

    def add_stroke(self, clip: str, frame: int, stroke: dict) -> Annotation:
        ann = self.covering(clip, frame)
        if ann is None:
            ann = Annotation(
                self._next_id,
                clip,
                frame,
                1,
                [],
                stroke.get("color") or DEFAULT_COLOR)
            self._next_id += 1
            self.annotations.append(ann)
        ann.strokes.append(stroke)
        return ann

    def clear_at(self, clip: str, frame: int) -> Annotation | None:
        ann = self.covering(clip, frame)
        if ann is None:
            return None
        self.annotations = [item for item in self.annotations if item.id != ann.id]
        return ann

    def set_range(self, ann_id: int, start: int, duration: int, max_frames: int):
        ann = self._by_id(ann_id)
        if ann is None:
            return
        last = max(1, int(max_frames))
        duration = max(1, int(duration))
        start = max(0, int(start))
        if start + duration > last:
            start = max(0, last - duration)
            duration = min(duration, last)
        ann.start = start
        ann.duration = max(1, duration)

    def set_color(self, ann_id: int, color: str):
        ann = self._by_id(ann_id)
        if ann is None:
            return
        ann.color = str(color or DEFAULT_COLOR)
        for stroke in ann.strokes:
            stroke["color"] = ann.color

    def bars(self) -> list[tuple[int, str, int, int, str]]:
        return [(ann.id, ann.clip, ann.start, ann.duration, ann.color) for ann in self.annotations]

    def get(self, ann_id: int) -> Annotation | None:
        return self._by_id(ann_id)

    def _read_sidecar(self, clip: str, video: Path):
        path = notes_path(video)
        if not path.exists():
            return
        try:
            data = json.loads(path.read_text(encoding="utf-8"))
        except (OSError, ValueError, TypeError):
            return
        items = []
        if isinstance(data, dict):
            items = data.get("annotations") or []
        elif isinstance(data, list):
            items = data
        for item in items:
            if not isinstance(item, dict):
                continue
            ann = Annotation(
                self._next_id,
                clip,
                item.get("start") or 0,
                item.get("duration") or 1,
                item.get("strokes") or [],
                item.get("color") or DEFAULT_COLOR)
            self._next_id += 1
            self.annotations.append(ann)

    def _video_for(self, clip: str, clips: list[tuple[str, Path]]) -> Path | None:
        found = io_utils.find_clip(clip, clips)
        if found is None:
            return None
        return found[1]

    def _by_id(self, ann_id: int) -> Annotation | None:
        for ann in self.annotations:
            if ann.id == ann_id:
                return ann
        return None
