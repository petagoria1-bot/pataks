"""
MainWindow — Fenêtre principale PATAKS v2.0
Gère le flow complet :
  1. SplashScreen  — logo animé + loading
  2. DetectionScreen — scan réel composants
  3. Application principale (sidebar + pages)
"""

import logging
from PyQt6.QtWidgets import (
    QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QStackedWidget, QLabel, QPushButton, QApplication,
    QSystemTrayIcon, QMenu, QSizePolicy
)
from PyQt6.QtCore import Qt, QPoint, QTimer, QSize
from PyQt6.QtGui import QPainter, QColor, QFont, QPen, QPainterPath

from ui.theme import Colors, Typography, Spacing, GLOBAL_STYLESHEET
from ui.pages.splash import SplashScreen
from ui.pages.detection import DetectionScreen, SystemConfig
from ui.components.sidebar import Sidebar
from ui.pages.boost import BoostPage
from ui.pages.dashboard import DashboardPage
from ui.pages.analyze import AnalyzePage
from ui.pages.optimize import OptimizePage
from ui.pages.monitor import MonitorPage
from ui.pages.security import SecurityPage
from ui.pages.settings import SettingsPage
from core.system_monitor import SystemMonitor

logger = logging.getLogger(__name__)


# ─── TITLE BAR ────────────────────────────────────────────────────────────────

class TitleBar(QWidget):
    """Barre de titre custom — drag + boutons."""

    def __init__(self, parent_window, parent=None):
        super().__init__(parent)
        self._win = parent_window
        self._drag_pos = None
        self.setFixedHeight(36)
        self._build()

    def _build(self):
        layout = QHBoxLayout(self)
        layout.setContentsMargins(16, 0, 4, 0)
        layout.setSpacing(0)

        # Logo minimaliste
        lbl_logo = QLabel("PATAKS")
        lbl_logo.setFont(Typography.display(13))
        lbl_logo.setStyleSheet(f"color: {Colors.SILVER_BRIGHT}; background: transparent; letter-spacing: 1px;")
        layout.addWidget(lbl_logo)

        sep = QLabel("  ·  ")
        sep.setStyleSheet(f"color: {Colors.SILVER_GHOST}; background: transparent;")
        layout.addWidget(sep)

        lbl_sub = QLabel("by Petagoria")
        lbl_sub.setFont(Typography.label(8))
        lbl_sub.setStyleSheet(f"color: {Colors.CRIMSON}; background: transparent; letter-spacing: 2px;")
        layout.addWidget(lbl_sub)
        layout.addStretch()

        for symbol, tooltip, action, is_close in [
            ("−", "Réduire",      self._win.showMinimized, False),
            ("□", "Agrandir",     self._toggle_maximize,   False),
            ("✕", "Fermer",       self._win.close,         True),
        ]:
            btn = QPushButton(symbol)
            btn.setFixedSize(46, 36)
            btn.setToolTip(tooltip)
            btn.setFont(QFont("Segoe UI Symbol", 10))
            btn.clicked.connect(action)
            btn.setCursor(Qt.CursorShape.PointingHandCursor)
            btn.setStyleSheet(f"""
                QPushButton {{
                    background: transparent;
                    color: {Colors.SILVER_DIM};
                    border: none;
                    font-size: 14px;
                }}
                QPushButton:hover {{
                    background: {'rgba(192,21,15,0.85)' if is_close else Colors.BG_HOVER};
                    color: {'white' if is_close else Colors.SILVER_BRIGHT};
                }}
            """)
            layout.addWidget(btn)

        self.setStyleSheet(f"""
            background: {Colors.BG_SURFACE};
            border-bottom: 1px solid {Colors.SILVER_GHOST};
        """)

    def _toggle_maximize(self):
        if self._win.isMaximized():
            self._win.showNormal()
        else:
            self._win.showMaximized()

    def mousePressEvent(self, e):
        if e.button() == Qt.MouseButton.LeftButton:
            self._drag_pos = e.globalPosition().toPoint()

    def mouseMoveEvent(self, e):
        if self._drag_pos and e.buttons() == Qt.MouseButton.LeftButton:
            if self._win.isMaximized():
                self._win.showNormal()
            self._win.move(self._win.pos() + e.globalPosition().toPoint() - self._drag_pos)
            self._drag_pos = e.globalPosition().toPoint()

    def mouseReleaseEvent(self, e):
        self._drag_pos = None

    def mouseDoubleClickEvent(self, e):
        self._toggle_maximize()


# ─── APP SHELL (sidebar + pages) ─────────────────────────────────────────────

class AppShell(QWidget):
    """Shell principal de l'app avec sidebar + stack de pages."""

    def __init__(self, system_config: SystemConfig = None, parent=None):
        super().__init__(parent)
        self._config = system_config
        self._monitor = SystemMonitor(interval_sec=1.0)
        self._build_ui()
        self._monitor.start()

        self._ui_timer = QTimer(self)
        self._ui_timer.timeout.connect(self._refresh_metrics)
        self._ui_timer.start(1000)

    def _build_ui(self):
        layout = QHBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        # Sidebar
        self._sidebar = Sidebar()
        self._sidebar.page_changed.connect(self._navigate)
        layout.addWidget(self._sidebar)

        # Séparateur
        sep = QWidget()
        sep.setFixedWidth(1)
        sep.setStyleSheet(f"background: {Colors.SILVER_GHOST};")
        layout.addWidget(sep)

        # Stack
        self._stack = QStackedWidget()
        self._stack.setStyleSheet(f"background: {Colors.BG_DEEP};")
        layout.addWidget(self._stack, 1)

        # Pages
        self._page_boost    = BoostPage(self._config)
        self._page_dashboard = DashboardPage()
        self._page_analyze  = AnalyzePage()
        self._page_optimize = OptimizePage()
        self._page_monitor  = MonitorPage()
        self._page_security = SecurityPage()
        self._page_settings = SettingsPage()

        self._pages = {
            "boost":     self._page_boost,
            "analyze":   self._page_analyze,
            "dashboard": self._page_dashboard,
            "optimize":  self._page_optimize,
            "monitor":   self._page_monitor,
            "security":  self._page_security,
            "settings":  self._page_settings,
        }
        for page in self._pages.values():
            self._stack.addWidget(page)

        # Mise à jour config dans boost page
        if self._config:
            self._page_boost.update_config(self._config)

        # Démarrer sur Boost
        self._stack.setCurrentWidget(self._page_boost)
        self._sidebar._select("boost")

    def _navigate(self, key: str):
        if key in self._pages:
            self._stack.setCurrentWidget(self._pages[key])
            if key == "security":
                self._page_security.refresh()

    def _refresh_metrics(self):
        try:
            snap = self._monitor.get_snapshot()
            current = self._stack.currentWidget()
            if current == self._page_dashboard:
                self._page_dashboard.update_metrics(snap)
            elif current == self._page_monitor:
                self._page_monitor.update_metrics(snap)
        except Exception as e:
            import logging
            logging.getLogger(__name__).error(f"Erreur refresh métriques: {e}")

    def _placeholder(self, title: str, subtitle: str) -> QWidget:
        from ui.components.widgets import SectionHeader
        w = QWidget()
        w.setStyleSheet(f"background: {Colors.BG_DEEP};")
        l = QVBoxLayout(w)
        l.setContentsMargins(Spacing.XL, Spacing.XL, Spacing.XL, Spacing.XL)
        l.addWidget(SectionHeader(title, subtitle))
        l.addStretch()
        lbl = QLabel("Cette section arrive dans PATAKS v2.1")
        lbl.setFont(Typography.body(12))
        lbl.setStyleSheet(f"color: {Colors.SILVER_GHOST};")
        lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
        l.addWidget(lbl)
        l.addStretch()
        return w

    def stop(self):
        self._ui_timer.stop()
        self._monitor.stop()


# ─── MAIN WINDOW ──────────────────────────────────────────────────────────────

class MainWindow(QMainWindow):
    """
    Fenêtre principale — contrôle le flow :
    Splash → Detection → App
    """

    def __init__(self):
        super().__init__()
        self._app_shell: AppShell = None
        self._system_config: SystemConfig = None
        self._setup_window()
        self._show_splash()

    def _setup_window(self):
        self.setWindowTitle("PATAKS by Petagoria")
        self.setMinimumSize(1100, 700)
        self.resize(1280, 800)
        self.setWindowFlags(
            Qt.WindowType.FramelessWindowHint |
            Qt.WindowType.Window
        )
        # Centrer
        screen = QApplication.primaryScreen()
        if screen:
            geo = screen.availableGeometry()
            self.move(
                (geo.width() - self.width()) // 2,
                (geo.height() - self.height()) // 2
            )
        self.setStyleSheet(GLOBAL_STYLESHEET + f"QMainWindow {{ background: {Colors.BG_DEEP}; }}")
        self._setup_tray()

    # ── FLOW SPLASH ───────────────────────────────────────────────────────────

    def _show_splash(self):
        """Affiche l'écran splash sans titlebar."""
        self._splash = SplashScreen()
        self._splash.loading_done.connect(self._show_detection)
        self.setCentralWidget(self._splash)
        self._splash.show()

    # ── FLOW DETECTION ────────────────────────────────────────────────────────

    def _show_detection(self):
        """Transition vers l'écran de détection des composants."""
        central = QWidget()
        central.setStyleSheet(f"background: {Colors.BG_DEEP};")
        main_layout = QVBoxLayout(central)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)

        # TitleBar
        title_bar = TitleBar(self)
        main_layout.addWidget(title_bar)

        # Detection screen
        self._detection = DetectionScreen()
        self._detection.detection_complete.connect(self._launch_app)
        main_layout.addWidget(self._detection, 1)

        self.setCentralWidget(central)

    # ── FLOW APP ──────────────────────────────────────────────────────────────

    def _launch_app(self, config: SystemConfig):
        """Lance l'application principale avec la config détectée."""
        self._system_config = config

        central = QWidget()
        central.setStyleSheet(f"background: {Colors.BG_DEEP};")
        main_layout = QVBoxLayout(central)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)

        # TitleBar avec info CPU
        title_bar = TitleBar(self)
        main_layout.addWidget(title_bar)

        # Infobar
        infobar = self._build_infobar(config)
        main_layout.addWidget(infobar)

        # App shell
        self._app_shell = AppShell(config)
        main_layout.addWidget(self._app_shell, 1)

        self.setCentralWidget(central)
        logger.info("Application lancée avec config: " + config.cpu.name)

    def _build_infobar(self, config: SystemConfig) -> QWidget:
        bar = QWidget()
        bar.setFixedHeight(34)
        bar.setStyleSheet(f"""
            background: {Colors.BG_SURFACE};
            border-bottom: 1px solid {Colors.SILVER_GHOST};
        """)
        layout = QHBoxLayout(bar)
        layout.setContentsMargins(16, 0, 16, 0)
        layout.setSpacing(0)

        chips = []
        if config.cpu.detected:
            chips.append(("🖥", config.cpu.name.split("@")[0].strip()[:36]))
        if config.gpu.detected:
            chips.append(("🎮", config.gpu.name[:32]))
        if config.ram.detected:
            chips.append(("💾", config.ram.name[:20]))
        chips.append(("🪟", config.os.name[:28] if config.os.detected else "Windows"))

        for i, (icon, text) in enumerate(chips):
            if i > 0:
                sep = QWidget()
                sep.setFixedSize(1, 16)
                sep.setStyleSheet(f"background: {Colors.SILVER_GHOST}; margin: 0 12px;")
                layout.addWidget(sep)
                layout.addSpacing(12)

            lbl_icon = QLabel(icon)
            lbl_icon.setFont(QFont("Segoe UI Emoji", 9))
            lbl_icon.setStyleSheet("background: transparent; padding-right: 4px;")
            layout.addWidget(lbl_icon)

            lbl = QLabel(text)
            lbl.setFont(Typography.body(9))
            lbl.setStyleSheet(f"color: {Colors.SILVER_DIM}; background: transparent;")
            layout.addWidget(lbl)

        layout.addStretch()

        # Indicateur admin
        lbl_admin = QLabel("● ADMIN")
        lbl_admin.setFont(Typography.label(8))
        lbl_admin.setStyleSheet(f"color: {Colors.SUCCESS}; background: transparent; letter-spacing: 1px; margin-right: 12px;")
        layout.addWidget(lbl_admin)

        # Horloge
        self._clock = QLabel("--:--:--")
        self._clock.setFont(Typography.mono(10))
        self._clock.setStyleSheet(f"color: {Colors.SILVER_DIM}; background: transparent;")
        layout.addWidget(self._clock)
        self._clock_timer = QTimer(self)
        self._clock_timer.timeout.connect(self._tick_clock)
        self._clock_timer.start(1000)
        self._tick_clock()

        return bar

    def _tick_clock(self):
        from datetime import datetime
        if self._clock:
            self._clock.setText(datetime.now().strftime("%H:%M:%S"))

    # ── TRAY & EVENTS ─────────────────────────────────────────────────────────

    def _setup_tray(self):
        self._tray = QSystemTrayIcon(self)
        menu = QMenu()
        menu.addAction("Afficher PATAKS", self._show_from_tray)
        menu.addSeparator()
        menu.addAction("Quitter PATAKS", self._quit_app)
        self._tray.setContextMenu(menu)
        self._tray.activated.connect(self._on_tray_activated)
        self._tray.show()

    def _show_from_tray(self):
        self.showNormal()
        self.raise_()
        self.activateWindow()

    def _on_tray_activated(self, reason):
        if reason == QSystemTrayIcon.ActivationReason.DoubleClick:
            self._show_from_tray()

    def _quit_app(self):
        self._force_quit = True
        self.close()

    def closeEvent(self, event):
        if not getattr(self, "_force_quit", False):
            self.hide()
            if hasattr(self, "_tray"):
                self._tray.showMessage(
                    "PATAKS",
                    "PATAKS tourne en arrière-plan. Double-cliquez sur l'icône pour rouvrir.",
                    QSystemTrayIcon.MessageIcon.Information,
                    2000,
                )
            event.ignore()
            return

        if self._app_shell:
            self._app_shell.stop()
        if hasattr(self, "_tray"):
            self._tray.hide()
        logger.info("PATAKS fermé proprement.")
        event.accept()

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setPen(QPen(QColor(Colors.SILVER_GHOST), 1))
        painter.drawRect(self.rect().adjusted(0, 0, -1, -1))
