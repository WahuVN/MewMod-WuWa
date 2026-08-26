@echo off
title ResonaMod Studio
cd /d "%~dp0"
if exist "dist\ResonaMod\ResonaMod.exe" (
    start "" "dist\ResonaMod\ResonaMod.exe"
) else if exist "dist\MewModWuWa\MewModWuWa.exe" (
    start "" "dist\MewModWuWa\MewModWuWa.exe"
) else (
    start "" pythonw.exe "ResonaMod.py"
)

