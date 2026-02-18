from __future__ import annotations

from contextlib import contextmanager
import subprocess
from threading import Thread

from maya import OpenMayaUI as omui

from maya_playblast.helpers import launchers
from maya_playblast.helpers.logger import log
from maya_playblast.ui import editor, utils as uiUtils


@contextmanager
def SetEditorFlag(view: omui.M3DView):
    name = uiUtils.get_editor_from_view(view)
    if not name:
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
    except Exception as e:
        raise e
    finally:
        uiUtils.delete_panel(widget)


@contextmanager
def ImageToVideo(output_path: str, width: int, height: int, frame_rate: int = 30,
                 codec: str = "libx264", crf: int = 24):
    proc = launchers.ffmpeg_capture(width, height, frame_rate, codec, crf, output_path)

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
        proc.wait()
