# PlayblastReadPixels

Plugin Maya C++ qui expose une commande `readPixels` retournant le contenu  
du render target VP2.0 directement en mémoire — sans écrire sur le disque.

## Structure

```
plugin/
  cmake/modules/FindMaya.cmake   ← Détection automatique du Maya devkit
  src/
    plugin_main.cpp              ← initializePlugin / uninitializePlugin
    read_pixels_cmd.h
    read_pixels_cmd.cpp          ← Implémentation de la commande
  CMakeLists.txt
  build.bat                      ← Script Windows
  build.sh                       ← Script Linux / macOS
```

## Prérequis

- CMake >= 3.13
- Maya Devkit (téléchargeable sur Autodesk Developer Network)
- Windows : Visual Studio 2019 ou 2022 (selon la version Maya)
- Linux / macOS : GCC / Clang

## Compilation

### Windows
```bat
build.bat 2025
build.bat 2025 "C:\path\to\devkit"
build.bat 2025 "" "C:\Maya\plug-ins"
```

### Linux / macOS
```bash
chmod +x build.sh
./build.sh 2025
./build.sh 2025 /path/to/devkit
./build.sh 2025 "" /path/to/output
```

### Manuellement
```bash
mkdir build && cd build
cmake .. -DMAYA_VERSION=2025 -DMAYA_DEVKIT_DIR=/path/to/devkit
cmake --build . --config Release
```

## Chargement dans Maya

```python
from maya import cmds
cmds.loadPlugin(r"C:\path\to\PlayblastReadPixels.mll")
```

Ou placer le `.mll` dans `Documents/maya/plug-ins/` pour un chargement automatique.

## Utilisation depuis Python

```python
import numpy as np
from maya import cmds

# Capture le viewport actif
raw = cmds.readPixels(width=1920, height=1080)
array = np.array(raw, dtype=np.uint8).reshape((1080, 1920, 4))
# Flip Y — origine OpenGL = bas-gauche
array = np.ascontiguousarray(array[::-1])
```

## Compatibilité Maya

| Maya | Visual Studio | Compilateur |
|------|--------------|-------------|
| 2022 | VS 2019      | MSVC 14.2   |
| 2023 | VS 2019      | MSVC 14.2   |
| 2024 | VS 2022      | MSVC 14.3   |
| 2025 | VS 2022      | MSVC 14.3   |
