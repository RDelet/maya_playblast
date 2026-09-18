from __future__ import annotations

from pathlib import Path

try:
    from PySide2 import QtCore
except ImportError:
    from PySide6 import QtCore

from maya import cmds

from ..core.constants import ROOT_PATH
from ..io.io_utils import VersionFormat, search_exe
from ..core.logger import log


def _settings_path() -> Path:
    maya_dir = Path(cmds.internalVar(userAppDir=True))
    prefs_dir = maya_dir / "prefs"
    prefs_dir.mkdir(parents=True, exist_ok=True)
    return prefs_dir / f"{ROOT_PATH.name}.ini"


def prefs_dir() -> Path:
    return _settings_path().parent


class Settings:

    FFMPEG_KEY = "paths/ffmpeg"
    FFPLAY_KEY = "paths/ffplay"
    FFPROBE_KEY = "paths/ffprobe"
    PLAYER_KEY = "paths/player"
    MAYA_FOLDER_KEY = "output/maya_folder"
    DEFAULT_MAYA_FOLDER = "playblast"
    VERSION_PREFIX_KEY = "output/version_prefix"
    VERSION_PADDING_KEY = "output/version_padding"
    VERSION_SUFFIX_KEY = "output/version_suffix"
    DEFAULT_VERSION_PREFIX = "_v"
    DEFAULT_VERSION_PADDING = 3
    _TOOL_KEYS = (("ffmpeg", FFMPEG_KEY), ("ffplay", FFPLAY_KEY), ("ffprobe", FFPROBE_KEY))
    _qsettings: QtCore.QSettings | None = None
    _bootstrapped = False

    def __init__(self):
        if Settings._qsettings is None:
            Settings._qsettings = QtCore.QSettings(str(_settings_path()), QtCore.QSettings.IniFormat)
        self._setting = Settings._qsettings
        if not Settings._bootstrapped:
            Settings._bootstrapped = True
            self._check_ffmpeg_tools()
            self._check_player_path()

    def _check_ffmpeg_tools(self):
        for name, key in self._TOOL_KEYS:
            path = self.get_path(key)
            if path and path.exists():
                continue
            found = search_exe(name)
            if found:
                self.set(key, found)
        self.fill_ffmpeg_siblings()
        missing = [name for name, key in self._TOOL_KEYS if not self._existing(key)]
        if missing:
            log.warning(
                f"{', '.join(missing)} not found. Please set the path in the settings.")

    def fill_ffmpeg_siblings(self):
        resolved = []
        for name, key in self._TOOL_KEYS:
            path = self.get_path(key)
            if path and path.exists():
                resolved.append(path)
        if not resolved:
            return
        seed = resolved[0]
        for name, key in self._TOOL_KEYS:
            if self._existing(key):
                continue
            sibling = seed.with_name(name + seed.suffix)
            if sibling.exists():
                self.set(key, sibling)

    def _check_player_path(self):
        player_path = self.get_path(self.PLAYER_KEY)
        if player_path and player_path.exists():
            return
        path = search_exe("OpenRV") or search_exe("vlc")
        if path:
            self.set(self.PLAYER_KEY, path)
        else:
            log.warning("Player not found in PATH. Please set the path to a video player in the settings.")

    def get_version_format(self) -> VersionFormat:
        prefix = self.get(self.VERSION_PREFIX_KEY)
        suffix = self.get(self.VERSION_SUFFIX_KEY)
        padding = self.get(self.VERSION_PADDING_KEY)
        if prefix is None:
            prefix = self.DEFAULT_VERSION_PREFIX
        if suffix is None:
            suffix = ""
        if padding is None or str(padding) == "":
            padding = self.DEFAULT_VERSION_PADDING
        return VersionFormat(str(prefix), padding, str(suffix))

    def get(self, key: str, default=None):
        value = self._setting.value(key, None)
        return default if value is None else value

    def get_path(self, key: str) -> Path | None:
        return self._as_path(self.get(key))

    def set(self, key: str, value: str | float | int | bool | Path):
        self._setting.setValue(key, str(value))
        self.save()

    def save(self):
        self._setting.sync()

    def _existing(self, key: str) -> bool:
        path = self.get_path(key)
        return bool(path and path.exists())

    def _as_path(self, value) -> Path | None:
        if not value:
            return None
        return Path(value)
