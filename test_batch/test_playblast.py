from __future__ import annotations

from pathlib import Path

import argparse
import sys
import traceback

from maya import standalone as maya_standalone
maya_standalone.initialize()

from maya import cmds

_ROOT_PATH = Path(__file__)
_MODULE_PARENT_PATH = _ROOT_PATH.parent.parent.parent
sys.path.insert(0, str(_MODULE_PARENT_PATH))

from maya_playblast.capture.config import CaptureConfig, ViewConfig
from maya_playblast.capture.frame_capture import FrameCapture
from maya_playblast.core.settings import Settings
from maya_playblast.maya import maya_utils


def _load_scene(scene_path: str):
    print(f"[INFO] OpenScene : {scene_path}")
    cmds.file(scene_path, open=True, force=True)
    print("[INFO] Scene loaded.")


def _parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Test playblast capture in batch/standalone.")
    parser.add_argument("--scene", type=str, default=str(_ROOT_PATH.parent / "test_playblast.ma"), help="Path to a Maya scene (.ma / .mb)")
    parser.add_argument("--output", type=str, default=r"D:\Playblast\BatchOutput.mp4", help="Output video path")
    parser.add_argument("--camera", type=str, default="persp", help="Camera transform or shape")
    parser.add_argument("--start", type=int, default=None, help="Start frame")
    parser.add_argument("--end", type=int, default=None, help="End frame")
    parser.add_argument("--width", type=int, default=960, help="Width in pixels")
    parser.add_argument("--height", type=int, default=540, help="Height in pixels")
    parser.add_argument("--ffmpeg", type=str, required=True, help="Path to ffmpeg.exe")
    return parser.parse_args()


def _set_ffmpeg(path: str):
    ffmpeg_path = Path(path)
    if not ffmpeg_path.exists():
        raise RuntimeError(f"FFmpeg not found: {ffmpeg_path}")
    Settings().set(Settings.FFMPEG_KEY, ffmpeg_path)


def main():

    args = _parse_args()

    print(f"[INFO] Maya {cmds.about(version=True)} — batch={cmds.about(batch=True)}")
    print("[INFO] Capture configuration:")
    print(f"\t\toutput    : {args.output}")
    print(f"\t\tcamera    : {args.camera}")
    print(f"\t\tresolution: {args.width}x{args.height}")
    print(f"\t\tffmpeg    : {args.ffmpeg}")

    _set_ffmpeg(args.ffmpeg)

    _load_scene(args.scene)

    start_frame = args.start if args.start is not None else maya_utils.get_animation_start()
    end_frame = args.end if args.end is not None else maya_utils.get_animation_end()

    capture_config = CaptureConfig(
        output_path=args.output,
        codec="libx264",
        crf=24,
        start_frame=start_frame,
        end_frame=end_frame,
        overwrite=True)

    print(f"\t\tframes    : {capture_config.start_frame} → {capture_config.end_frame} "
          f"({capture_config.frame_count} frames @ {capture_config.frame_rate} fps)")

    view_config = ViewConfig(
        view=None,
        width=args.width,
        height=args.height,
        camera=args.camera)

    print("[INFO] Starting capture...")
    capture = FrameCapture(capture_config, view_config)

    def on_complete(path):
        print(f"[SUCCESS] Capture complete: {path}")

    capture.on_capture_complete.register(on_complete)
    capture.run()


if __name__ == "__main__":
    try:
        main()
    except Exception as exc:
        print(f"\n[ERROR] {exc}")
        traceback.print_exc()
        sys.exit(1)
