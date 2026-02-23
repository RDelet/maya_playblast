@echo off

if "%~1"=="" (
    echo Usage : build.bat MAYA_VERSION [OUTPUT_DIR] [MAYA_DEVKIT_DIR]
    exit /b 1
)

set MAYA_VERSION=%~1
set DEVKIT_DIR=%~2
set OUTPUT_DIR=%~3

cd /d "%~dp0"

if not exist build mkdir build

if "%OUTPUT_DIR%"=="" (
    cmake . -B build -DMAYA_VERSION=%MAYA_VERSION% -G "Visual Studio 17 2022" -A x64
) else if "%DEVKIT_DIR%"=="" (
    cmake . -B build -DMAYA_VERSION=%MAYA_VERSION% -DPLUGIN_OUTPUT_DIR="%OUTPUT_DIR%" -G "Visual Studio 17 2022" -A x64
) else (
    cmake . -B build -DMAYA_VERSION=%MAYA_VERSION% -DPLUGIN_OUTPUT_DIR="%OUTPUT_DIR%" -DMAYA_DEVKIT_DIR="%DEVKIT_DIR%" -G "Visual Studio 17 2022" -A x64
)

if errorlevel 1 (
    echo [ERREUR] CMake configure a echoue.
    exit /b 1
)

cmake --build build --config Release
if errorlevel 1 (
    echo [ERREUR] Build a echoue.
    exit /b 1
)

echo.
echo  [OK] Build termine — build\Release\PlayblastReadPixels.mll