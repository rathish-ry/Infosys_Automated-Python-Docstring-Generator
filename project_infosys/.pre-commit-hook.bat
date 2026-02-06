@echo off
REM Pre-commit hook wrapper for Windows
REM Activates venv and runs docgen

setlocal enabledelayedexpansion

REM Get the venv Python path
set VENV_PYTHON=C:\Users\RATHEESH\Desktop\jupyter\venv\Scripts\python.exe

REM Run docgen for each file argument
for %%F in (%*) do (
    echo.
    echo Checking: %%F
    echo.
    "%VENV_PYTHON%" -m docgen "%%F"
    if !errorlevel! neq 0 (
        exit /b 1
    )
)

exit /b 0
