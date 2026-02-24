#!/bin/bash

# ==========================================================
# Maya Plugin Build Script (Shell version)
# ==========================================================

set -e  # Stop on first error
set -o pipefail

# -------------------------------
# Usage check
# -------------------------------
if [ -z "$1" ]; then
    echo
    echo "Usage: $0 MAYA_VERSION [MAYA_DEVKIT_DIR] [BASE_OUTPUT_DIR]"
    echo
    echo "Example:"
    echo "    $0 2024 \"/path/to/devkit\" \"./maya_playblast/plugins\""
    echo
    exit 1
fi

MAYA_VERSION="$1"
DEVKIT_DIR="$2"
BASE_OUTPUT_DIR="$3"

# -------------------------------
# Determine output directory
# -------------------------------
PLATFORM=$(uname | tr '[:upper:]' '[:lower:]')  # linux, darwin, etc.

# Map Darwin to macos
if [ "$PLATFORM" = "darwin" ]; then
    PLATFORM="macos"
fi

if [ -n "$BASE_OUTPUT_DIR" ]; then
    OUTPUT_DIR="$BASE_OUTPUT_DIR/$PLATFORM/maya$MAYA_VERSION"
else
    OUTPUT_DIR=""
fi

echo
echo "=========================================================="
echo "  Building Maya Plugin"
echo "=========================================================="
echo "  Maya Version    : $MAYA_VERSION"
echo "  DevKit Directory: $DEVKIT_DIR"
echo "  Output Directory: $OUTPUT_DIR"
echo "=========================================================="
echo

# -------------------------------
# Validate DevKit directory
# -------------------------------
if [ -n "$DEVKIT_DIR" ] && [ ! -d "$DEVKIT_DIR" ]; then
    echo "[ERROR] Provided MAYA_DEVKIT_DIR does not exist:"
    echo "        $DEVKIT_DIR"
    exit 1
fi

# -------------------------------
# Clean and create build directory
# -------------------------------
if [ -d build ]; then
    echo "Cleaning previous build directory..."
    rm -rf build
fi
mkdir -p build

# -------------------------------
# Configure with CMake
# -------------------------------
echo
echo "Configuring project with CMake..."
echo

cmake . -B build \
    -DMAYA_VERSION="$MAYA_VERSION" \
    -DPLUGIN_OUTPUT_DIR="$OUTPUT_DIR" \
    -DMAYA_DEVKIT_DIR="$DEVKIT_DIR"

# -------------------------------
# Build
# -------------------------------
echo
echo "Building Release configuration..."
echo

cmake --build build --config Release

# -------------------------------
# Success
# -------------------------------
echo
echo "=========================================================="
echo "[SUCCESS] Plugin successfully built!"
echo
echo "Output:"
echo "  build/Release/PlayblastReadPixels.mll"
echo "=========================================================="
echo