@echo off
chcp 65001 >nul
title PATAKS Builder — by Petagoria
color 0C

cls
echo.
echo  ============================================================
echo.
echo   ██████╗  █████╗ ████████╗ █████╗ ██╗  ██╗███████╗
echo   ██╔══██╗██╔══██╗╚══██╔══╝██╔══██╗██║ ██╔╝██╔════╝
echo   ██████╔╝███████║   ██║   ███████║█████╔╝ ███████╗
echo   ██╔═══╝ ██╔══██║   ██║   ██╔══██║██╔═██╗ ╚════██║
echo   ██║     ██║  ██║   ██║   ██║  ██║██║  ██╗███████║
echo   ╚═╝     ╚═╝  ╚═╝   ╚═╝   ╚═╝  ╚═╝╚═╝  ╚═╝╚══════╝
echo.
echo        by Petagoria  ^|  Gaming Optimizer v2.0
echo.
echo  ============================================================
echo.

REM Aller dans le dossier du script
cd /d "%~dp0"

REM ── ÉTAPE 1 : Python ────────────────────────────────────────────
echo  [1/5]  Verification Python 3.12+...
python --version 2>NUL
IF ERRORLEVEL 1 (
    echo.
    echo  [ERREUR] Python non detecte.
    echo.
    echo  Telecharger Python 3.12 : https://www.python.org/downloads/
    echo  IMPORTANT : Cocher "Add Python to PATH" lors de l'installation.
    echo.
    pause & exit /b 1
)
echo         OK

REM ── ÉTAPE 2 : Dépendances ────────────────────────────────────────
echo  [2/5]  Installation des dependances...
echo         (PyQt6, psutil, pywin32, WMI, PyInstaller)
echo.
pip install PyQt6 psutil pywin32 WMI pyinstaller Pillow --quiet --upgrade
IF ERRORLEVEL 1 (
    echo  [ERREUR] Installation echouee. Verifiez votre connexion internet.
    pause & exit /b 1
)
echo         OK — dependances installees

REM ── ÉTAPE 3 : Nettoyage ─────────────────────────────────────────
echo  [3/5]  Nettoyage des anciens builds...
if exist "dist\PATAKS.exe" del /f /q "dist\PATAKS.exe"
if exist "build" rmdir /s /q "build" 2>nul
echo         OK

REM ── ÉTAPE 4 : Compilation PyInstaller ────────────────────────────
echo  [4/5]  Compilation en cours...
echo         (peut prendre 2-5 minutes selon votre machine)
echo.
pyinstaller pataks.spec --noconfirm --clean --log-level WARN
IF ERRORLEVEL 1 (
    echo.
    echo  [ERREUR] Compilation PyInstaller echouee.
    echo  Consultez le fichier : build\PATAKS\warn-PATAKS.txt
    echo.
    pause & exit /b 1
)

REM ── ÉTAPE 5 : Vérification ───────────────────────────────────────
echo  [5/5]  Verification du fichier final...
if not exist "dist\PATAKS.exe" (
    echo  [ERREUR] PATAKS.exe introuvable dans dist\
    pause & exit /b 1
)

REM Taille du fichier
for %%A in ("dist\PATAKS.exe") do set SIZE=%%~zA
set /a SIZE_MB=%SIZE% / 1048576

echo.
echo  ============================================================
echo.
echo   BUILD REUSSI !
echo.
echo   Fichier  : dist\PATAKS.exe
echo   Taille   : %SIZE_MB% MB
echo.
echo   L'executable demande automatiquement les droits Admin
echo   et n'affiche aucune fenetre console.
echo.
echo  ============================================================
echo.

REM Proposer de lancer PATAKS directement
choice /c ON /m "  Lancer PATAKS maintenant ? (O=Oui, N=Non)"
IF ERRORLEVEL 2 goto fin
IF ERRORLEVEL 1 (
    echo  Lancement de PATAKS...
    start "" "dist\PATAKS.exe"
)

:fin
echo.
echo  Terminé. Appuyez sur une touche pour fermer.
pause >nul
