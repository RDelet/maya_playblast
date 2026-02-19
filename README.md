# maya_playblast

A custom playblast to override the fucking maya playblast

# Dependencies

- Numpy: https://numpy.org/

# How to use it ?

```python
from maya_playblast.maya.viewport import VIEWPORT_FLAGS
import maya_playblast

# If you want to set visibility of elements
joint_flag = VIEWPORT_FLAGS.get("joints")
joint_flag.keep_visible = True

# Record
maya_playblast.record(r"D:\Groot.mp4")
```
