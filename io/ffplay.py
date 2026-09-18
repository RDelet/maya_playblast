from __future__ import annotations

import ctypes
import os
import subprocess
import sys
import tempfile
from pathlib import Path

from ..core.logger import log
from ..core.settings import Settings

WINDOW_TITLE = "maya_playblast_seq"

_USER32 = None
if sys.platform == "win32":
    _USER32 = ctypes.WinDLL("user32", use_last_error=True)
    _USER32.GetWindowThreadProcessId.argtypes = [ctypes.c_void_p, ctypes.POINTER(ctypes.c_ulong)]
    _USER32.GetWindowThreadProcessId.restype = ctypes.c_ulong
    _USER32.GetWindowLongPtrW.argtypes = [ctypes.c_void_p, ctypes.c_int]
    _USER32.GetWindowLongPtrW.restype = ctypes.c_ssize_t
    _USER32.SetWindowLongPtrW.argtypes = [ctypes.c_void_p, ctypes.c_int, ctypes.c_ssize_t]
    _USER32.SetWindowLongPtrW.restype = ctypes.c_ssize_t
    _USER32.SetParent.argtypes = [ctypes.c_void_p, ctypes.c_void_p]
    _USER32.SetParent.restype = ctypes.c_void_p
    _USER32.MoveWindow.argtypes = [
        ctypes.c_void_p,
        ctypes.c_int,
        ctypes.c_int,
        ctypes.c_int,
        ctypes.c_int,
        ctypes.c_bool
    ]
    _USER32.MoveWindow.restype = ctypes.c_bool
    _USER32.FindWindowW.argtypes = [ctypes.c_wchar_p, ctypes.c_wchar_p]
    _USER32.FindWindowW.restype = ctypes.c_void_p
    _USER32.SetWindowPos.argtypes = [
        ctypes.c_void_p,
        ctypes.c_void_p,
        ctypes.c_int,
        ctypes.c_int,
        ctypes.c_int,
        ctypes.c_int,
        ctypes.c_uint
    ]
    _USER32.SetWindowPos.restype = ctypes.c_bool
    _USER32.IsWindow.argtypes = [ctypes.c_void_p]
    _USER32.IsWindow.restype = ctypes.c_bool
    _USER32.GetWindowTextLengthW.argtypes = [ctypes.c_void_p]
    _USER32.GetWindowTextLengthW.restype = ctypes.c_int
    _USER32.SendMessageW.argtypes = [ctypes.c_void_p, ctypes.c_uint, ctypes.c_size_t, ctypes.c_size_t]
    _USER32.SendMessageW.restype = ctypes.c_ssize_t


def write_concat_list(clips: list[Path]) -> Path:
    path = Path(tempfile.gettempdir()) / "maya_playblast_concat.txt"
    lines = []
    for clip in clips:
        text = clip.resolve().as_posix().replace("'", r"'\''")
        lines.append(f"file '{text}'")
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")
    return path


def probe_duration(path: Path) -> float | None:
    ffprobe = Settings().get_ffprobe()
    if not ffprobe or not ffprobe.exists():
        raise RuntimeError("FFprobe path is not set. Please set it in the settings.")
    result = subprocess.run(
        [str(ffprobe), "-v", "error", "-show_entries", "format=duration", "-of", "csv=p=0", str(path)],
        stdout=subprocess.PIPE,
        stderr=subprocess.DEVNULL,
        universal_newlines=True,
        creationflags=_no_window_flags())
    try:
        duration = float((result.stdout or "").strip())
    except ValueError:
        return None
    if duration <= 0:
        return None
    return duration


def valid_clips(clips: list[Path]) -> list[tuple[Path, float]]:
    kept = []
    for clip in clips:
        try:
            duration = probe_duration(clip)
            if duration:
                kept.append((clip, duration))
            else:
                log.warning(f"Skipping invalid clip: {clip}")
        except RuntimeError:
            raise
        except Exception as exc:
            log.warning(f"Skipping clip {clip}: {exc}")
    return kept


def probe_fps(path: Path) -> float:
    ffprobe = Settings().get_ffprobe()
    if not ffprobe or not ffprobe.exists():
        return 24.0
    result = subprocess.run(
        [str(ffprobe), "-v", "error", "-select_streams", "v:0",
         "-show_entries", "stream=r_frame_rate", "-of", "csv=p=0", str(path)],
        stdout=subprocess.PIPE,
        stderr=subprocess.DEVNULL,
        universal_newlines=True,
        creationflags=_no_window_flags())
    text = (result.stdout or "").strip()
    if "/" in text:
        num, den = text.split("/", 1)
        try:
            value = float(num) / float(den)
            if value > 0:
                return value
        except ValueError:
            pass
    try:
        value = float(text)
        if value > 0:
            return value
    except ValueError:
        pass
    return 24.0


def start_ffplay(concat_path: Path, width: int, height: int, start_seconds: float = 0.0) -> subprocess.Popen:
    ffplay = Settings().get_ffplay()
    if not ffplay or not ffplay.exists():
        raise RuntimeError("FFplay path is not set. Please set it in the settings.")

    cmd = [
        str(ffplay),
        "-f", "concat",
        "-safe", "0",
        "-i", str(concat_path)
    ]
    if start_seconds > 0.001:
        cmd.extend(["-ss", f"{start_seconds:.3f}"])
    cmd.extend([
        "-autoexit",
        "-noborder",
        "-window_title", WINDOW_TITLE,
        "-left", "-32000",
        "-top", "-32000",
        "-x", str(max(width, 16)),
        "-y", str(max(height, 16)),
        "-loglevel", "quiet"
    ])
    kwargs = {
        "stdout": subprocess.DEVNULL,
        "stderr": subprocess.DEVNULL,
        "stdin": subprocess.DEVNULL,
        "env": os.environ.copy()
    }
    if sys.platform == "win32":
        kwargs["creationflags"] = _no_window_flags() | getattr(subprocess, "CREATE_NEW_PROCESS_GROUP", 0)
    return subprocess.Popen(cmd, **kwargs)


def find_window_hwnd(pid: int) -> int | None:
    if _USER32 is None:
        return None
    titled = _USER32.FindWindowW(None, WINDOW_TITLE)
    if titled:
        return int(titled)
    titled = []
    others = []
    enum_proc = ctypes.WINFUNCTYPE(ctypes.c_int, ctypes.c_void_p, ctypes.c_void_p)

    def callback(hwnd, lparam):
        proc_id = ctypes.c_ulong()
        _USER32.GetWindowThreadProcessId(hwnd, ctypes.byref(proc_id))
        if proc_id.value != pid:
            return 1
        if _USER32.GetWindowTextLengthW(hwnd) > 0:
            titled.append(int(hwnd))
        else:
            others.append(int(hwnd))
        return 1

    callback_ref = enum_proc(callback)
    _USER32.EnumWindows(callback_ref, 0)
    found = titled or others
    return found[0] if found else None


def parent_window(child_hwnd: int, parent_hwnd: int, width: int, height: int) -> bool:
    if _USER32 is None:
        return False
    if not _USER32.IsWindow(child_hwnd) or not _USER32.IsWindow(parent_hwnd):
        return False
    gwl_style = -16
    ws_child = 0x40000000
    ws_visible = 0x10000000
    ws_clipsiblings = 0x04000000
    ws_popup = 0x80000000
    swp_showwindow = 0x0040
    swp_framechanged = 0x0020
    style = _USER32.GetWindowLongPtrW(child_hwnd, gwl_style)
    style = (style & ~ws_popup) | ws_child | ws_visible | ws_clipsiblings
    _USER32.SetWindowLongPtrW(child_hwnd, gwl_style, style)
    _USER32.SetParent(child_hwnd, parent_hwnd)
    _USER32.SetWindowPos(child_hwnd, 0, 0, 0, max(width, 16), max(height, 16), swp_showwindow | swp_framechanged)
    return True


def move_window(hwnd: int, width: int, height: int):
    if _USER32 is None:
        return
    if not _USER32.IsWindow(hwnd):
        return
    width = max(int(width), 16)
    height = max(int(height), 16)
    swp_nozorder = 0x0004
    swp_showwindow = 0x0040
    swp_framechanged = 0x0020
    _USER32.SetWindowPos(hwnd, 0, 0, 0, width, height, swp_nozorder | swp_showwindow | swp_framechanged)
    _USER32.MoveWindow(hwnd, 0, 0, width, height, True)
    wm_size = 0x0005
    lparam = (height << 16) | (width & 0xFFFF)
    _USER32.SendMessageW(hwnd, wm_size, 0, lparam)


def stop_process(proc: subprocess.Popen | None):
    if not proc:
        return
    if proc.poll() is not None:
        return
    proc.terminate()
    try:
        proc.wait(timeout=2)
    except Exception:
        proc.kill()


def _no_window_flags() -> int:
    if sys.platform != "win32":
        return 0
    return getattr(subprocess, "CREATE_NO_WINDOW", 0x08000000)
