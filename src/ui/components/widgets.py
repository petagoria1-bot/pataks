"""
PATAKS UI Components
====================
Composants réutilisables :
- GlassCard        : Carte glassmorphism
- MetricWidget     : Métrique avec valeur + graphique mini
- CircularGauge    : Jauge circulaire animée
- MiniSparkline    : Graphique mini sparkline
- StatusBadge      : Badge de statut coloré
- AnimatedButton   : Bouton avec animation glow
- SectionHeader    : En-tête de section avec accent crimson
"""

import math
from collections import deque
from typing import Optional

from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel,
    QPushButton, QGraphicsDropShadowEffect, QSizePolicy, QFrame
)
from PyQt6.QtCore import (
    Qt, QTimer, QPropertyAnimation, QEasingCurve,
    pyqtProperty, QRect, QPoint, QSize
)
from PyQt6.QtGui import (
    QPainter, QPen, QBrush, QColor, QLinearGradient,
    QPainterPath, QRadialGradient, QFont, QConicalGradient
)

from ui.theme import Colors, Typography, Spacing, Radius, get_status_color


# ─── GLASS CARD ───────────────────────────────────────────────────────────────

class GlassCard(QWidget):
    """
    Carte glassmorphism avec bordure subtile et fond semi-transparent.
    Effet : fond sombre + bordure top lumineuse.
    """

    def __init__(self, parent=None, glow_color: str = None):
        super().__init__(parent)
        self._glow_color = glow_color
        self._hover = False
        self.setMouseTracking(True)
        self._setup_layout()

    def _setup_layout(self):
        self._layout = QVBoxLayout(self)
        self._layout.setContentsMargins(Spacing.LG, Spacing.LG, Spacing.LG, Spacing.LG)
        self._layout.setSpacing(Spacing.SM)

    def layout(self):
        return self._layout

    def enterEvent(self, event):
        self._hover = True
        self.update()
        super().enterEvent(event)

    def leaveEvent(self, event):
        self._hover = False
        self.update()
        super().leaveEvent(event)

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)

        rect = self.rect().adjusted(1, 1, -1, -1)
        path = QPainterPath()
        path.addRoundedRect(rect.x(), rect.y(), rect.width(), rect.height(),
                            Radius.LG, Radius.LG)

        # Fond glassmorphism
        bg_color = QColor(Colors.BG_GLASS if self._hover else Colors.BG_SURFACE)
        bg_color.setAlpha(220)
        painter.fillPath(path, bg_color)

        # Bordure
        border_color = QColor(Colors.SILVER_GHOST)
        if self._hover:
            border_color = QColor(self._glow_color or Colors.CRIMSON)
            border_color.setAlpha(100)
        painter.setPen(QPen(border_color, 1))
        painter.drawPath(path)

        # Bordure top lumineuse (highlight)
        top_grad = QLinearGradient(0, rect.top(), 0, rect.top() + 2)
        top_color = QColor(Colors.SILVER if not self._hover else
                           (self._glow_color or Colors.CRIMSON))
        top_color.setAlpha(60)
        top_grad.setColorAt(0, top_color)
        top_grad.setColorAt(1, QColor(0, 0, 0, 0))
        painter.fillPath(path, top_grad)


# ─── METRIC WIDGET ────────────────────────────────────────────────────────────

class MetricWidget(GlassCard):
    """
    Widget métrique complet :
    - Label catégorie (ex: "CPU")
    - Valeur numérique large (ex: "67")
    - Unité (ex: "%")
    - Mini sparkline
    - Barre de progression colorée
    """

    def __init__(self, title: str, unit: str = "%",
                 color: str = Colors.CRIMSON,
                 history_len: int = 30,
                 parent=None):
        super().__init__(parent, glow_color=color)
        self.title = title
        self.unit = unit
        self.color = color
        self.history = deque(maxlen=history_len)
        self._value = 0.0
        self._build_ui()

    def _build_ui(self):
        layout = self.layout()

        # Header row
        header = QHBoxLayout()
        self.lbl_title = QLabel(self.title.upper())
        self.lbl_title.setFont(Typography.label(9))
        self.lbl_title.setStyleSheet(f"color: {Colors.SILVER_DIM}; letter-spacing: 2px;")

        self.lbl_status = QLabel("●")
        self.lbl_status.setStyleSheet(f"color: {Colors.SUCCESS}; font-size: 8px;")

        header.addWidget(self.lbl_title)
        header.addStretch()
        header.addWidget(self.lbl_status)
        layout.addLayout(header)

        # Value row
        val_row = QHBoxLayout()
        val_row.setAlignment(Qt.AlignmentFlag.AlignBottom)

        self.lbl_value = QLabel("0")
        self.lbl_value.setFont(Typography.font("JetBrains Mono", 32, QFont.Weight.Bold))
        self.lbl_value.setStyleSheet(f"color: {Colors.SILVER_BRIGHT};")
        self.lbl_value.setAlignment(Qt.AlignmentFlag.AlignBottom | Qt.AlignmentFlag.AlignLeft)

        self.lbl_unit = QLabel(self.unit)
        self.lbl_unit.setFont(Typography.body(11))
        self.lbl_unit.setStyleSheet(f"color: {Colors.SILVER_DIM}; padding-bottom: 4px;")
        self.lbl_unit.setAlignment(Qt.AlignmentFlag.AlignBottom | Qt.AlignmentFlag.AlignLeft)

        val_row.addWidget(self.lbl_value)
        val_row.addWidget(self.lbl_unit)
        val_row.addStretch()
        layout.addLayout(val_row)

        # Sparkline
        self.sparkline = MiniSparkline(color=self.color, height=40)
        layout.addWidget(self.sparkline)

        # Progress bar custom
        self.progress = MiniProgressBar(color=self.color)
        layout.addWidget(self.progress)

        self.setMinimumSize(160, 150)

    def update_value(self, value: float, thresholds: tuple = (70, 85)):
        self._value = value
        self.history.append(value)

        self.lbl_value.setText(f"{value:.0f}")
        self.sparkline.update_data(list(self.history))
        self.progress.set_value(value)

        # Couleur statut
        color = get_status_color(value, thresholds)
        self.lbl_status.setStyleSheet(f"color: {color}; font-size: 8px;")

    def set_subtitle(self, text: str):
        """Sous-titre optionnel (ex: nom CPU)."""
        if not hasattr(self, 'lbl_sub'):
            self.lbl_sub = QLabel(text)
            self.lbl_sub.setFont(Typography.label(8))
            self.lbl_sub.setStyleSheet(f"color: {Colors.SILVER_DIM};")
            self.layout().insertWidget(1, self.lbl_sub)
        self.lbl_sub.setText(text)


# ─── MINI SPARKLINE ───────────────────────────────────────────────────────────

class MiniSparkline(QWidget):
    """Graphique sparkline minimaliste avec gradient fill."""

    def __init__(self, color: str = Colors.CRIMSON, height: int = 40, parent=None):
        super().__init__(parent)
        self.color = QColor(color)
        self.data: list[float] = []
        self.setFixedHeight(height)
        self.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)

    def update_data(self, data: list[float]):
        self.data = data
        self.update()

    def paintEvent(self, event):
        if len(self.data) < 2:
            return

        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)

        w, h = self.width(), self.height()
        mn, mx = min(self.data), max(self.data)
        rng = mx - mn if mx != mn else 1

        # Calculer les points
        n = len(self.data)
        pts = []
        for i, v in enumerate(self.data):
            x = i * w / (n - 1)
            y = h - (v - mn) / rng * (h - 4) - 2
            pts.append(QPoint(int(x), int(y)))

        # Path ligne
        path = QPainterPath()
        path.moveTo(pts[0])
        for pt in pts[1:]:
            path.lineTo(pt)

        # Fill gradient
        fill_path = QPainterPath(path)
        fill_path.lineTo(w, h)
        fill_path.lineTo(0, h)
        fill_path.closeSubpath()

        grad = QLinearGradient(0, 0, 0, h)
        fill_color = QColor(self.color)
        fill_color.setAlpha(40)
        grad.setColorAt(0, fill_color)
        grad.setColorAt(1, QColor(0, 0, 0, 0))
        painter.fillPath(fill_path, grad)

        # Ligne principale
        pen = QPen(self.color, 1.5)
        pen.setCapStyle(Qt.PenCapStyle.RoundCap)
        pen.setJoinStyle(Qt.PenJoinStyle.RoundJoin)
        painter.setPen(pen)
        painter.drawPath(path)

        # Point actuel (dernier)
        if pts:
            last = pts[-1]
            painter.setPen(Qt.PenStyle.NoPen)
            glow = QRadialGradient(last.x(), last.y(), 6)
            dot_color = QColor(self.color)
            glow.setColorAt(0, dot_color)
            dot_color2 = QColor(self.color)
            dot_color2.setAlpha(0)
            glow.setColorAt(1, dot_color2)
            painter.setBrush(glow)
            painter.drawEllipse(last.x() - 5, last.y() - 5, 10, 10)

            painter.setBrush(QColor(self.color))
            painter.drawEllipse(last.x() - 2, last.y() - 2, 4, 4)


# ─── MINI PROGRESS BAR ────────────────────────────────────────────────────────

class MiniProgressBar(QWidget):
    """Barre de progression fine avec gradient et animation."""

    def __init__(self, color: str = Colors.CRIMSON, parent=None):
        super().__init__(parent)
        self.color = QColor(color)
        self._value = 0.0
        self._animated_value = 0.0
        self.setFixedHeight(4)
        self.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)

        # Animation smooth
        self._timer = QTimer(self)
        self._timer.timeout.connect(self._animate)
        self._timer.start(16)  # 60fps

    def set_value(self, value: float):
        self._value = max(0, min(100, value))

    def _animate(self):
        diff = self._value - self._animated_value
        if abs(diff) > 0.1:
            self._animated_value += diff * 0.15
            self.update()

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)

        w, h = self.width(), self.height()
        fill_w = int(w * self._animated_value / 100)

        # Track
        painter.setPen(Qt.PenStyle.NoPen)
        painter.setBrush(QColor(Colors.BG_ELEVATED))
        painter.drawRoundedRect(0, 0, w, h, h//2, h//2)

        if fill_w > 0:
            # Gradient fill
            grad = QLinearGradient(0, 0, fill_w, 0)
            dark = QColor(self.color)
            dark.setAlpha(180)
            grad.setColorAt(0, dark)
            grad.setColorAt(1, self.color)
            painter.setBrush(grad)
            painter.drawRoundedRect(0, 0, fill_w, h, h//2, h//2)


# ─── CIRCULAR GAUGE ───────────────────────────────────────────────────────────

class CircularGauge(QWidget):
    """
    Jauge circulaire animée style gaming.
    Arc de 270° avec valeur centrale et label.
    """

    def __init__(self, title: str = "", color: str = Colors.CRIMSON,
                 size: int = 120, parent=None):
        super().__init__(parent)
        self.title = title
        self.base_color = QColor(color)
        self._value = 0.0
        self._animated = 0.0
        self.setFixedSize(size, size)

        self._anim_timer = QTimer(self)
        self._anim_timer.timeout.connect(self._tick)
        self._anim_timer.start(16)

    def set_value(self, value: float):
        self._value = max(0, min(100, value))

    def _tick(self):
        diff = self._value - self._animated
        if abs(diff) > 0.1:
            self._animated += diff * 0.12
            self.update()

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)

        w, h = self.width(), self.height()
        cx, cy = w // 2, h // 2
        r = min(w, h) // 2 - 10
        pen_w = 6

        # Arc de fond (track)
        track_pen = QPen(QColor(Colors.SILVER_GHOST), pen_w)
        track_pen.setCapStyle(Qt.PenCapStyle.RoundCap)
        painter.setPen(track_pen)
        painter.drawArc(cx - r, cy - r, r * 2, r * 2,
                        225 * 16, -270 * 16)

        # Arc valeur avec gradient
        if self._animated > 0:
            span = int(-270 * self._animated / 100 * 16)
            grad = QConicalGradient(cx, cy, 225)
            dark = QColor(self.base_color)
            dark.setAlpha(150)
            grad.setColorAt(0, dark)
            grad.setColorAt(0.5, self.base_color)
            bright = QColor(self.base_color)
            bright.setRed(min(255, bright.red() + 40))
            grad.setColorAt(1.0, bright)
            val_pen = QPen(QBrush(grad), pen_w)
            val_pen.setCapStyle(Qt.PenCapStyle.RoundCap)
            painter.setPen(val_pen)
            painter.drawArc(cx - r, cy - r, r * 2, r * 2,
                            225 * 16, span)

        # Valeur centrale
        painter.setPen(QPen(QColor(Colors.SILVER_BRIGHT)))
        painter.setFont(Typography.font("JetBrains Mono", max(10, r // 4),
                                        QFont.Weight.Bold))
        painter.drawText(self.rect(), Qt.AlignmentFlag.AlignCenter,
                         f"{self._animated:.0f}")

        # Label
        if self.title:
            painter.setFont(Typography.label(8))
            painter.setPen(QPen(QColor(Colors.SILVER_DIM)))
            label_rect = QRect(0, cy + r // 2, w, 20)
            painter.drawText(label_rect, Qt.AlignmentFlag.AlignCenter, self.title)


# ─── STATUS BADGE ─────────────────────────────────────────────────────────────

class StatusBadge(QLabel):
    """Badge coloré avec indicateur de statut."""

    STATUS_STYLES = {
        "ok":       (Colors.SUCCESS,  "#0A2010"),
        "warning":  (Colors.WARNING,  "#251500"),
        "critical": (Colors.DANGER,   "#200505"),
        "info":     ("#2090E0",        "#050F20"),
    }

    def __init__(self, text: str = "", status: str = "ok", parent=None):
        super().__init__(text, parent)
        self.set_status(status)
        self.setFont(Typography.label(9))
        self.setContentsMargins(8, 3, 8, 3)

    def set_status(self, status: str):
        color, bg = self.STATUS_STYLES.get(status, (Colors.SILVER_DIM, Colors.BG_SURFACE))
        self.setStyleSheet(f"""
            QLabel {{
                color: {color};
                background: {bg};
                border: 1px solid {color}40;
                border-radius: 10px;
                padding: 2px 8px;
                font-size: 9px;
                font-weight: 600;
                letter-spacing: 1px;
            }}
        """)


# ─── SECTION HEADER ───────────────────────────────────────────────────────────

class SectionHeader(QWidget):
    """En-tête de section avec accent crimson."""

    def __init__(self, title: str, subtitle: str = "", parent=None):
        super().__init__(parent)
        layout = QHBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(Spacing.SM)

        # Accent bar
        accent = QFrame()
        accent.setFixedSize(3, 28)
        accent.setStyleSheet(f"""
            background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                stop:0 {Colors.CRIMSON_GLOW}, stop:1 {Colors.CRIMSON_DARK});
            border-radius: 2px;
        """)
        layout.addWidget(accent)

        # Text column
        text_col = QVBoxLayout()
        text_col.setSpacing(1)

        lbl_title = QLabel(title)
        lbl_title.setFont(Typography.heading(14))
        lbl_title.setStyleSheet(f"color: {Colors.SILVER_BRIGHT};")
        text_col.addWidget(lbl_title)

        if subtitle:
            lbl_sub = QLabel(subtitle.upper())
            lbl_sub.setFont(Typography.label(8))
            lbl_sub.setStyleSheet(f"color: {Colors.SILVER_DIM}; letter-spacing: 2px;")
            text_col.addWidget(lbl_sub)

        layout.addLayout(text_col)
        layout.addStretch()


# ─── ANIMATED BUTTON (GLOW) ───────────────────────────────────────────────────

class GlowButton(QPushButton):
    """Bouton avec effet glow animé au hover."""

    def __init__(self, text: str, color: str = Colors.CRIMSON,
                 parent=None):
        super().__init__(text, parent)
        self._color = QColor(color)
        self._glow_alpha = 0
        self._hover = False
        self.setCursor(Qt.CursorShape.PointingHandCursor)
        self.setMinimumHeight(42)

        self._timer = QTimer(self)
        self._timer.timeout.connect(self._animate_glow)
        self._timer.start(16)

        self._setup_shadow()

    def _setup_shadow(self):
        self._shadow = QGraphicsDropShadowEffect(self)
        self._shadow.setBlurRadius(0)
        self._shadow.setColor(self._color)
        self._shadow.setOffset(0, 0)
        self.setGraphicsEffect(self._shadow)

    def _animate_glow(self):
        target = 25 if self._hover else 0
        diff = target - self._glow_alpha
        if abs(diff) > 0.5:
            self._glow_alpha += diff * 0.15
            blur = self._glow_alpha * 0.8
            self._shadow.setBlurRadius(blur)
            self.update()

    def enterEvent(self, event):
        self._hover = True
        super().enterEvent(event)

    def leaveEvent(self, event):
        self._hover = False
        super().leaveEvent(event)

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)

        rect = self.rect().adjusted(1, 1, -1, -1)
        path = QPainterPath()
        path.addRoundedRect(rect.x(), rect.y(), rect.width(), rect.height(),
                            Radius.MD, Radius.MD)

        # Fond gradient
        if self._hover:
            grad = QLinearGradient(0, 0, 0, rect.height())
            c1 = QColor(self._color)
            c1.setRed(min(255, c1.red() + 30))
            c2 = QColor(self._color)
            grad.setColorAt(0, c1)
            grad.setColorAt(1, c2)
            painter.fillPath(path, grad)
        else:
            painter.fillPath(path, self._color)

        # Texte
        painter.setPen(QPen(QColor("white")))
        font = Typography.heading(11)
        font.setLetterSpacing(QFont.SpacingType.AbsoluteSpacing, 1.0)
        painter.setFont(font)
        painter.drawText(rect, Qt.AlignmentFlag.AlignCenter, self.text())
