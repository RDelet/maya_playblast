# maya_playblast

A custom playblast to override the fucking maya playblast

# Dependencies

- Numpy: https://numpy.org/

# How to use it ?

```python
import maya_playblast
from maya_playblast.maya.viewport import VIEWPORT_FLAGS

# If you want to set visibility of elements
VIEWPORT_FLAGS["joints"] = True
# Record
maya_playblast.record(r"D:\Groot.mp4")
```
