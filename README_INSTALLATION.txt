=====================================================
   PATAKS by Petagoria — Guide d'installation
=====================================================

OPTION A — Compiler un vrai .exe (RECOMMANDÉ)
------------------------------------------------
1. Extraire ce dossier sur votre Bureau (Desktop)
2. Double-clic sur  BUILD_PATAKS.bat
3. Attendre 2-5 minutes (compilation PyInstaller)
4. L'exe se trouve dans  dist\PATAKS.exe
5. Créer un raccourci sur le Bureau

→ Résultat : PATAKS.exe avec icône, UAC admin,
  ZÉRO fenêtre console, comme une vraie application.


OPTION B — Lancer en mode développeur (rapide)
------------------------------------------------
1. Installer Python 3.12 : https://python.org/downloads
   ⚠ Cocher "Add Python to PATH"
2. Ouvrir CMD en ADMINISTRATEUR dans ce dossier
3. Taper :
   pip install PyQt6 psutil pywin32 WMI
4. Taper :
   python main.py


PRÉREQUIS
----------
- Windows 10 version 2004+ ou Windows 11
- Python 3.12+ (pour compilation ou mode dev)
- Droits Administrateur (requis pour les optimisations)
- OpenHardwareMonitor (optionnel, pour températures GPU)


SUPPORT
--------
Petagoria — contact@petagoria.com

=====================================================
