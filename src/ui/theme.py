"""
PATAKS Design System
====================
Palette : Noir profond (#0A0A0F) + Crimson (#E02020) + Argent (#C0C8D8)
Typographie : Inter / Rajdhani (gaming)
Glassmorphism : surfaces semi-transparentes avec blur
Animations : 60 FPS, cubic-bezier
"""

from dataclasses import dataclass
from PyQt6.QtGui import QColor, QFont, QPalette, QLinearGradient
from PyQt6.QtCore import Qt


# ─── PALETTE ──────────────────────────────────────────────────────────────────

class Colors:
    # Backgrounds
    BG_DEEP       = "#09090F"   # Noir absolu background principal
    BG_SURFACE    = "#0F0F1A"   # Surface cartes
    BG_ELEVATED   = "#14141F"   # Surface élevée
    BG_GLASS      = "#1A1A2E"   # Glass panels
    BG_HOVER      = "#1E1E30"   # Hover state

    # Accents
    CRIMSON       = "#E02020"   # Rouge gaming primaire
    CRIMSON_DARK  = "#A01515"   # Rouge foncé
    CRIMSON_GLOW  = "#FF3030"   # Rouge brillant (hover/active)
    CRIMSON_DIM   = "#3D0A0A"   # Rouge très atténué (badges)

    # Silver / Argent
    SILVER        = "#C0C8D8"   # Texte principal
    SILVER_DIM    = "#7A8499"   # Texte secondaire
    SILVER_GHOST  = "#3A3F50"   # Séparateurs, bordures
    SILVER_BRIGHT = "#E8EEF8"   # Texte highlight

    # Status
    SUCCESS       = "#20C060"   # Vert succès
    WARNING       = "#F0A020"   # Orange warning
    DANGER        = "#E02020"   # Rouge critique
    INFO          = "#2090E0"   # Bleu info

    # Chart colors
    CHART_CPU     = "#E02020"   # Rouge CPU
    CHART_RAM     = "#2090E0"   # Bleu RAM
    CHART_GPU     = "#20C060"   # Vert GPU
    CHART_TEMP    = "#F0A020"   # Orange température
    CHART_NET     = "#A020E0"   # Violet réseau


# ─── TYPOGRAPHY ───────────────────────────────────────────────────────────────

class Typography:
    # Font families
    DISPLAY  = "Rajdhani"       # Display gaming — fallback: "Segoe UI"
    BODY     = "Inter"          # Corps de texte — fallback: "Segoe UI"
    MONO     = "JetBrains Mono" # Données numériques — fallback: "Consolas"

    # Sizes (pt)
    SIZE_XS  = 9
    SIZE_SM  = 10
    SIZE_MD  = 12
    SIZE_LG  = 14
    SIZE_XL  = 18
    SIZE_2XL = 24
    SIZE_3XL = 32
    SIZE_4XL = 48

    @staticmethod
    def font(family: str = "Inter", size: int = 12,
             weight: QFont.Weight = QFont.Weight.Normal) -> QFont:
        f = QFont(family, size)
        f.setWeight(weight)
        return f

    @staticmethod
    def display(size: int = 24) -> QFont:
        return Typography.font("Rajdhani", size, QFont.Weight.Bold)

    @staticmethod
    def heading(size: int = 14) -> QFont:
        return Typography.font("Inter", size, QFont.Weight.DemiBold)

    @staticmethod
    def body(size: int = 11) -> QFont:
        return Typography.font("Inter", size, QFont.Weight.Normal)

    @staticmethod
    def mono(size: int = 10) -> QFont:
        return Typography.font("JetBrains Mono", size, QFont.Weight.Normal)

    @staticmethod
    def label(size: int = 9) -> QFont:
        f = Typography.font("Inter", size, QFont.Weight.Medium)
        f.setLetterSpacing(QFont.SpacingType.AbsoluteSpacing, 1.5)
        return f


# ─── SPACING ──────────────────────────────────────────────────────────────────

class Spacing:
    XS  = 4
    SM  = 8
    MD  = 12
    LG  = 16
    XL  = 24
    XXL = 32
    XXXL = 48


# ─── BORDER RADIUS ────────────────────────────────────────────────────────────

class Radius:
    SM  = 4
    MD  = 8
    LG  = 12
    XL  = 16
    FULL = 9999


# ─── STYLESHEET GLOBAL ────────────────────────────────────────────────────────

GLOBAL_STYLESHEET = f"""
/* ─── RESET & BASE ─────────────────────────────────────────────────── */
* {{
    font-family: 'Inter', 'Segoe UI', sans-serif;
    color: {Colors.SILVER};
    selection-background-color: {Colors.CRIMSON_DARK};
    selection-color: {Colors.SILVER_BRIGHT};
}}

QMainWindow, QDialog {{
    background-color: {Colors.BG_DEEP};
}}

QWidget {{
    background-color: transparent;
}}

/* ─── SCROLLBARS ────────────────────────────────────────────────────── */
QScrollBar:vertical {{
    background: {Colors.BG_SURFACE};
    width: 6px;
    border-radius: 3px;
    margin: 0;
}}
QScrollBar::handle:vertical {{
    background: {Colors.SILVER_GHOST};
    border-radius: 3px;
    min-height: 20px;
}}
QScrollBar::handle:vertical:hover {{
    background: {Colors.CRIMSON};
}}
QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {{
    height: 0;
}}
QScrollBar:horizontal {{
    background: {Colors.BG_SURFACE};
    height: 6px;
    border-radius: 3px;
}}
QScrollBar::handle:horizontal {{
    background: {Colors.SILVER_GHOST};
    border-radius: 3px;
    min-width: 20px;
}}

/* ─── BOUTONS ───────────────────────────────────────────────────────── */
QPushButton {{
    background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
        stop:0 {Colors.BG_ELEVATED}, stop:1 {Colors.BG_SURFACE});
    color: {Colors.SILVER};
    border: 1px solid {Colors.SILVER_GHOST};
    border-radius: {Radius.MD}px;
    padding: 8px 16px;
    font-size: 11px;
    font-weight: 500;
}}
QPushButton:hover {{
    background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
        stop:0 {Colors.BG_HOVER}, stop:1 {Colors.BG_ELEVATED});
    border-color: {Colors.SILVER_DIM};
    color: {Colors.SILVER_BRIGHT};
}}
QPushButton:pressed {{
    background: {Colors.BG_SURFACE};
    padding-top: 9px;
    padding-bottom: 7px;
}}
QPushButton[variant="primary"] {{
    background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
        stop:0 {Colors.CRIMSON_GLOW}, stop:1 {Colors.CRIMSON});
    color: white;
    border: none;
    font-weight: 600;
}}
QPushButton[variant="primary"]:hover {{
    background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
        stop:0 #FF4444, stop:1 {Colors.CRIMSON_GLOW});
}}
QPushButton[variant="ghost"] {{
    background: transparent;
    border: 1px solid {Colors.SILVER_GHOST};
    color: {Colors.SILVER_DIM};
}}
QPushButton[variant="ghost"]:hover {{
    border-color: {Colors.CRIMSON};
    color: {Colors.CRIMSON};
    background: {Colors.CRIMSON_DIM};
}}

/* ─── LABELS ────────────────────────────────────────────────────────── */
QLabel {{
    background: transparent;
    color: {Colors.SILVER};
}}
QLabel[role="title"] {{
    color: {Colors.SILVER_BRIGHT};
    font-size: 18px;
    font-weight: 700;
}}
QLabel[role="subtitle"] {{
    color: {Colors.SILVER_DIM};
    font-size: 10px;
    letter-spacing: 2px;
    text-transform: uppercase;
}}
QLabel[role="value"] {{
    color: {Colors.SILVER_BRIGHT};
    font-family: 'JetBrains Mono', 'Consolas', monospace;
    font-size: 28px;
    font-weight: 700;
}}
QLabel[role="unit"] {{
    color: {Colors.SILVER_DIM};
    font-size: 11px;
}}
QLabel[status="ok"] {{ color: {Colors.SUCCESS}; }}
QLabel[status="warning"] {{ color: {Colors.WARNING}; }}
QLabel[status="critical"] {{ color: {Colors.DANGER}; }}

/* ─── INPUTS ────────────────────────────────────────────────────────── */
QLineEdit {{
    background: {Colors.BG_SURFACE};
    border: 1px solid {Colors.SILVER_GHOST};
    border-radius: {Radius.SM}px;
    color: {Colors.SILVER};
    padding: 8px 12px;
    font-size: 11px;
}}
QLineEdit:focus {{
    border-color: {Colors.CRIMSON};
    background: {Colors.BG_ELEVATED};
}}

/* ─── PROGRESS BAR ──────────────────────────────────────────────────── */
QProgressBar {{
    background: {Colors.BG_SURFACE};
    border: none;
    border-radius: 3px;
    height: 6px;
    text-align: center;
}}
QProgressBar::chunk {{
    background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
        stop:0 {Colors.CRIMSON_DARK}, stop:1 {Colors.CRIMSON_GLOW});
    border-radius: 3px;
}}
QProgressBar[status="ok"]::chunk {{
    background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
        stop:0 #158040, stop:1 {Colors.SUCCESS});
}}
QProgressBar[status="warning"]::chunk {{
    background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
        stop:0 #A06010, stop:1 {Colors.WARNING});
}}

/* ─── TOOLTIPS ──────────────────────────────────────────────────────── */
QToolTip {{
    background: {Colors.BG_GLASS};
    border: 1px solid {Colors.SILVER_GHOST};
    color: {Colors.SILVER};
    padding: 6px 10px;
    border-radius: {Radius.SM}px;
    font-size: 10px;
}}

/* ─── COMBOBOX ──────────────────────────────────────────────────────── */
QComboBox {{
    background: {Colors.BG_SURFACE};
    border: 1px solid {Colors.SILVER_GHOST};
    border-radius: {Radius.SM}px;
    color: {Colors.SILVER};
    padding: 6px 12px;
    font-size: 11px;
    min-width: 120px;
}}
QComboBox:hover {{ border-color: {Colors.CRIMSON}; }}
QComboBox::drop-down {{
    subcontrol-origin: padding;
    subcontrol-position: top right;
    width: 20px;
    border: none;
}}
QComboBox QAbstractItemView {{
    background: {Colors.BG_ELEVATED};
    border: 1px solid {Colors.SILVER_GHOST};
    selection-background-color: {Colors.CRIMSON_DIM};
    selection-color: {Colors.CRIMSON_GLOW};
}}

/* ─── GROUPBOX ──────────────────────────────────────────────────────── */
QGroupBox {{
    background: {Colors.BG_SURFACE};
    border: 1px solid {Colors.SILVER_GHOST};
    border-radius: {Radius.LG}px;
    margin-top: 12px;
    padding: 16px;
    font-size: 11px;
    font-weight: 600;
    color: {Colors.SILVER_DIM};
}}
QGroupBox::title {{
    subcontrol-origin: margin;
    left: 12px;
    padding: 0 8px;
    letter-spacing: 1.5px;
    text-transform: uppercase;
    font-size: 9px;
}}

/* ─── TABLES ────────────────────────────────────────────────────────── */
QTableWidget {{
    background: {Colors.BG_SURFACE};
    border: 1px solid {Colors.SILVER_GHOST};
    border-radius: {Radius.MD}px;
    gridline-color: {Colors.BG_ELEVATED};
    font-size: 11px;
}}
QTableWidget::item {{
    padding: 8px 12px;
    border: none;
}}
QTableWidget::item:selected {{
    background: {Colors.CRIMSON_DIM};
    color: {Colors.SILVER_BRIGHT};
}}
QHeaderView::section {{
    background: {Colors.BG_ELEVATED};
    color: {Colors.SILVER_DIM};
    border: none;
    border-bottom: 1px solid {Colors.SILVER_GHOST};
    padding: 8px 12px;
    font-size: 9px;
    font-weight: 600;
    letter-spacing: 1.5px;
    text-transform: uppercase;
}}

/* ─── SPLITTER ──────────────────────────────────────────────────────── */
QSplitter::handle {{
    background: {Colors.SILVER_GHOST};
    width: 1px;
}}

/* ─── MENU ──────────────────────────────────────────────────────────── */
QMenu {{
    background: {Colors.BG_ELEVATED};
    border: 1px solid {Colors.SILVER_GHOST};
    border-radius: {Radius.MD}px;
    padding: 4px;
}}
QMenu::item {{
    padding: 8px 20px;
    border-radius: {Radius.SM}px;
    font-size: 11px;
}}
QMenu::item:selected {{
    background: {Colors.CRIMSON_DIM};
    color: {Colors.CRIMSON_GLOW};
}}
QMenu::separator {{
    height: 1px;
    background: {Colors.SILVER_GHOST};
    margin: 4px 8px;
}}

/* ─── MESSAGEBOX ────────────────────────────────────────────────────── */
QMessageBox {{
    background: {Colors.BG_SURFACE};
}}
QMessageBox QLabel {{
    color: {Colors.SILVER};
    font-size: 11px;
}}
"""


def get_status_color(value: float, thresholds: tuple = (70, 85)) -> str:
    """Retourne la couleur selon le seuil (0-100)."""
    if value >= thresholds[1]:
        return Colors.DANGER
    elif value >= thresholds[0]:
        return Colors.WARNING
    return Colors.SUCCESS


def get_temp_color(temp_c: float) -> str:
    """Couleur selon la température."""
    if temp_c >= 85:
        return Colors.DANGER
    elif temp_c >= 70:
        return Colors.WARNING
    return Colors.SUCCESS
