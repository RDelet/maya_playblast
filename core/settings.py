from __future__ import annotations

from typing import Dict
from pathlib import Path

try:
    from PySide2 import QtCore
except:
    from PySide6 import QtCore

from ..core.constants import SETTINGS_PATH
from ..io.io_utils import search_exe
from ..maya.viewport import VIEWPORT_FLAGS

from ..core.logger import log


class Settings:

    _instance: Settings | None = None

    FFMPEG_KEY = "paths/ffmpeg"
    PLAYER_KEY = "paths/player"

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._initialized = False

        return cls._instance

    def __init__(self):
        if self._initialized:
            return
        self._setting = QtCore.QSettings(str(SETTINGS_PATH), QtCore.QSettings.IniFormat)
        self._initialized = True

        self._check_ffpeg_path()
        self._check_player_path()

    def _check_ffpeg_path(self):
        ffmpeg_path = self.get_ffmpeg()
        if not ffmpeg_path or not ffmpeg_path.exists:
            path = search_exe("ffmpeg")
            if path:
                self.set(self.FFMPEG_KEY, path)
                self.save()
            else:
                log.warning("ffmpeg not found in PATH. Please set the path to ffmpeg executable in the settings.")
    
    def _check_player_path(self):
        player_path = self.get_player()
        if not player_path or not player_path.exists:
            path = search_exe("OpenRV")
            if not path:
                log.warning("OpenRV not found in PATH. Checking for vlc...")
            path = search_exe("vlc")
            if not path:
                log.warning("vlc not found in PATH. Please set the path to vlc executable in the settings.")
            
            if path:
                self.set(self.PLAYER_KEY, path)
                self.save()
    
    def get_ffmpeg(self) -> Path:
        return Path(Settings().get(self.FFMPEG_KEY))

    def get_player(self) -> Path:
        return Path(Settings().get(self.PLAYER_KEY))

    def get(self, key: str):
        return self._setting.value(key, None)

    def set(self, key: str, value: str | float | int | bool):
        self._setting.setValue(key, str(value))

    def save(self):
        self._setting.sync()