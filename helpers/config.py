from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Optional

from maya_playblast.helpers import file, maya_utils


@dataclass
class CaptureConfig:

    output_path: str | Path
    codec: str = "libx264"
    crf: int = 24
    start_frame: Optional[int] = None
    end_frame: Optional[int] = None
    frame_rate: Optional[int] = None

    def __post_init__(self) -> None:
        if self.crf < 0 or self.crf > 51:
            raise ValueError(f"CRF must be between 0 and 51, got {self.crf}")
        
        if isinstance(self.output_path, str):
            self.output_path = Path(self.output_path)
        if self.output_path.exists():
            self.output_path = file.increment_file_path(self.output_path)

        if self.start_frame is None:
            self.start_frame = maya_utils.get_animation_start()
        if self.end_frame is None:
            self.end_frame = maya_utils.get_animation_end()
        if self.frame_rate is None:
            self.frame_rate = maya_utils.get_frame_rate()

    @property
    def frame_count(self) -> int:
        return self.end_frame - self.start_frame + 1
