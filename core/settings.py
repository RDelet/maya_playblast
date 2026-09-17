from __future__ import annotations

from pathlib import Path

try:
    from PySide2 import QtCore
except ImportError:
    from PySide6 import QtCore

from maya import cmds

from ..core.constants import ROOT_PATH
from ..io.io_utils import search_exe
from ..core.logger import log


def _settings_path() -> Path:
    maya_dir = Path(cmds.internalVar(userAppDir=True))
    prefs_dir = maya_dir / "prefs"
    prefs_dir.mkdir(parents=True, exist_ok=True)
    return prefs_dir / f"{ROOT_PATH.name}.ini"


class Settings:

    FFMPEG_KEY = "paths/ffmpeg"
    PLAYER_KEY = "paths/player"
    _qsettings: QtCore.QSettings | None = None
    _bootstrapped = False

    def __init__(self):
        if Settings._qsettings is None:
            Settings._qsettings = QtCore.QSettings(str(_settings_path()), QtCore.QSettings.IniFormat)
        self._setting = Settings._qsettings
        if not Settings._bootstrapped:
            Settings._bootstrapped = True
            self._check_ffmpeg_path()
            self._check_player_path()

    def _check_ffmpeg_path(self):
        ffmpeg_path = self.get_ffmpeg()
        if ffmpeg_path and ffmpeg_path.exists():
            return
        path = search_exe("ffmpeg")
        if path:
            self.set(self.FFMPEG_KEY, path)
            self.save()
        else:
            log.warning("ffmpeg not found in PATH. Please set the path to ffmpeg executable in the settings.")

    def _check_player_path(self):
        player_path = self.get_player()
        if player_path and player_path.exists():
            return
        path = search_exe("OpenRV") or search_exe("vlc")
        if path:
            self.set(self.PLAYER_KEY, path)
            self.save()
        else:
            log.warning("Player not found in PATH. Please set the path to a video player in the settings.")

    def get_ffmpeg(self) -> Path | None:
        return self._as_path(self.get(self.FFMPEG_KEY))

    def get_player(self) -> Path | None:
        return self._as_path(self.get(self.PLAYER_KEY))

    def get(self, key: str):
        return self._setting.value(key, None)

    def set(self, key: str, value: str | float | int | bool | Path):
        self._setting.setValue(key, str(value))
        self.save()

    def save(self):
        self._setting.sync()

    def _as_path(self, value) -> Path | None:
        if not value:
            return None
        return Path(value)
