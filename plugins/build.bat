@echo off
setlocal EnableExtensions EnableDelayedExpansion

REM ==========================================================
REM  Maya Plugin Build Script
REM ==========================================================

if "%~1"=="" (
    echo.
    echo Usage: build.bat MAYA_VERSION [OUTPUT_DIR] [MAYA_DEVKIT_DIR]
    echo.
    echo Example:
    echo     build.bat 2024
    echo     build.bat 2024 "C:\MyPlugins"
    echo     build.bat 2024 "C:\MyPlugins" "C:\Autodesk\Maya2024\devkit"
    echo.
    exit /b 1
)

set MAYA_VERSION=%~1
set DEVKIT_DIR=%~2
set OUTPUT_DIR=%~3

cd /d "%~dp0"

echo.
echo ==========================================================
echo   Building Maya Plugin
echo ==========================================================
echo   Maya Version  : %MAYA_VERSION%

if not "%OUTPUT_DIR%"=="" (
    echo   Output Dir    : %OUTPUT_DIR%
)

if not "%DEVKIT_DIR%"=="" (
    echo   DevKit Dir    : %DEVKIT_DIR%
)

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
REM ----------------------------------------------------------

echo.
echo Configuring project with CMake...
echo.

if "%OUTPUT_DIR%"=="" (
    cmake . -B build ^
        -DMAYA_VERSION=%MAYA_VERSION% ^
        -G "Visual Studio 17 2022" ^
        -A x64
) else if "%DEVKIT_DIR%"=="" (
    cmake . -B build ^
        -DMAYA_VERSION=%MAYA_VERSION% ^
        -DPLUGIN_OUTPUT_DIR="%OUTPUT_DIR%" ^
        -G "Visual Studio 17 2022" ^
        -A x64
) else (
    cmake . -B build ^
        -DMAYA_VERSION=%MAYA_VERSION% ^
        -DPLUGIN_OUTPUT_DIR="%OUTPUT_DIR%" ^
        -DMAYA_DEVKIT_DIR="%DEVKIT_DIR%" ^
        -G "Visual Studio 17 2022" ^
        -A x64
)

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