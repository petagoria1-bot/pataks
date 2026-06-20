"""
Sidebar — Navigation principale PATAKS.
Design : fond noir profond, accent crimson sur sélection, icônes SVG.
"""

from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QPushButton,
    QLabel, QFrame, QSizePolicy
)
from PyQt6.QtCore import Qt, pyqtSignal, QPropertyAnimation, QEasingCurve, QRect
from PyQt6.QtGui import QPainter, QColor, QPainterPath, QPen, QLinearGradient, QFont

from ui.theme import Colors, Typography, Spacing, Radius


# Icônes SVG en unicode / emoji minimalistes (remplacer par SVG réels en prod)
NAV_ITEMS = [
    ("boost",      "⚡",  "Booster mon PC",  "Gaming Mode 1-clic"),
    ("analyze",    "◈",  "Analyse IA",      "Diagnostic système"),
    ("dashboard",  "⬡",  "Dashboard",       "Métriques live"),
    ("monitor",    "◉",  "Moniteur",        "Temps réel"),
    ("security",   "◫",  "Sécurité",        "Backups & logs"),
    ("settings",   "⚙",  "Paramètres",      "Configuration"),
]


class NavButton(QPushButton):
    """Bouton de navigation avec animation de sélection."""

    def __init__(self, key: str, icon: str, label: str, sublabel: str, parent=None):
        super().__init__(parent)
        self.key = key
        self._selected = False
        self._hover_anim = 0.0
        self.setCursor(Qt.CursorShape.PointingHandCursor)
        self.setFixedHeight(56)
        self.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)
        self.setFlat(True)

        # Layout interne
        layout = QHBoxLayout(self)
        layout.setContentsMargins(16, 0, 16, 0)
        layout.setSpacing(12)

        # Icône
        self.lbl_icon = QLabel(icon)
        self.lbl_icon.setFixedWidth(24)
        self.lbl_icon.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.lbl_icon.setFont(QFont("Segoe UI Symbol", 14))
        layout.addWidget(self.lbl_icon)

        # Texte
        text_col = QVBoxLayout()
        text_col.setSpacing(0)

        self.lbl_label = QLabel(label)
        self.lbl_label.setFont(Typography.heading(11))
        text_col.addWidget(self.lbl_label)

        self.lbl_sub = QLabel(sublabel)
        self.lbl_sub.setFont(Typography.label(8))
        text_col.addWidget(self.lbl_sub)

        layout.addLayout(text_col)
        layout.addStretch()

        self._update_style()

    def set_selected(self, selected: bool):
        self._selected = selected
        self._update_style()
        self.update()

    def _update_style(self):
        if self._selected:
            self.lbl_label.setStyleSheet(f"color: {Colors.SILVER_BRIGHT}; background: transparent;")
            self.lbl_sub.setStyleSheet(f"color: {Colors.CRIMSON}; background: transparent;")
            self.lbl_icon.setStyleSheet(f"color: {Colors.CRIMSON}; background: transparent;")
        else:
            self.lbl_label.setStyleSheet(f"color: {Colors.SILVER_DIM}; background: transparent;")
            self.lbl_sub.setStyleSheet(f"color: {Colors.SILVER_GHOST}; background: transparent;")
            self.lbl_icon.setStyleSheet(f"color: {Colors.SILVER_GHOST}; background: transparent;")

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)

        rect = self.rect()

        if self._selected:
            # Fond sélectionné
            bg = QColor(Colors.CRIMSON_DIM)
            path = QPainterPath()
            path.addRoundedRect(8, 4, rect.width() - 16, rect.height() - 8, 8, 8)
            painter.fillPath(path, bg)

            # Accent bar gauche
            accent = QLinearGradient(0, 0, 0, rect.height())
            accent.setColorAt(0, QColor(Colors.CRIMSON_GLOW))
            accent.setColorAt(1, QColor(Colors.CRIMSON_DARK))
            painter.setBrush(accent)
            painter.setPen(Qt.PenStyle.NoPen)
            painter.drawRoundedRect(8, 8, 3, rect.height() - 16, 2, 2)

        # Dessiner le contenu QWidget
        super().paintEvent(event)


class Sidebar(QWidget):
    """
    Barre latérale de navigation PATAKS.
    Émet page_changed(key) quand l'utilisateur change de page.
    """

    page_changed = pyqtSignal(str)

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setFixedWidth(220)
        self._nav_buttons: dict[str, NavButton] = {}
        self._current = "dashboard"
        self._build_ui()

    def _build_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        # ── Logo / Header ────────────────────────────────────────────
        header = QWidget()
        header.setFixedHeight(80)
        header.setStyleSheet(f"""
            background: qlineargradient(x1:0, y1:0, x2:1, y2:1,
                stop:0 {Colors.BG_SURFACE}, stop:1 {Colors.BG_GLASS});
            border-bottom: 1px solid {Colors.SILVER_GHOST};
        """)
        header_layout = QVBoxLayout(header)
        header_layout.setContentsMargins(20, 16, 16, 16)
        header_layout.setSpacing(2)

        lbl_brand = QLabel("PATAKS")
        lbl_brand.setFont(Typography.display(22))
        lbl_brand.setStyleSheet(f"color: {Colors.SILVER_BRIGHT}; background: transparent;")

        lbl_sub = QLabel("by PETAGORIA")
        lbl_sub.setFont(Typography.label(8))
        lbl_sub.setStyleSheet(f"color: {Colors.CRIMSON}; background: transparent; letter-spacing: 3px;")

        header_layout.addWidget(lbl_brand)
        header_layout.addWidget(lbl_sub)
        layout.addWidget(header)

        # ── Navigation Items ─────────────────────────────────────────
        nav_container = QWidget()
        nav_container.setStyleSheet(f"background: {Colors.BG_DEEP};")
        nav_layout = QVBoxLayout(nav_container)
        nav_layout.setContentsMargins(0, 8, 0, 8)
        nav_layout.setSpacing(2)

        for key, icon, label, sublabel in NAV_ITEMS:
            btn = NavButton(key, icon, label, sublabel)
            btn.clicked.connect(lambda checked, k=key: self._on_nav(k))
            self._nav_buttons[key] = btn
            nav_layout.addWidget(btn)

        nav_layout.addStretch()
        layout.addWidget(nav_container, 1)

        # ── Footer ───────────────────────────────────────────────────
        footer = QWidget()
        footer.setFixedHeight(60)
        footer.setStyleSheet(f"""
            background: {Colors.BG_SURFACE};
            border-top: 1px solid {Colors.SILVER_GHOST};
        """)
        footer_layout = QHBoxLayout(footer)
        footer_layout.setContentsMargins(16, 0, 16, 0)

        # Indicateur version
        lbl_version = QLabel("v2.0.0")
        lbl_version.setFont(Typography.label(8))
        lbl_version.setStyleSheet(f"color: {Colors.SILVER_GHOST}; background: transparent;")

        # Status dot (online)
        dot = QLabel("● ACTIF")
        dot.setFont(Typography.label(8))
        dot.setStyleSheet(f"color: {Colors.SUCCESS}; background: transparent; letter-spacing: 1px;")

        footer_layout.addWidget(lbl_version)
        footer_layout.addStretch()
        footer_layout.addWidget(dot)
        layout.addWidget(footer)

        # Sélection initiale
        self._select("dashboard")

        # Style global sidebar
        self.setStyleSheet(f"background: {Colors.BG_DEEP};")

    def _on_nav(self, key: str):
        self._select(key)
        self.page_changed.emit(key)

    def _select(self, key: str):
        if self._current in self._nav_buttons:
            self._nav_buttons[self._current].set_selected(False)
        self._current = key
        if key in self._nav_buttons:
            self._nav_buttons[key].set_selected(True)

    def get_current(self) -> str:
        return self._current

    def paintEvent(self, event):
        """Ombre droite de la sidebar."""
        painter = QPainter(self)
        grad = QLinearGradient(self.width() - 8, 0, self.width(), 0)
        grad.setColorAt(0, QColor(0, 0, 0, 0))
        grad.setColorAt(1, QColor(0, 0, 0, 40))
        painter.fillRect(self.width() - 8, 0, 8, self.height(), grad)
        super().paintEvent(event)
