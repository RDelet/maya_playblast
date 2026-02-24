# maya_playblast

A custom playblast to override the fucking maya playblast

# Dependencies

- Numpy: https://numpy.org/
- Pillow: https://pypi.org/project/pillow/
- FFmpeg: https://www.ffmpeg.org/
- OpenRV: https://github.com/AcademySoftwareFoundation/OpenRV

# Install numpy and pillow

```python
import maya_playblast
maya_playblast.install_dependencies()
```

# Show UI

```python
from maya_playblast.ui import main

"""
# Use this code if you compile plugin
from maya import cmds

plugin_path = r"D:\Work\GitHub\maya_playblast\plugins\Release\PlayblastReadPixels.mll"
if not cmds.pluginInfo(plugin_path, query=True, loaded=True):
    cmds.loadPlugin(plugin_path)
"""

main.PlayblastDialog().show()
```

# Build Plugins

```
cd ../maya_playblast/plugin
build.bat 2022 "MAYA_SDK_PATH" "OUTPUT_DIR"
```

# Check custom capture commande

```python
from __future__ import annotations

import ctypes
import numpy as np
from PIL import Image

from maya import cmds, OpenMayaUI as omui

from maya_playblast.capture.context import VP2Override

plugin_path = r"D:\Work\GitHub\maya_playblast\plugins\Release\PlayblastReadPixels.mll"
if not cmds.pluginInfo(plugin_path, query=True, loaded=True):
    cmds.loadPlugin(plugin_path)

view   = omui.M3dView.active3dView()
width  = view.portWidth()
height = view.portHeight()

# Force first capture. But why ?...
try:
    cmds.readPixels()
except :
    pass

with VP2Override(view):
    ptr_str = cmds.readPixels()

ptr = int(ptr_str)
c_array = (ctypes.c_uint8 * (width * height * 4)).from_address(ptr)
array = np.ctypeslib.as_array(c_array).reshape((height, width, 4)).copy()[::-1]

output_path = r"D:\output.png"
Image.fromarray(array, mode="RGBA").save(output_path)
```