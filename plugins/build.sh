#!/bin/bash

if [ -z "$1" ]; then
    echo "Usage : build.sh MAYA_VERSION [DEVKIT_DIR] [OUTPUT_DIR]"
    exit 1
fi

MAYA_VERSION="$1"
DEVKIT_DIR="$2"
OUTPUT_DIR="$3"

# Se place dans le dossier du script
cd "$(dirname "$0")"

mkdir -p build

if [ -z "$DEVKIT_DIR" ]; then
    cmake . -B build -DMAYA_VERSION="$MAYA_VERSION"
elif [ -z "$OUTPUT_DIR" ]; then
    cmake . -B build -DMAYA_VERSION="$MAYA_VERSION" -DMAYA_DEVKIT_DIR="$DEVKIT_DIR"
else
    cmake . -B build -DMAYA_VERSION="$MAYA_VERSION" -DMAYA_DEVKIT_DIR="$DEVKIT_DIR" -DPLUGIN_OUTPUT_DIR="$OUTPUT_DIR"
fi

if [ $? -ne 0 ]; then
    echo "[ERREUR] CMake configure a echoue."
    exit 1
fi

cmake --build build --parallel $(nproc 2>/dev/null || sysctl -n hw.ncpu)
if [ $? -ne 0 ]; then
    echo "[ERREUR] Build a echoue."
    exit 1
fi

echo ""
echo " [OK] Build termine — build/PlayblastReadPixels.so"