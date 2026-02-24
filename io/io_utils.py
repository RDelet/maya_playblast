from __future__ import annotations

from pathlib import Path
import platform
import shutil
import subprocess
import sys
from importlib import import_module

from ..core.logger import log


def get_platform() -> str | None:
    return platform.system().lower()


def increment_file_path(path: str | Path) -> Path:
    if isinstance(path, str):
        path = Path(path)

    i = 1
    while path.exists():
        new_path = path.parent / f"{path.stem}_{i}{path.suffix}"
        if not new_path.exists():
            return new_path
        i += 1
    
    return path


def check_directory(path: str | Path, build: bool = True) -> bool:
    if isinstance(path, str):
        path = Path(path)
    if path.suffix:
        path = path.parent

    if not path.exists():
        if build:
            path.mkdir(parents=True, exist_ok=True)
        else:
            return False
    
    return path.exists()


def search_exe(exe_name: str) -> Path | None:
    found = shutil.which(exe_name)
    if found:
        return Path(found)

    return None


def install_module(module_name: str, package_name: str | None = None) -> bool:
    package = package_name or module_name

    if _is_importable(module_name):
        log.debug(f"'{module_name}' already installed, installation ignored.")
        return True

    log.debug(f"Install '{package}' with pip...")

    try:
        maya_py = Path(sys.executable).parent / "mayapy.exe"
        result = subprocess.run([str(maya_py), "-m", "pip", "install", package],
                                stdout=subprocess.PIPE,
                                stderr=subprocess.PIPE,
                                timeout=120)
    except subprocess.TimeoutExpired:
        log.error(f"Timeout when installing '{package}'.")
        return False
    except Exception as e:
        log.error(f"Error during installation of '{package}' : {e}")
        return False
    
    return True if result.returncode == 0 else False


def _is_importable(module_name: str) -> bool:
    try:
        import_module(module_name)
        return True
    except ImportError:
        return False