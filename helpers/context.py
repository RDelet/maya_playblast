from __future__ import annotations

from contextlib import contextmanager
from pathlib import Path
from threading import Thread

from maya import OpenMayaUI as omui

from maya_playblast.helpers import launchers
from maya_playblast.helpers.config import CaptureConfig
from maya_playblast.helpers.logger import log
from maya_playblast.ui import editor, ui_utils


@contextmanager
def SetEditorFlag(view: omui.M3dView):
    name = ui_utils.get_editor_from_view(view)
    if not name:
        yield
        return

    states = editor.VIEWPORT_FLAGS.snapshot(name)
    try:
        yield editor.disable_viewport_state(name)
    finally:
        editor.set_viewport_state(name, states)


@contextmanager
def UseNewPanel(width: int, height: int):
    widget = ui_utils.create_panel(width, height)
    try:
        yield ui_utils.get_view(widget.panel.objectName())
    finally:
        ui_utils.delete_panel(widget)


@contextmanager
def ImageToVideo(config: CaptureConfig, width: int, height: int):
    proc = launchers.ffmpeg_capture(config, width, height)

    stderr_lines = []
    def drain_stderr():
        for line in proc.stderr:
            stderr_lines.append(line.decode(errors="replace").strip())

    stderr_thread = Thread(target=drain_stderr, daemon=True)
    stderr_thread.start()

    try:
        yield proc
    except Exception as e:
        log.error(e)
        raise e
    finally:
        try:
            proc.stdin.close()
        except Exception as e:
            log.warning(f"Failed to close stdin: {e}")

        stderr_thread.join()
        if stderr_lines:
            log.error("ffmpeg stderr:\n" + "\n".join(stderr_lines))
        try:
            proc.wait(timeout=30)
        except Exception as e:
            log.error("FFmpeg did not terminate in time, killing process.")
            proc.kill()
