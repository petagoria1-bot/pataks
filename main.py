"""
PATAKS by Petagoria
===================
Professional Windows Gaming Optimization Suite
Version: 2.0.0
Author: Petagoria Team
"""

import sys
import os
import ctypes
import logging
from pathlib import Path

# Ensure we're running on Windows
if sys.platform != "win32":
    print("PATAKS requires Windows 10/11")
    sys.exit(1)

# Setup paths
BASE_DIR = Path(__file__).parent
sys.path.insert(0, str(BASE_DIR / "src"))

# Configure logging before anything else
LOG_DIR = Path(os.environ.get("APPDATA", ".")) / "Petagoria" / "PATAKS" / "logs"
LOG_DIR.mkdir(parents=True, exist_ok=True)

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    handlers=[
        logging.FileHandler(LOG_DIR / "pataks.log", encoding="utf-8"),
        logging.StreamHandler(sys.stdout),
    ],
)

logger = logging.getLogger("PATAKS")


def check_admin():
    """Check and request administrator privileges."""
    try:
        is_admin = ctypes.windll.shell32.IsUserAnAdmin()
    except Exception:
        is_admin = False

    if not is_admin:
        logger.warning("Not running as administrator. Requesting elevation...")
        try:
            ctypes.windll.shell32.ShellExecuteW(
                None, "runas", sys.executable, " ".join([f'"{arg}"' for arg in sys.argv]), None, 1
            )
        except Exception as e:
            logger.error(f"Failed to elevate privileges: {e}")
        sys.exit(0)

    logger.info("Running with administrator privileges ✓")


def main():
    """Main application entry point."""
    logger.info("=" * 60)
    logger.info("PATAKS by Petagoria - Starting...")
    logger.info("=" * 60)

    # Check for admin rights (required for optimizations)
    check_admin()

    # Import PyQt6 and launch app
    try:
        from PyQt6.QtWidgets import QApplication
        from PyQt6.QtCore import Qt, QCoreApplication
        from PyQt6.QtGui import QIcon, QFont, QFontDatabase

        QCoreApplication.setAttribute(Qt.ApplicationAttribute.AA_EnableHighDpiScaling, True)
        QCoreApplication.setAttribute(Qt.ApplicationAttribute.AA_UseHighDpiPixmaps, True)

        app = QApplication(sys.argv)
        app.setApplicationName("PATAKS")
        app.setApplicationDisplayName("PATAKS by Petagoria")
        app.setApplicationVersion("2.0.0")
        app.setOrganizationName("Petagoria")

        # Import and launch main window
        from ui.main_window import MainWindow

        window = MainWindow()
        window.show()

        logger.info("Application launched successfully")
        sys.exit(app.exec())

    except ImportError as e:
        logger.critical(f"Missing dependency: {e}")
        logger.critical("Run: pip install PyQt6 psutil wmi pywin32")
        sys.exit(1)
    except Exception as e:
        logger.critical(f"Fatal error: {e}", exc_info=True)
        sys.exit(1)


if __name__ == "__main__":
    main()
