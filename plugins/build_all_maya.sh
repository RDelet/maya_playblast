#!/bin/bash

# ==========================================================
# Maya Plugin Batch Build Script (Shell version)
# ==========================================================

set -e
set -o pipefail

# -------------------------------
# Usage check
# -------------------------------
if [ -z "$1" ]; then
    echo
    echo "Usage: $0 [MAYA_BASE_DIR] [BASE_OUTPUT_DIR]"
    exit 1
fi

MAYA_BASE_DIR="$1"
BASE_OUTPUT_DIR="$2"

echo "[DEBUG] Maya base directory: $MAYA_BASE_DIR"
echo "[DEBUG] Base output directory: $BASE_OUTPUT_DIR"
echo

# Ensure base output directory exists
mkdir -p "$BASE_OUTPUT_DIR"

FOUND=0

# Loop through all folders in the Maya base directory
for DEVKIT_PATH in "$MAYA_BASE_DIR"/*; do
    if [ -d "$DEVKIT_PATH" ]; then
        MAYA_YEAR=$(basename "$DEVKIT_PATH")

        # Check if folder name is a 4-digit number
        if [[ "$MAYA_YEAR" =~ ^[0-9]{4}$ ]]; then
            FOUND=1
            echo
            echo "=========================================================="
            echo "Building for Maya $MAYA_YEAR using devkit: $DEVKIT_PATH"
            echo "=========================================================="
            echo

            # Call build.sh for this Maya version
            if ./build.sh "$MAYA_YEAR" "$DEVKIT_PATH" "$BASE_OUTPUT_DIR"; then
                echo "[SUCCESS] Build succeeded for Maya $MAYA_YEAR"
            else
                echo "[ERROR] Build failed for Maya $MAYA_YEAR"
            fi

            # Clean build directory to avoid conflicts for next build
            if [ -d build ]; then
                echo "Cleaning previous build directory..."
                rm -rf build
            fi

        else
            echo "[DEBUG] Skipping folder (not a year): $DEVKIT_PATH"
        fi
    fi
done

if [ "$FOUND" -eq 0 ]; then
    echo "[WARNING] No valid Maya year folders found in $MAYA_BASE_DIR"
fi

echo "=========================================================="
echo "All builds finished."
echo "=========================================================="