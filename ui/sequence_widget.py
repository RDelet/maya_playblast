from __future__ import annotations

import json
from pathlib import Path

try:
    from PySide2 import QtCore, QtWidgets
except ImportError:
    from PySide6 import QtCore, QtWidgets

from ..core.constants import VIDEO_SUFFIXES
from ..core.logger import log
from ..core.settings import Settings
from ..io import ffplay, io_utils
from .player_widget import PlayerWidget


class SequenceWidget(QtWidgets.QWidget):

    STYLE = """
        SequenceWidget QPushButton#placeholder {
            background: #1e1e1e;
            border: 1px dashed #555;
            border-radius: 3px;
            padding: 18px;
            color: #888;
        }
        SequenceWidget QPushButton#placeholder:hover {
            border-color: #e0a020;
            color: #e0a020;
        }
    """

    shotSelected = QtCore.Signal(str)
    playingChanged = QtCore.Signal(bool)

    def __init__(self, parent: QtWidgets.QWidget | None = None):
        super().__init__(parent)

        self._settings = Settings()
        self._root: Path | None = None
        self._stem = "playblast"
        self._suffix = ".mp4"
        self._clip_key = None

        layout = QtWidgets.QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(4)

        self._player_host = QtWidgets.QWidget(self)
        self._player_host.setMinimumHeight(200)
        host_layout = QtWidgets.QVBoxLayout(self._player_host)
        host_layout.setContentsMargins(0, 0, 0, 0)
        host_layout.setSpacing(0)
        layout.addWidget(self._player_host, 1)

        self._placeholder = QtWidgets.QPushButton("Player detached — click to attach", self._player_host)
        self._placeholder.setObjectName("placeholder")
        self._placeholder.clicked.connect(self._attach_player)
        self._placeholder.hide()
        host_layout.addWidget(self._placeholder)

        self._player = PlayerWidget(self._player_host)
        self._player.set_host(self._player_host)
        self._player.layoutChanged.connect(lambda: self.playingChanged.emit(True))
        self._player.detachedChanged.connect(self._on_detached)
        self._player.shotSelected.connect(self.shotSelected)
        self._player.orderChanged.connect(self._on_playlist_changed)
        host_layout.addWidget(self._player)

        self.setStyleSheet(self.STYLE)
        self.setSizePolicy(QtWidgets.QSizePolicy.Preferred, QtWidgets.QSizePolicy.Expanding)

    def set_root(self, folder: Path | None):
        self._root = folder
        self._player.set_label_root(folder)
        self.refresh()

    def set_clip_name(self, stem: str, extension: str):
        self._stem = stem
        self._suffix = "." + extension.lstrip(".")

    def ordered_names(self) -> list[str]:
        return self._player.ordered_names()

    def clip_paths(self) -> list[str]:
        paths = []
        for name, path, duration in self._player.playlist():
            paths.append(self._store_path(path))
        return paths

    def set_order(self, names: list[str]):
        clips = []
        for name in names:
            path = self._shot_video(str(name))
            if path:
                clips.append(path)
        self._settings.set("ui/sequence/clips", json.dumps([self._store_path(path) for path in clips]))
        self.refresh()

    def set_clip_paths(self, paths: list[str]):
        self._settings.set("ui/sequence/clips", json.dumps([str(path) for path in paths]))
        self.refresh()

    def refresh(self):
        stored = self._stored_clips()
        if stored is None:
            paths = []
            for name in self._shot_dirs():
                path = self._shot_video(name)
                if path:
                    paths.append(path)
        else:
            paths = [path for path in stored if path.exists()]
        self._load_paths(paths)

    def stop(self):
        self._clip_key = None
        self._player.stop()
        if self._player.is_detached():
            self._player.attach()

    def _shot_dirs(self) -> list[str]:
        if not self._root or not self._root.exists():
            return []
        names = [path.name for path in self._root.iterdir() if path.is_dir()]
        names.sort(key=str.lower)
        return names

    def _stored_clips(self) -> list[Path] | None:
        raw = self._settings.get("ui/sequence/clips")
        if raw is None:
            return None
        try:
            data = json.loads(str(raw))
        except (TypeError, ValueError):
            return None
        if not isinstance(data, list):
            return None
        paths = []
        for item in data:
            path = self._resolve_path(str(item))
            if path:
                paths.append(path)
        return paths

    def _store_path(self, path: Path) -> str:
        if self._root:
            try:
                return path.resolve().relative_to(self._root.resolve()).as_posix()
            except ValueError:
                pass
        return str(path)

    def _resolve_path(self, text: str) -> Path | None:
        path = Path(text)
        if not path.is_absolute() and self._root:
            path = self._root / path
        return path if path.exists() else None

    def _save_playlist(self):
        self._settings.set("ui/sequence/clips", json.dumps(self.clip_paths()))

    def _on_playlist_changed(self, names: list):
        self._save_playlist()
        paths = [path for name, path, duration in self._player.playlist() if path.exists()]
        self._clip_key = tuple((str(path), path.stat().st_mtime) for path in paths)

    def _on_detached(self, detached: bool):
        self._placeholder.setVisible(detached)
        self._player_host.setMinimumHeight(0 if detached else 200)
        self.playingChanged.emit(True)

    def _attach_player(self):
        self._player.attach()

    def _load_paths(self, paths: list[Path]):
        key = tuple((str(path), path.stat().st_mtime) for path in paths)
        if key == self._clip_key:
            return
        if not paths:
            self._clip_key = key
            self._player.stop()
            return
        try:
            timed = ffplay.valid_clips(paths)
        except RuntimeError as exc:
            log.error(str(exc))
            return
        durations = {path: duration for path, duration in timed}
        clips = []
        for path in paths:
            duration = durations.get(path)
            if not duration:
                continue
            clips.append((self._clip_label(path), path, duration))
        if not clips:
            self._clip_key = key
            self._player.stop()
            return
        try:
            self._player.load(clips)
            self._clip_key = key
            if self._settings.get("ui/sequence/clips") is None:
                self._save_playlist()
        except RuntimeError as exc:
            log.error(str(exc))

    def _clip_label(self, path: Path) -> str:
        if self._root:
            try:
                return path.resolve().relative_to(self._root.resolve()).as_posix()
            except ValueError:
                pass
        return path.name

    def _shot_video(self, name: str) -> Path | None:
        if not self._root:
            return None
        folder = self._root / name
        clip = io_utils.latest_version(
            folder / f"{self._stem}{self._suffix}",
            self._settings.get_version_format())
        if clip:
            return clip
        return self._newest_video(folder)

    def _newest_video(self, folder: Path) -> Path | None:
        if not folder.exists() or not folder.is_dir():
            return None
        files = [path for path in folder.iterdir() if path.is_file() and path.suffix.lower() in VIDEO_SUFFIXES]
        if not files:
            return None
        files.sort(key=lambda path: path.stat().st_mtime)
        return files[-1]
