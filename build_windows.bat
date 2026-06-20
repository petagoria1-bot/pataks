@echo off
REM =========================================================
REM  PATAKS by Petagoria — Script d'installation et de build
REM =========================================================
SETLOCAL ENABLEDELAYEDEXPANSION

echo.
echo  ██████╗  █████╗ ████████╗ █████╗ ██╗  ██╗███████╗
echo  ██╔══██╗██╔══██╗╚══██╔══╝██╔══██╗██║ ██╔╝██╔════╝
echo  ██████╔╝███████║   ██║   ███████║█████╔╝ ███████╗
echo  ██╔═══╝ ██╔══██║   ██║   ██╔══██║██╔═██╗ ╚════██║
echo  ██║     ██║  ██║   ██║   ██║  ██║██║  ██╗███████║
echo  ╚═╝     ╚═╝  ╚═╝   ╚═╝   ╚═╝  ╚═╝╚═╝  ╚═╝╚══════╝
echo                              by Petagoria
echo.
echo  [1/4] Vérification Python...
python --version 2>NUL
IF ERRORLEVEL 1 (
    echo  ERREUR: Python non trouvé. Installez Python 3.12+
    pause
    exit /b 1
)

echo  [2/4] Installation des dépendances...
pip install -r requirements.txt --quiet
IF ERRORLEVEL 1 (
    echo  ERREUR: Installation des dépendances échouée
    pause
    exit /b 1
)
echo  Dépendances installées OK

echo  [3/4] Build PyInstaller...
pyinstaller pataks.spec --noconfirm --clean
IF ERRORLEVEL 1 (
    echo  ERREUR: Build PyInstaller échoué
    pause
    exit /b 1
)

echo  [4/4] Build terminé !
echo.
echo  Exécutable : dist\PATAKS.exe
echo.
echo  Lancez PATAKS.exe en tant qu'administrateur.
echo.
pause
