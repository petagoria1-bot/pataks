@echo off
chcp 65001 >nul
title PATAKS

REM Aller dans le dossier du script
cd /d "%~dp0"

REM Vérifier si l'exe existe
if exist "dist\PATAKS.exe" (
    start "" "dist\PATAKS.exe"
    exit
)

REM Sinon, lancer en Python direct
echo Lancement en mode developpeur...
python main.py
