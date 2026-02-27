@echo off
setlocal EnableExtensions EnableDelayedExpansion

REM ==========================================================================
REM test_playblast.bat
REM Test du plugin PlayblastReadPixels en mode batch ou mayapy
REM
REM Usage :
REM   test_playblast.bat [OPTIONS]
REM
REM Options :
REM   --maya-version  <2022|2023|2024|2025|2026>   (defaut : 2024)
REM   --maya-dir      <C:\Program Files\Autodesk>   (defaut : auto)
REM   --output        <chemin\output.mp4>           (defaut : .\output_test.mp4)
REM   --start         <frame>
REM   --end           <frame>
REM   --width         <px>                          (defaut : 960)
REM   --height        <px>                          (defaut : 540)
REM   --no-pause                                    Ne pas attendre a la fin
REM ==========================================================================

REM ── Valeurs par défaut ─────────────────────────────────────────────────────
set "MAYA_VERSION=2022"
set "MAYA_BASE_DIR=C:\Program Files\Autodesk"
set "OUTPUT=D:\Playblast\BatchOutput.mp4"
set "START="
set "END="
set "WIDTH=960"
set "HEIGHT=540"
set "NO_PAUSE=1"
set "SCRIPT_DIR=%~dp0"

REM ── Parsing des arguments ──────────────────────────────────────────────────
:parse_args
if "%~1"=="" goto :end_parse

if /i "%~1"=="--maya-version"  ( set "MAYA_VERSION=%~2"  & shift & shift & goto :parse_args )
if /i "%~1"=="--maya-dir"      ( set "MAYA_BASE_DIR=%~2" & shift & shift & goto :parse_args )
if /i "%~1"=="--output"        ( set "OUTPUT=%~2"        & shift & shift & goto :parse_args )
if /i "%~1"=="--start"         ( set "START=%~2"         & shift & shift & goto :parse_args )
if /i "%~1"=="--end"           ( set "END=%~2"           & shift & shift & goto :parse_args )
if /i "%~1"=="--width"         ( set "WIDTH=%~2"         & shift & shift & goto :parse_args )
if /i "%~1"=="--height"        ( set "HEIGHT=%~2"        & shift & shift & goto :parse_args )
if /i "%~1"=="--no-pause"      ( set "NO_PAUSE=1"        & shift         & goto :parse_args )

echo [WARNING] Argument inconnu : %~1
shift
goto :parse_args
:end_parse

set "PYTHONHOME="
set "PYTHONPATH="
set "PYTHONSTARTUP="
set "PYTHONUSERBASE="
set "PYTHONEXECUTABLE="

set "PATH=%MAYA_BIN%;%SystemRoot%\system32;%SystemRoot%"
set "MAYA_LOCATION=%MAYA_DIR%"
set "MAYA_APP_DIR=%SCRIPT_DIR%maya_test_env"

set "MAYA_DIR=%MAYA_BASE_DIR%\Maya%MAYA_VERSION%"
set "MAYA_BIN=%MAYA_DIR%\bin"
set "MAYA_PY=%MAYA_BIN%\mayapy.exe"
set "MAYA_BATCH=%MAYA_BIN%\mayabatch.exe"
set "PYTHON_SCRIPT=%SCRIPT_DIR%test_playblast.py"
set "PY_SCRIPT_FWD=!PYTHON_SCRIPT:\=/!"

echo.
echo ==========================================================================
echo   Test PlayblastReadPixels
echo ==========================================================================
echo   Mode          : !MODE!
echo   Maya          : !MAYA_VERSION! ^(!MAYA_BIN!^)
echo   Output        : !OUTPUT!
echo   Plugin        : !PLUGIN!
echo   Backend       : !BACKEND!
echo   Resolution    : !WIDTH!x!HEIGHT!
if not "!START!"=="" echo   Frames        : !START! ^-^> !END!
echo ==========================================================================
echo.

if not exist "!MAYA_BIN!" (
    echo [ERROR] Repertoire Maya introuvable : !MAYA_BIN!
    echo         Utilisez --maya-dir ou --maya-version pour corriger le chemin.
    goto :error
)

if not exist "!PYTHON_SCRIPT!" (
    echo [ERROR] Script Python introuvable : !PYTHON_SCRIPT!
    echo         Assurez-vous que test_playblast.py est dans le meme repertoire.
    goto :error
)

if not "!PLUGIN!"=="" (
    if not exist "!PLUGIN!" (
        echo [ERROR] Plugin introuvable : !PLUGIN!
        goto :error
    )
)

if not exist "!MAYA_BATCH!" (
    echo [ERROR] maya.exe introuvable : !MAYA_BATCH!
    goto :error
)

echo [INFO] Lancement via maya -batch...

set "MAYA_APP_DIR=!SCRIPT_DIR!maya_test_env"
set "PY_ARGS=--output "!OUTPUT!" --width !WIDTH! --height !HEIGHT!"
set "PY_CMD=import os; exec(open(os.environ['PY_SCRIPT_FWD']).read())"

if not "!START!"==""  set "PY_ARGS=!PY_ARGS! --start !START!"
if not "!END!"==""    set "PY_ARGS=!PY_ARGS! --end !END!"

echo [CMD]  "!MAYA_PY!" "!PYTHON_SCRIPT!"
echo.


"!MAYA_PY!" "!PYTHON_SCRIPT!"

goto :check_result

:check_result
if errorlevel 1 (
    echo.
    echo [ERROR] Le test a echoue ^(code !ERRORLEVEL!^).
    goto :error
)

echo.
echo ==========================================================================
echo [SUCCESS] Test termine avec succes.
echo           Sortie : !OUTPUT!
echo ==========================================================================
goto :end

:error
echo.
echo ==========================================================================
echo [FAILED] Le test a echoue. Voir les logs ci-dessus.
echo ==========================================================================
if "!NO_PAUSE!"=="0" pause
exit /b 1

:end
if "!NO_PAUSE!"=="0" pause
exit /b 0