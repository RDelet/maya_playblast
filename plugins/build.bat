@echo off
setlocal EnableExtensions

REM ==========================================================
REM Maya Plugin Build Script (Fixed for paths with spaces)
REM ==========================================================

if "%~1"=="" (
    echo.
    echo Usage: build.bat MAYA_VERSION [MAYA_DEVKIT_DIR] [BASE_OUTPUT_DIR]
    echo.
    echo Example:
    echo     build.bat 2024 "DekKit Directory" ".\maya_playblast\plugins"
    echo.
    exit /b 1
)

set "MAYA_VERSION=%~1"
set "DEVKIT_DIR=%~2"
set "BASE_OUTPUT_DIR=%~3"

REM ----------------------------------------------------------
REM If a base output directory is provided, append win\maya{Year}
REM ----------------------------------------------------------
if not "%BASE_OUTPUT_DIR%"=="" (
    set "OUTPUT_DIR=%BASE_OUTPUT_DIR%\windows\maya%MAYA_VERSION%"
) else (
    set "OUTPUT_DIR="
)

echo.
echo ==========================================================
echo   Building Maya Plugin
echo ==========================================================
echo   Maya Version    : %MAYA_VERSION%
echo   DevKit Directory: %DEVKIT_DIR%
echo   Output Directory: %OUTPUT_DIR%
echo ==========================================================
echo.

REM ----------------------------------------------------------
REM Validate DevKit directory if provided
REM ----------------------------------------------------------
if not "%DEVKIT_DIR%"=="" (
    if not exist "%DEVKIT_DIR%" (
        echo [ERROR] Provided MAYA_DEVKIT_DIR does not exist:
        echo         %DEVKIT_DIR%
        exit /b 1
    )
)

REM ----------------------------------------------------------
REM Create build directory
REM ----------------------------------------------------------
if not exist build (
    echo Creating build directory...
    mkdir build
)

REM ----------------------------------------------------------
REM Configure with CMake
REM Use quotes around paths to handle spaces
REM ----------------------------------------------------------
echo.
echo Configuring project with CMake...
echo.

cmake . -B build ^
    -DMAYA_VERSION="%MAYA_VERSION%" ^
    -DPLUGIN_OUTPUT_DIR="%OUTPUT_DIR%" ^
    -DMAYA_DEVKIT_DIR="%DEVKIT_DIR%" ^
    -G "Visual Studio 17 2022" ^
    -A x64

if errorlevel 1 (
    echo.
    echo [ERROR] CMake configuration failed.
    exit /b 1
)

REM ----------------------------------------------------------
REM Build
REM ----------------------------------------------------------
echo.
echo Building Release configuration...
echo.

cmake --build build --config Release

if errorlevel 1 (
    echo.
    echo [ERROR] Build failed.
    exit /b 1
)

REM ----------------------------------------------------------
REM Success
REM ----------------------------------------------------------
echo.
echo ==========================================================
echo [SUCCESS] Plugin successfully built!
echo.
echo Output:
echo   build\Release\PlayblastReadPixels.mll
echo ==========================================================
echo.

exit /b 0