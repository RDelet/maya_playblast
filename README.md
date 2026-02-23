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
main.PlayblastDialog().show()
```

# Build Plugins

```
cd ../maya_playblast/plugin
build.bat 2022 "MAYA_SDK_PATH" "OUTPUT_DIR"
```

# Check custom capture commande

```python
import ctypes
import numpy as np
from PIL import Image

from maya import OpenMayaUI as omui

plugin_path = r"D:\Work\GitHub\maya_playblast\plugins\Release\PlayblastReadPixels.mll"
if not cmds.pluginInfo(plugin_path, query=True, loaded=True):
    cmds.loadPlugin(plugin_path)

view   = omui.M3dView.active3dView()
width  = view.portWidth()
height = view.portHeight()

ptr_str = cmds.readPixels()
ptr = int(ptr_str)
c_array = (ctypes.c_uint8 * (width * height * 4)).from_address(ptr)
array = np.ctypeslib.as_array(c_array).reshape((height, width, 4)).copy()

output_path = r"D:\output.jng"
Image.fromarray(array, mode="RGBA").save(output_path)
```