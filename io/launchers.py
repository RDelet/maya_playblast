from __future__ import annotations
from pathlib import Path
import subprocess

from maya_playblast.core import constants
from maya_playblast.capture.config import CaptureConfig, ViewConfig
from maya_playblast.core.logger import log


def open_player(path: str | Path):
    if isinstance(path, str):
        path = Path(path)
    if not path.exists():
        raise RuntimeError(f"Path {path} does not exists !")

    try:
        log.warning(f"Open file {path} with {constants.PLAYER_PATH}")
        return subprocess.Popen([str(constants.PLAYER_PATH), str(path)],
                                stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL,
                                creationflags=subprocess.DETACHED_PROCESS | subprocess.CREATE_NEW_PROCESS_GROUP)
    except Exception as e:
        raise RuntimeError(f"Failed  to read {path} !\n\t{e}") from e


def ffmpeg_capture(config: CaptureConfig, view_cfg: ViewConfig):
    proc_cmd = [str(constants.FFMPEG_PATH),
                '-y',
                '-f', 'rawvideo',
                '-vcodec', 'rawvideo',
                '-pix_fmt', 'rgba',
                '-s', f'{view_cfg.width}x{view_cfg.height}',
                '-framerate', f'{config.frame_rate}',
                '-i', '-',
                '-vf', 'pad=ceil(iw/2)*2:ceil(ih/2)*2',
                '-c:v', config.codec, '-crf', f'{config.crf}',
                '-pix_fmt', 'yuv444p',
                str(config.output_path)]

    return subprocess.Popen(proc_cmd, stdin=subprocess.PIPE, stderr=subprocess.PIPE)
