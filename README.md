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

With:
- ../ThirdParty/Maya_SDKs/2022
- ../ThirdParty/Maya_SDKs/2023
- ...

```
cd ../maya_playblast/plugin
build_all_maya.bat "../ThirdParty/Maya_SDKs" "../maya_playblast/plugin"
```

# Check custom capture commande

```python
from __future__ import annotations

import ctypes
import numpy as np
from PIL import Image

from maya import cmds

from maya_playblast.capture.context import VP2Override
from maya_playblast.maya import maya_ui

view   = maya_ui.get_active_view()
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