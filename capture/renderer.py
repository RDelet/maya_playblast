from __future__ import annotations

import ctypes

import numpy as np
from maya import cmds

from .config import ViewConfig
from ..core.logger import log
from ..maya import look, maya_ui, maya_utils, viewport

try:
    from maya.api import OpenMayaRender as omr
except ImportError:
    omr = None


_BGRA_FORMATS = set()
if omr is not None:
    _BGRA_FORMATS = {omr.MRenderer.kB8G8R8A8, omr.MRenderer.kB8G8R8X8}


class ViewportRenderer:

    def __init__(self, view_config: ViewConfig):
        self._view_cfg = view_config
        self._target_manager = None
        self._target = None
        self._source_name = ""
        self._source_fallback = ""
        self._capture_window = ""

    def setup(self) -> None:
        if omr is None:
            raise RuntimeError("OpenMayaRender is not available.")

        self._target_manager = omr.MRenderer.getRenderTargetManager()
        if self._target_manager is None:
            raise RuntimeError("Viewport 2.0 render target manager is not initialized.")

        self._source_name, self._source_fallback = self._resolve_sources()
        self._target = self._acquire_target()
        if not self._render():
            raise RuntimeError(f"MRenderer.render failed for source '{self._source_name}'.")

        log.debug(f"ViewportRenderer source: {self._source_name}")

    def teardown(self) -> None:
        if self._capture_window:
            maya_ui.delete_capture_panel(self._capture_window)
            self._capture_window = ""
        if self._target_manager is not None and self._target is not None:
            self._target_manager.releaseRenderTarget(self._target)
        self._target = None
        self._target_manager = None

    def capture_frame(self, frame: int) -> np.ndarray:
        maya_utils.current_time(frame)
        if not self._render():
            raise RuntimeError(f"MRenderer.render failed for source '{self._source_name}'.")
        return self._pixels_from_target()

    def _resolve_sources(self) -> tuple[str, str]:
        if cmds.about(batch=True) or not self._view_cfg.view:
            shape = maya_utils.camera_shape(self._view_cfg.camera)
            return f"batch:{shape}", f"batch:{self._view_cfg.camera}"

        panel = self._view_cfg.model_panel
        if not panel:
            raise RuntimeError("Could not resolve model panel from the active view.")

        view_w = self._view_cfg.view.portWidth()
        view_h = self._view_cfg.view.portHeight()
        if self._view_cfg.width == view_w and self._view_cfg.height == view_h:
            return f"viewport:{panel}", panel

        try:
            window, sized_panel, editor = maya_ui.create_capture_panel(
                self._view_cfg.width,
                self._view_cfg.height,
                self._view_cfg.camera)
            self._capture_window = window
            self._copy_panel_state(panel, editor)
            cmds.refresh(force=True)
            log.debug(f"Capture panel {sized_panel} at {self._view_cfg.width}x{self._view_cfg.height}")
            return f"viewport:{sized_panel}", sized_panel
        except Exception as exc:
            log.warning(f"Could not open sized capture view, using active panel: {exc}")
            return f"viewport:{panel}", panel

    def _copy_panel_state(self, source_panel: str, dest_editor: str):
        source_editor = cmds.modelPanel(source_panel, query=True, modelEditor=True)
        viewport.set_viewport_states(dest_editor, self._view_cfg.flags)
        look.apply_look(look.read_look(source_editor), dest_editor)
        try:
            appearance = cmds.modelEditor(source_editor, query=True, displayAppearance=True)
            cmds.modelEditor(dest_editor, edit=True, displayAppearance=appearance)
        except Exception:
            pass

    def _acquire_target(self):
        desc = omr.MRenderTargetDescription()
        desc.setName("maya_playblast_color")
        desc.setWidth(self._view_cfg.width)
        desc.setHeight(self._view_cfg.height)
        desc.setArraySliceCount(1)
        desc.setMultiSampleCount(1)
        desc.setRasterFormat(omr.MRenderer.kR8G8B8A8_UNORM)
        target = self._target_manager.acquireRenderTarget(desc)
        if target is None:
            raise RuntimeError("Failed to acquire Viewport 2.0 render target.")
        return target

    def _render(self) -> bool:
        if omr.MRenderer.render(self._source_name, [self._target]):
            return True
        if self._source_fallback and omr.MRenderer.render(self._source_fallback, [self._target]):
            log.debug(f"ViewportRenderer source fallback: {self._source_fallback}")
            self._source_name = self._source_fallback
            self._source_fallback = ""
            return True
        return False

    def _pixels_from_target(self) -> np.ndarray:
        ptr, row_pitch, slice_pitch = self._target.rawData()
        try:
            raw = ctypes.string_at(int(ptr), int(slice_pitch))
            packed = np.frombuffer(raw, dtype=np.uint8).copy()
        finally:
            omr.MRenderTarget.freeRawData(ptr)

        width = self._view_cfg.width
        height = self._view_cfg.height
        row_bytes = int(row_pitch)
        needed = height * row_bytes
        if packed.size < needed:
            raise RuntimeError(f"Unexpected raw buffer size {packed.size} for {width}x{height} pitch {row_bytes}.")
        if row_bytes < width * 4:
            raise RuntimeError(f"Unexpected row pitch {row_bytes} for width {width}.")

        rows = packed[:needed].reshape((height, row_bytes))
        pixels = rows[:, :width * 4].reshape((height, width, 4))

        format_id = self._target.targetDescription().rasterFormat()
        if format_id in _BGRA_FORMATS:
            pixels = pixels[:, :, [2, 1, 0, 3]]

        return np.ascontiguousarray(pixels)
