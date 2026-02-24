#!/usr/bin/env bash

# ==========================================================
#  Maya Plugin Build Script
# ==========================================================

set -e  # Stop on first error

# ----------------------------------------------------------
# Usage
# ----------------------------------------------------------

if [ -z "$1" ]; then
    echo
    echo "Usage: ./build.sh MAYA_VERSION [OUTPUT_DIR] [MAYA_DEVKIT_DIR]"
    echo
    echo "Example:"
    echo "    ./build.sh 2024"
    echo "    ./build.sh 2024 /home/user/plugins"
    echo "    ./build.sh 2024 /home/user/plugins /usr/autodesk/maya2024/devkit"
    echo
    exit 1
fi

MAYA_VERSION="$1"
OUTPUT_DIR="$2"
DEVKIT_DIR="$3"

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

echo
echo "=========================================================="
echo "  Building Maya Plugin"
echo "=========================================================="
echo "  Maya Version : $MAYA_VERSION"

if [ -n "$OUTPUT_DIR" ]; then
    echo "  Output Dir   : $OUTPUT_DIR"
fi

if [ -n "$DEVKIT_DIR" ]; then
    echo "  DevKit Dir   : $DEVKIT_DIR"
fi

echo "=========================================================="
echo

# ----------------------------------------------------------
# Validate DevKit
# ----------------------------------------------------------

if [ -n "$DEVKIT_DIR" ] && [ ! -d "$DEVKIT_DIR" ]; then
    echo "[ERROR] Provided MAYA_DEVKIT_DIR does not exist:"
    echo "        $DEVKIT_DIR"
    exit 1
fi

# ----------------------------------------------------------
# Create build directory
# ----------------------------------------------------------

if [ ! -d "build" ]; then
    echo "Creating build directory..."
    mkdir build
fi

# ----------------------------------------------------------
# Configure with CMake
# ----------------------------------------------------------

echo
echo "Configuring project with CMake..."
echo

CMAKE_ARGS=(-DMAYA_VERSION="$MAYA_VERSION")

if [ -n "$OUTPUT_DIR" ]; then
    CMAKE_ARGS+=(-DPLUGIN_OUTPUT_DIR="$OUTPUT_DIR")
fi

if [ -n "$DEVKIT_DIR" ]; then
    CMAKE_ARGS+=(-DMAYA_DEVKIT_DIR="$DEVKIT_DIR")
fi

cmake -S . -B build "${CMAKE_ARGS[@]}"

echo
echo "Building Release configuration..."
echo

cmake --build build --config Release

# ----------------------------------------------------------
# Success
# ----------------------------------------------------------

echo
echo "=========================================================="
echo "[SUCCESS] Plugin successfully built!"
echo
echo "Output:"
echo "  build/Release/PlayblastReadPixels.so"
echo "=========================================================="
echo