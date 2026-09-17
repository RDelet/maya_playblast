@echo off
setlocal EnableExtensions EnableDelayedExpansion

REM ==========================================================================
REM test_playblast.bat
REM Batch / mayapy playblast capture test
REM
REM Usage :
REM   test_playblast.bat [OPTIONS]
REM
REM Options :
REM   --maya-version  <2022|2023|2024|2025|2026>   (default : 2022)
REM   --maya-dir      <C:\Program Files\Autodesk>
REM   --output        <path\output.mp4>
REM   --camera        <camera>
REM   --start         <frame>
REM   --end           <frame>
REM   --width         <px>                          (default : 960)
REM   --height        <px>                          (default : 540)
REM   --ffmpeg        <path\ffmpeg.exe>             (required)
REM ==========================================================================

set "MAYA_VERSION=2022"
set "MAYA_BASE_DIR=C:\Program Files\Autodesk"
set "OUTPUT=D:\Playblast\BatchOutput.mp4"
set "CAMERA=persp"
set "START="
set "END="
set "WIDTH=960"
set "HEIGHT=540"
set "FFMPEG="
set "NO_PAUSE=1"
set "SCRIPT_DIR=%~dp0"

:parse_args
if "%~1"=="" goto :end_parse

if /i "%~1"=="--maya-version"  ( set "MAYA_VERSION=%~2"  & shift & shift & goto :parse_args )
if /i "%~1"=="--maya-dir"      ( set "MAYA_BASE_DIR=%~2" & shift & shift & goto :parse_args )
if /i "%~1"=="--output"        ( set "OUTPUT=%~2"        & shift & shift & goto :parse_args )
if /i "%~1"=="--camera"        ( set "CAMERA=%~2"        & shift & shift & goto :parse_args )
if /i "%~1"=="--start"         ( set "START=%~2"         & shift & shift & goto :parse_args )
if /i "%~1"=="--end"           ( set "END=%~2"           & shift & shift & goto :parse_args )
if /i "%~1"=="--width"         ( set "WIDTH=%~2"         & shift & shift & goto :parse_args )
if /i "%~1"=="--height"        ( set "HEIGHT=%~2"        & shift & shift & goto :parse_args )
if /i "%~1"=="--ffmpeg"        ( set "FFMPEG=%~2"        & shift & shift & goto :parse_args )
if /i "%~1"=="--no-pause"      ( set "NO_PAUSE=1"        & shift         & goto :parse_args )

echo [WARNING] Unknown argument : %~1
shift
goto :parse_args
:end_parse

set "MAYA_DIR=%MAYA_BASE_DIR%\Maya%MAYA_VERSION%"
set "MAYA_BIN=%MAYA_DIR%\bin"
set "MAYA_PY=%MAYA_BIN%\mayapy.exe"
set "PYTHON_SCRIPT=%SCRIPT_DIR%test_playblast.py"

set "PYTHONHOME="
set "PYTHONPATH="
set "PYTHONSTARTUP="
set "PYTHONUSERBASE="
set "PYTHONEXECUTABLE="
set "PATH=%MAYA_BIN%;%SystemRoot%\system32;%SystemRoot%"
set "MAYA_LOCATION=%MAYA_DIR%"
set "MAYA_APP_DIR=%SCRIPT_DIR%maya_test_env"

echo.
echo ==========================================================================
echo   Test playblast capture
echo ==========================================================================
echo   Maya          : !MAYA_VERSION! ^(!MAYA_BIN!^)
echo   Output        : !OUTPUT!
echo   Camera        : !CAMERA!
echo   Resolution    : !WIDTH!x!HEIGHT!
echo   FFmpeg        : !FFMPEG!
if not "!START!"=="" echo   Frames        : !START! ^-^> !END!
echo ==========================================================================
echo.

if not exist "!MAYA_BIN!" (
    echo [ERROR] Maya directory not found : !MAYA_BIN!
    goto :error
)

if not exist "!PYTHON_SCRIPT!" (
    echo [ERROR] Python script not found : !PYTHON_SCRIPT!
    goto :error
)

if not exist "!MAYA_PY!" (
    echo [ERROR] mayapy.exe not found : !MAYA_PY!
    goto :error
)

if "!FFMPEG!"=="" (
    echo [ERROR] --ffmpeg is required.
    goto :error
)

if not exist "!FFMPEG!" (
    echo [ERROR] FFmpeg not found : !FFMPEG!
    goto :error
)

set "START_ARGS="
set "END_ARGS="
if not "!START!"=="" set "START_ARGS=--start !START!"
if not "!END!"=="" set "END_ARGS=--end !END!"

echo [CMD]  "!MAYA_PY!" "!PYTHON_SCRIPT!" --output "!OUTPUT!" --width !WIDTH! --height !HEIGHT! --camera !CAMERA! --ffmpeg "!FFMPEG!" !START_ARGS! !END_ARGS!
echo.

"!MAYA_PY!" "!PYTHON_SCRIPT!" --output "!OUTPUT!" --width !WIDTH! --height !HEIGHT! --camera !CAMERA! --ffmpeg "!FFMPEG!" !START_ARGS! !END_ARGS!

if errorlevel 1 (
    echo.
    echo [ERROR] The test failed ^(code !ERRORLEVEL!^).
    goto :error
)

echo.
echo ==========================================================================
echo [SUCCESS] Test completed.
echo           Output : !OUTPUT!
echo ==========================================================================
if "!NO_PAUSE!"=="0" pause
exit /b 0

:error
echo.
echo ==========================================================================
echo [FAILED] The test failed. See logs above.
echo ==========================================================================
if "!NO_PAUSE!"=="0" pause
exit /b 1
