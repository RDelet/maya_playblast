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
from maya_playblast.maya import maya_utils


def _load_scene(scene_path: str):
    print(f"[INFO] OpenScene : {scene_path}")
    cmds.file(scene_path, open=True, force=True)
    print("[INFO] Scene loaded.")


def _parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Test du plugin PlayblastReadPixels en mode batch/standalone.")
    parser.add_argument("--scene",   type=str, default=str(_ROOT_PATH.parent / "test_playblast.ma"), help="Chemin vers la scène Maya (.ma / .mb)")
    parser.add_argument("--output",  type=str, default=r"D:\Playblast\BatchOutput.mp4", help="Chemin de sortie de la vidéo")
    parser.add_argument("--start",   type=int, default=None, help="Frame de début")
    parser.add_argument("--end",     type=int, default=None, help="Frame de fin")
    parser.add_argument("--width",   type=int, default=960,  help="Largeur en pixels")
    parser.add_argument("--height",  type=int, default=540,  help="Hauteur en pixels")
    return parser.parse_args()


def main():

    args = _parse_args()

    print(f"[INFO] Maya {cmds.about(version=True)} — batch={cmds.about(batch=True)}")
    print(f"[INFO] Configuration de la capture :")
    print(f"\t\toutput  : {args.output}")
    print(f"\t\trésolution : {args.width}x{args.height}")
    
    _load_scene(args.scene)

    capture_config = CaptureConfig(
        output_path=args.output,
        codec="libx264",
        crf=24,
        start_frame=maya_utils.get_animation_start(),
        end_frame=maya_utils.get_animation_end(),
        width=args.width,
        height=args.height,)

    print(f"\t\tframes  : {capture_config.start_frame} → {capture_config.end_frame} "
          f"({capture_config.frame_count} frames @ {capture_config.frame_rate} fps)")

    view_config = ViewConfig(view=None, width=args.width, height=args.height)


    print("[INFO] Démarrage de la capture...")
    capture = FrameCapture(capture_config, view_config)

    def on_complete(path):
        print(f"[SUCCESS] Capture terminée : {path}")

    capture.on_capture_complete.register(on_complete)
    capture.run()


if __name__ == "__main__":
    try:
        main()
    except Exception as exc:
        print(f"\n[ERROR] {exc}")
        traceback.print_exc()
        sys.exit(1)
