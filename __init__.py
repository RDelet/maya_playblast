from __future__ import annotations

import platform

from maya import cmds

from ._core import record, install_dependencies
from .core import constants
from .core.logger import log
from .io import io_utils
from .maya import maya_utils

__all__ = ["record", install_dependencies]


def load_plugins():
    maya_dir = f"maya{maya_utils.get_version()}"
    plugin_name = "PlayblastReadPixels.mll"
    plugin_path = str(constants.ROOT_PATH / "plugins" / io_utils.get_platform() / maya_dir / "Release" / plugin_name)

    if cmds.pluginInfo(plugin_path, query=True, loaded=True):
        log.warning(f"Plugin {plugin_path} already load.")
        return
    
    try:
        log.warning(f"Try to load plugin {plugin_path}.")
        cmds.loadPlugin(plugin_path)
    except Exception as e:
        log.error(f"Failed to load plugin {plugin_path}: {e}")
    finally:
        log.warning(f"Plugin {plugin_path} loaded.")


load_plugins()