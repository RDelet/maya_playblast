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
