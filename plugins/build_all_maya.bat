@echo off
setlocal EnableExtensions EnableDelayedExpansion

REM ==========================================================
REM Maya Plugin Batch Build Script (Debug-safe version)
REM ==========================================================

if "%~1"=="" (
    echo.
    echo Usage: build_all.bat [MAYA_BASE_DIR] [BASE_OUTPUT_DIR]
    exit /b 1
)

set "MAYA_BASE_DIR=%~1"
set "BASE_OUTPUT_DIR=%~2"

echo [DEBUG] Maya base directory: !MAYA_BASE_DIR!
echo [DEBUG] Base output directory: !BASE_OUTPUT_DIR!
echo.

REM Make sure base output directory exists
if not exist "!BASE_OUTPUT_DIR!" mkdir "!BASE_OUTPUT_DIR!"

REM Loop through all folders in the Maya base directory
set "FOUND=0"
for /d %%D in ("%MAYA_BASE_DIR%\*") do (
    set "MAYA_YEAR=%%~nxD"

    REM Check if folder name is 4-digit number
    echo !MAYA_YEAR!| findstr "^[0-9][0-9][0-9][0-9]$" >nul
    if not errorlevel 1 (
        set "FOUND=1"
        set "DEVKIT_PATH=%%D"

        call build.bat !MAYA_YEAR! "!DEVKIT_PATH!" "!BASE_OUTPUT_DIR!"

        if errorlevel 1 (
            echo [ERROR] Build failed for Maya !MAYA_YEAR!
        ) else (
            echo [SUCCESS] Build succeeded for Maya !MAYA_YEAR!
        )
        echo.
    ) else (
        echo [DEBUG] Skipping folder ^(not a year^): %%D
    )

    REM ----------------------------------------------------------
    REM Clean previous build directory
    REM ----------------------------------------------------------
    if exist build (
        echo Cleaning previous build directory...
        rmdir /s /q build
    )

)

if "!FOUND!"=="0" echo [WARNING] No valid Maya year folders found in !MAYA_BASE_DIR!

echo ==========================================================
echo All builds finished.
echo ==========================================================
pause