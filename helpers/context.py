from __future__ import annotations

from contextlib import contextmanager
from pathlib import Path
from threading import Thread

from maya import OpenMayaUI as omui

from maya_playblast.helpers import launchers
from maya_playblast.helpers.config import CaptureConfig
from maya_playblast.helpers.logger import log
from maya_playblast.ui import editor, uiUtils


@contextmanager
def SetEditorFlag(view: omui.M3dView):
    name = uiUtils.get_editor_from_view(view)
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
    widget = uiUtils.create_panel(width, height)
    try:
        yield uiUtils.get_view(widget.panel.objectName())
    finally:
        uiUtils.delete_panel(widget)


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
        proc.stdin.close()
        stderr_thread.join()
        if stderr_lines:
            log.error("ffmpeg stderr:\n" + "\n".join(stderr_lines))
        try:
            proc.wait(timeout=30)
        except Exception as e:
            proc.kill()
            raise e
