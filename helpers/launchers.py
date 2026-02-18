from __future__ import annotations
from pathlib import Path
import subprocess

from maya_playblast.helpers import constants
from maya_playblast.helpers.logger import log


def open_player(path: str | Path):
    if isinstance(path, str):
        path = Path(path)
    if not path.exists():
        raise RuntimeError(f"Path {path.as_posix()} does not exists !")

    try:
        cmd = f"{str(constants.PLAYER_PATH)} {str(path)}"
        log.warning(f"Read file {cmd}")
        return subprocess.Popen(cmd,
                                stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL,
                                creationflags=subprocess.DETACHED_PROCESS | subprocess.CREATE_NEW_PROCESS_GROUP)
    except Exception as e:
        raise RuntimeError(f"Impossible to read {path.as_posix()}")


def ffmpeg_capture(width: int, height: int, frame_rate: int, codec: str, crf: int, output_path: str):
    proc_cmd = [str(constants.FFMPEG_PATH),
                '-y',
                '-f', 'rawvideo',
                '-vcodec', 'rawvideo',
                '-pix_fmt', 'rgba',
                '-s', f'{width}x{height}',
                '-framerate', f'{frame_rate}',
                '-i', '-',
                '-vf', 'pad=ceil(iw/2)*2:ceil(ih/2)*2',
                '-c:v', codec, '-crf', f'{crf}',
                '-pix_fmt', 'yuv444p',
                str(output_path)]

    return subprocess.Popen(proc_cmd, stdin=subprocess.PIPE, stderr=subprocess.PIPE)
