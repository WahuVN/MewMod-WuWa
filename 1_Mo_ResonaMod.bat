@echo off
title ResonaMod
cd /d "%~dp0"
if exist "dist\ResonaMod\ResonaMod.exe" (
    start "" "dist\ResonaMod\ResonaMod.exe"
) else if exist "ResonaMod.exe" (
    start "" "ResonaMod.exe"
) else (
    start "" pythonw.exe "ResonaMod.py"
)

