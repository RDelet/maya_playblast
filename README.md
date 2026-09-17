# maya_playblast

A custom playblast to override the Maya playblast.

# Dependencies

- Numpy: https://numpy.org/
- FFmpeg: https://www.ffmpeg.org/
- OpenRV: https://github.com/AcademySoftwareFoundation/OpenRV

# Install numpy

Use Maya's Python so the package lands in the correct site-packages:

```
mayapy -m pip install -r requirements.txt
```

# Show UI

```python
from maya_playblast.ui import main
main.PlayblastDialog().show()
```
