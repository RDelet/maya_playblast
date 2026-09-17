from __future__ import annotations

from contextlib import contextmanager
from threading import Thread

from ..core.logger import log
from ..io import launchers
from ..maya import maya_ui, viewport
from ..capture.config import CaptureConfig, ViewConfig


@contextmanager
def SetEditorFlag(view_cfg: ViewConfig):
    if not view_cfg.view:
        yield
        return

    name = maya_ui.get_editor_from_view(view_cfg.view)
    if not name:
        log.warning("Impossible to get editor from view.")
        yield
        return

    states = viewport.VIEWPORT_FLAGS.snapshot(name)
    try:
        viewport.set_viewport_states(name, view_cfg.flags)
        yield
    finally:
        viewport.set_viewport_states(name, states)


@contextmanager
def ImageToVideo(config_cfg: CaptureConfig, view_cfg: ViewConfig):
    proc = launchers.ffmpeg_capture(config_cfg, view_cfg)

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
        raise
    finally:
        try:
            proc.stdin.close()
        except Exception as e:
            log.warning(f"Failed to close stdin: {e}")

        stderr_thread.join()
        try:
            proc.wait(timeout=30)
        except Exception:
            log.error("FFmpeg did not terminate in time, killing process.")
            proc.kill()
            proc.wait(timeout=5)

        if proc.returncode not in (0, None):
            if stderr_lines:
                log.error("ffmpeg stderr:\n" + "\n".join(stderr_lines))
            raise RuntimeError(f"FFmpeg failed with code {proc.returncode}.")
