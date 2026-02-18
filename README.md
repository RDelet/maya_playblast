# maya_playblast
A custom playblast to override the fucking maya playblast
# Dependencies
- Numpy: https://numpy.org/
# How to use it ?
```python
from maya_playblast.ui.editor import VIEWPORT_FLAGS
import maya_playblast as mpb

# If you want to set visibility of elements
joint_flag = VIEWPORT_FLAGS.get("joints")
joint_flag.keep_visible = True
# REcord
mpb.record(r"D:\Groot.mp4")
```
