from __future__ import annotations

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
        if not self.ffmpeg_path or not self.ffmpeg_path.exists:
            path = search_exe("ffmpeg")
            if path:
                self.ffmpeg_path = path
                self.save()
            else:
                log.warning("ffmpeg not found in PATH. Please set the path to ffmpeg executable in the settings.")
    
    def _check_player_path(self):
        if not self.player_path or not self.player_path.exists:
            path = search_exe("OpenRV")
            if not path:
                log.warning("OpenRV not found in PATH. Checking for vlc...")
            path = search_exe("vlc")
            if not path:
                log.warning("vlc not found in PATH. Please set the path to vlc executable in the settings.")
            
            if path:
                self.player_path = path
                self.save()
    
    @property
    def ffmpeg_path(self) -> Path | None:
        val = self._setting.value("paths/ffmpeg", None)
        return Path(val) if val else None

    @ffmpeg_path.setter
    def ffmpeg_path(self, value: str | Path | None):
        if value:
            if not isinstance(value, (str, Path)):
                value = Path(value)
            self._setting.setValue("paths/ffmpeg", str(value))
        else:
            self._setting.remove("paths/ffmpeg")

    @property
    def player_path(self) -> Path | None:
        val = self._setting.value("paths/player", None)
        return Path(val) if val else None

    @player_path.setter
    def player_path(self, value: str | Path | None):
        if value:
            if not isinstance(value, (str, Path)):
                value = Path(value)
            self._setting.setValue("paths/player", str(value))
        else:
            self._setting.remove("paths/player")

    @property
    def output_path(self) -> Path | None:
        val = self._setting.value("capture/last_output", None)
        return Path(val) if val else None

    @output_path.setter
    def output_path(self, value: str | Path | None):
        if value:
            self._setting.setValue("capture/last_output", str(value))

    @property
    def encoder(self) -> str:
        return self._setting.value("capture/encoder", 0)

    @encoder.setter
    def encoder(self, value: int):
        self._setting.setValue("capture/encoder", value)
    
    @property
    def muxer(self) -> str:
        return self._setting.value("capture/muxer", 0)

    @muxer.setter
    def muxer(self, value: int):
        self._setting.setValue("capture/muxer", value)

    @property
    def last_crf(self) -> int:
        return int(self._setting.value("capture/crf", 24))

    @last_crf.setter
    def last_crf(self, value: int):
        self._setting.setValue("capture/crf", value)
    
    @property
    def viewport_flags(self) -> dict[str, bool]:
        flags = {}
        for flag in VIEWPORT_FLAGS:
            val = self._setting.value(f"viewport_flags/{flag.name}", None)
            flags[flag.name] = val.lower() == "true"

        return flags
    
    @viewport_flags.setter
    def viewport_flags(self, flags: dict[str, bool]):
        for name, value in flags.items():
            self._setting.setValue(f"viewport_flags/{name}", str(value))

    def save(self):
        self._setting.sync()