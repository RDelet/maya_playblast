from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path

from maya import OpenMayaUI as omui

from ..io import io_utils
from ..maya import maya_ui, maya_utils
from ..maya.viewport import ViewportFlags, VIEWPORT_FLAGS


@dataclass
class CaptureConfig:

    output_path: str | Path
    codec: str = "libx264"
    crf: int = 24
    start_frame: int | None = None
    end_frame: int | None = None
    frame_rate: int | None = None
    # For custom panel
    width: int | None = None
    height: int | None = None

    def __post_init__(self) -> None:
        if self.crf < 0 or self.crf > 51:
            raise ValueError(f"CRF must be between 0 and 51, got {self.crf}")
        
        if isinstance(self.output_path, str):
            self.output_path = Path(self.output_path)
        if self.output_path.exists():
            self.output_path = io_utils.increment_file_path(self.output_path)

        if self.start_frame is None:
            self.start_frame = maya_utils.get_animation_start()
        if self.end_frame is None:
            self.end_frame = maya_utils.get_animation_end()
        if self.frame_rate is None:
            self.frame_rate = maya_utils.get_frame_rate()

    @property
    def frame_count(self) -> int:
        return self.end_frame - self.start_frame + 1



@dataclass
class ViewConfig:

    view: omui.M3dView
    width: int | None = None
    height: int | None = None
    flags: ViewportFlags = field(default_factory=lambda: VIEWPORT_FLAGS.copy())

    def __post_init__(self):
        if self.width is None:
            self.width = self.view.portWidth()
        if self.height is None:
            self.height = self.view.portHeight()

    @classmethod
    def from_active(cls) -> ViewConfig:
        return cls(view=maya_ui.get_active_view())