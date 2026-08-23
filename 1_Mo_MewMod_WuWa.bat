@echo off
title MewMod WuWa
cd /d "%~dp0"
if exist "dist\MewModWuWa\MewModWuWa.exe" (
    start "" "dist\MewModWuWa\MewModWuWa.exe"
) else (
    start "" pythonw.exe "MewModWuWa.py"
)

