from __future__ import annotations
from pathlib import Path
import subprocess

from ..core.logger import log
from ..core.settings import Settings
from ..capture.config import CaptureConfig, ViewConfig



def open_player(path: str | Path):
    if isinstance(path, str):
        path = Path(path)
    if not path.exists():
        raise RuntimeError(f"Path {path} does not exists !")

    settings = Settings()
    player_path = settings.get_player()
    if not player_path:
        raise RuntimeError("Player path is not set. Please set it in the settings.")
    if not player_path.exists():
        raise RuntimeError(f"Player path {player_path} does not exist. Please check your settings.")

    try:
        log.warning(f"Open file {path} with {player_path}")
        return subprocess.Popen([str(player_path), str(path)],
                                stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL,
                                creationflags=subprocess.DETACHED_PROCESS | subprocess.CREATE_NEW_PROCESS_GROUP)
    except Exception as e:
        raise RuntimeError(f"Failed  to read {path} !\n\t{e}") from e


def ffmpeg_capture(config: CaptureConfig, view_cfg: ViewConfig):
    settings = Settings()
    ffmpeg_path = settings.get_ffmpeg()
    if not ffmpeg_path:
        raise RuntimeError("FFmpeg path is not set. Please set it in the settings.")
    if not ffmpeg_path.exists():
        raise RuntimeError(f"FFmpeg path {ffmpeg_path} does not exist. Please check your settings.")

    proc_cmd = [str(ffmpeg_path),
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
