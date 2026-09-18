from __future__ import annotations

import collections
import subprocess
import sys
import threading
from pathlib import Path

try:
    from PySide2 import QtCore
except ImportError:
    from PySide6 import QtCore

from ..core.settings import Settings


class FrameCache:

    def __init__(self, max_frames: int = 400):
        self._max = max(1, int(max_frames))
        self._data = collections.OrderedDict()

    def clear(self):
        self._data.clear()

    def has(self, frame: int) -> bool:
        return frame in self._data

    def nearest(self, frame: int):
        if not self._data:
            return None
        if frame in self._data:
            self._data.move_to_end(frame)
            return self._data[frame]
        closest = min(self._data, key=lambda key: abs(key - frame))
        return self._data[closest]

    def get(self, frame: int):
        data = self._data.get(frame)
        if data is None:
            return None
        self._data.move_to_end(frame)
        return data

    def put(self, frame: int, data: bytes):
        if not data:
            return
        self._data[frame] = data
        self._data.move_to_end(frame)
        while len(self._data) > self._max:
            self._data.popitem(last=False)


class FrameGrabber(QtCore.QThread):

    frameReady = QtCore.Signal(int, int, bytes)

    def __init__(self, parent: QtCore.QObject | None = None):
        super().__init__(parent)
        self._lock = threading.Lock()
        self._event = threading.Event()
        self._stop = False
        self._urgent = None
        self._prefetch = []

    def ask(self, generation: int, frame: int, path: Path, seconds: float, urgent: bool = True):
        job = (generation, frame, path, seconds)
        with self._lock:
            if urgent:
                self._urgent = job
            elif job not in self._prefetch:
                self._prefetch.append(job)
                if len(self._prefetch) > 8:
                    self._prefetch.pop(0)
        self._event.set()

    def cancel(self):
        with self._lock:
            self._urgent = None
            self._prefetch = []

    def shutdown(self):
        self._stop = True
        self.cancel()
        self._event.set()
        self.wait(2000)

    def run(self):
        while not self._stop:
            self._event.wait(0.25)
            self._event.clear()
            if self._stop:
                return
            job = None
            with self._lock:
                if self._urgent is not None:
                    job = self._urgent
                    self._urgent = None
                elif self._prefetch:
                    job = self._prefetch.pop(0)
            if job is None:
                continue
            generation, frame, path, seconds = job
            data = extract_jpeg(path, seconds)
            if data and not self._stop:
                self.frameReady.emit(generation, frame, data)


def extract_jpeg(path: Path, seconds: float) -> bytes:
    ffmpeg = Settings().get_ffmpeg()
    if not ffmpeg or not ffmpeg.exists():
        return b""
    cmd = [
        str(ffmpeg),
        "-v", "error",
        "-ss", f"{max(0.0, seconds):.4f}",
        "-i", str(path),
        "-frames:v", "1",
        "-f", "mjpeg",
        "-q:v", "3",
        "pipe:1"
    ]
    kwargs = {
        "stdout": subprocess.PIPE,
        "stderr": subprocess.DEVNULL,
        "stdin": subprocess.DEVNULL
    }
    if sys.platform == "win32":
        kwargs["creationflags"] = getattr(subprocess, "CREATE_NO_WINDOW", 0x08000000)
    result = subprocess.run(cmd, **kwargs)
    return result.stdout or b""


def clip_at(clips: list[tuple[Path, float]], seconds: float) -> tuple[Path, float] | None:
    if not clips:
        return None
    remaining = max(0.0, seconds)
    last_index = len(clips) - 1
    for index, (path, duration) in enumerate(clips):
        if remaining <= duration or index == last_index:
            local = min(remaining, max(duration - 0.001, 0.0))
            return path, max(0.0, local)
        remaining -= duration
    path, duration = clips[-1]
    return path, max(0.0, duration - 0.001)
