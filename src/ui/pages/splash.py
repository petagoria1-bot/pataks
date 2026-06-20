"""
SplashScreen — Écran de démarrage PATAKS.
Fenêtre frameless avec logo animé, anneau rotatif, barre de progression.
"""

import math
from PyQt6.QtWidgets import QWidget, QVBoxLayout, QLabel, QApplication
from PyQt6.QtCore import (
    Qt, QTimer, QThread, pyqtSignal, QPointF, QRectF, QSize
)
from PyQt6.QtGui import (
    QPainter, QColor, QPen, QBrush, QFont,
    QLinearGradient, QConicalGradient, QRadialGradient,
    QPainterPath
)

from ui.theme import Colors, Typography


LOAD_STEPS = [
    (8,  "Initialisation du moteur PATAKS..."),
    (20, "Chargement des modules système..."),
    (35, "Initialisation des drivers WMI..."),
    (50, "Vérification des permissions administrateur..."),
    (65, "Chargement du moteur d'analyse IA..."),
    (78, "Préparation de l'interface gaming..."),
    (90, "Vérification de l'intégrité système..."),
    (100,"Prêt."),
]


class SplashScreen(QWidget):
    """
    Écran splash plein écran centré.
    Émet loading_done quand la barre atteint 100%.
    """

    loading_done = pyqtSignal()

    def __init__(self):
        super().__init__()
        self._progress = 0.0
        self._anim_progress = 0.0
        self._step_idx = 0
        self._label_text = "Initialisation..."
        self._angle = 0.0          # rotation anneau scanner
        self._pulse = 0.0          # pulsation logo
        self._particles: list[dict] = []

        self._setup_window()
        self._init_particles()
        self._start_timers()

    def _setup_window(self):
        self.setWindowFlags(
            Qt.WindowType.FramelessWindowHint |
            Qt.WindowType.WindowStaysOnTopHint |
            Qt.WindowType.SplashScreen
        )
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground, False)
        self.setFixedSize(1280, 800)

        # Centrer
        screen = QApplication.primaryScreen()
        if screen:
            geo = screen.availableGeometry()
            self.move(
                (geo.width() - self.width()) // 2,
                (geo.height() - self.height()) // 2
            )

    def _init_particles(self):
        """Génère des particules montantes."""
        import random
        for _ in range(30):
            self._particles.append({
                "x": random.uniform(0.05, 0.95),
                "y": random.uniform(0.6, 1.0),
                "speed": random.uniform(0.0003, 0.0008),
                "size": random.uniform(1, 2.5),
                "alpha": 0.0,
                "dx": random.uniform(-0.002, 0.002),
            })

    def _start_timers(self):
        # Timer animation (60fps)
        self._anim_timer = QTimer(self)
        self._anim_timer.timeout.connect(self._tick_anim)
        self._anim_timer.start(16)

        # Timer progression loading
        self._load_timer = QTimer(self)
        self._load_timer.timeout.connect(self._tick_load)
        self._load_timer.start(350)

    def _tick_anim(self):
        """Mise à jour animation 60fps."""
        self._angle = (self._angle + 1.5) % 360
        self._pulse = (self._pulse + 0.02) % (2 * math.pi)

        # Smooth progress
        diff = self._progress - self._anim_progress
        if abs(diff) > 0.01:
            self._anim_progress += diff * 0.12

        # Particules
        for p in self._particles:
            p["y"] -= p["speed"]
            p["x"] += p["dx"]
            if p["y"] < 0.0:
                import random
                p["y"] = random.uniform(0.85, 1.0)
                p["x"] = random.uniform(0.05, 0.95)
                p["alpha"] = 0.0
            elif p["y"] < 0.2:
                p["alpha"] = max(0, p["alpha"] - 0.03)
            else:
                p["alpha"] = min(0.7, p["alpha"] + 0.02)

        self.update()

    def _tick_load(self):
        """Avance la barre de chargement étape par étape."""
        if self._step_idx >= len(LOAD_STEPS):
            self._load_timer.stop()
            QTimer.singleShot(500, self.loading_done.emit)
            return

        pct, label = LOAD_STEPS[self._step_idx]
        self._progress = pct
        self._label_text = label
        self._step_idx += 1

    # ── PAINT ────────────────────────────────────────────────────

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        painter.setRenderHint(QPainter.RenderHint.TextAntialiasing)

        W, H = self.width(), self.height()
        cx, cy = W // 2, H // 2

        # ── Fond ──────────────────────────────────────────────
        painter.fillRect(0, 0, W, H, QColor("#07070E"))

        # Radial glow background
        grad_bg = QRadialGradient(cx, cy - 80, 350)
        grad_bg.setColorAt(0, QColor(80, 0, 0, 30))
        grad_bg.setColorAt(1, QColor(0, 0, 0, 0))
        painter.fillRect(0, 0, W, H, QBrush(grad_bg))

        # Grille hexagonale (lignes fines)
        self._draw_hex_grid(painter, W, H)

        # ── Particules ────────────────────────────────────────
        for p in self._particles:
            x = int(p["x"] * W)
            y = int(p["y"] * H)
            alpha = int(p["alpha"] * 200)
            if alpha > 5:
                color = QColor(224, 32, 32, alpha)
                painter.setPen(Qt.PenStyle.NoPen)
                painter.setBrush(color)
                r = p["size"]
                painter.drawEllipse(QRectF(x - r, y - r, r * 2, r * 2))

        # ── Anneaux pulsants ──────────────────────────────────
        pulse_factor = 0.5 + 0.5 * math.sin(self._pulse)
        for i, (radius, base_alpha) in enumerate([(180, 40), (210, 25), (240, 12)]):
            alpha = int(base_alpha * (0.6 + 0.4 * math.sin(self._pulse + i * 0.8)))
            color = QColor(224, 32, 32, alpha)
            pen = QPen(color, 1)
            painter.setPen(pen)
            painter.setBrush(Qt.BrushStyle.NoBrush)
            painter.drawEllipse(QRectF(cx - radius, cy - 110 - radius,
                                       radius * 2, radius * 2))

        # ── Anneau scanner rotatif ────────────────────────────
        self._draw_scanner_ring(painter, cx, cy - 110, 160)

        # ── Cercle intérieur fond ─────────────────────────────
        inner_r = 140
        inner_grad = QRadialGradient(cx, cy - 110, inner_r)
        inner_grad.setColorAt(0, QColor(30, 0, 0, 60))
        inner_grad.setColorAt(0.7, QColor(10, 0, 0, 30))
        inner_grad.setColorAt(1, QColor(0, 0, 0, 0))
        painter.setPen(Qt.PenStyle.NoPen)
        painter.setBrush(QBrush(inner_grad))
        painter.drawEllipse(QRectF(cx - inner_r, cy - 110 - inner_r,
                                   inner_r * 2, inner_r * 2))

        # Bordure cercle intérieur
        border_alpha = 60 + int(30 * pulse_factor)
        painter.setPen(QPen(QColor(224, 32, 32, border_alpha), 1.5))
        painter.setBrush(Qt.BrushStyle.NoBrush)
        r2 = 138
        painter.drawEllipse(QRectF(cx - r2, cy - 110 - r2, r2 * 2, r2 * 2))

        # ── Logo PATAKS ───────────────────────────────────────
        glow_alpha = int(80 + 60 * pulse_factor)
        glow = QRadialGradient(cx, cy - 110, 80)
        glow.setColorAt(0, QColor(224, 32, 32, glow_alpha))
        glow.setColorAt(1, QColor(0, 0, 0, 0))
        painter.setPen(Qt.PenStyle.NoPen)
        painter.setBrush(QBrush(glow))
        painter.drawEllipse(QRectF(cx - 80, cy - 190, 160, 160))

        font_logo = QFont("Rajdhani", 56, QFont.Weight.Bold)
        painter.setFont(font_logo)
        # Shadow
        painter.setPen(QColor(0, 0, 0, 120))
        painter.drawText(QRectF(2, 2, W, H - 280), Qt.AlignmentFlag.AlignCenter, "PATAKS")
        # Main text
        painter.setPen(QColor(Colors.SILVER_BRIGHT))
        painter.drawText(QRectF(0, 0, W, H - 280), Qt.AlignmentFlag.AlignCenter, "PATAKS")

        # Sous-titre "by Petagoria"
        font_sub = QFont("Inter", 10, QFont.Weight.Medium)
        font_sub.setLetterSpacing(QFont.SpacingType.AbsoluteSpacing, 4)
        painter.setFont(font_sub)
        painter.setPen(QColor(Colors.CRIMSON))
        painter.drawText(QRectF(0, 0, W, H - 210), Qt.AlignmentFlag.AlignCenter, "by Petagoria")

        # ── Barre de progression ──────────────────────────────
        bar_w, bar_h = 320, 2
        bar_x = cx - bar_w // 2
        bar_y = cy + 120

        # Label
        font_label = QFont("Inter", 9)
        font_label.setLetterSpacing(QFont.SpacingType.AbsoluteSpacing, 1.5)
        painter.setFont(font_label)
        painter.setPen(QColor(Colors.SILVER_DIM))
        painter.drawText(QRectF(bar_x, bar_y - 20, bar_w, 16),
                         Qt.AlignmentFlag.AlignCenter, self._label_text)

        # Track
        painter.setPen(Qt.PenStyle.NoPen)
        painter.setBrush(QColor(Colors.SILVER_GHOST))
        painter.drawRoundedRect(QRectF(bar_x, bar_y, bar_w, bar_h), 1, 1)

        # Fill
        fill_w = max(0, int(bar_w * self._anim_progress / 100))
        if fill_w > 2:
            grad_bar = QLinearGradient(bar_x, 0, bar_x + fill_w, 0)
            grad_bar.setColorAt(0, QColor(Colors.CRIMSON_DARK))
            grad_bar.setColorAt(1, QColor(Colors.CRIMSON_GLOW))
            painter.setBrush(QBrush(grad_bar))
            painter.drawRoundedRect(QRectF(bar_x, bar_y, fill_w, bar_h), 1, 1)

            # Glow tip
            tip_glow = QRadialGradient(bar_x + fill_w, bar_y + 1, 6)
            tip_glow.setColorAt(0, QColor(255, 80, 80, 180))
            tip_glow.setColorAt(1, QColor(0, 0, 0, 0))
            painter.setBrush(QBrush(tip_glow))
            painter.drawEllipse(QRectF(bar_x + fill_w - 6, bar_y - 5, 12, 12))

        # Pourcentage
        font_pct = QFont("JetBrains Mono", 10, QFont.Weight.Bold)
        painter.setFont(font_pct)
        painter.setPen(QColor(Colors.SILVER_BRIGHT))
        painter.drawText(QRectF(bar_x + bar_w + 12, bar_y - 8, 50, 20),
                         Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter,
                         f"{int(self._anim_progress)}%")

        # ── Bordure fenêtre ───────────────────────────────────
        painter.setPen(QPen(QColor(Colors.SILVER_GHOST), 1))
        painter.setBrush(Qt.BrushStyle.NoBrush)
        painter.drawRect(0, 0, W - 1, H - 1)

    def _draw_hex_grid(self, painter: QPainter, W: int, H: int):
        """Grille hexagonale très subtile en fond."""
        painter.setPen(QPen(QColor(224, 32, 32, 6), 0.5))
        painter.setBrush(Qt.BrushStyle.NoBrush)
        hex_w, hex_h = 60, 52
        cols = W // hex_w + 2
        rows = H // hex_h + 2
        for row in range(rows):
            for col in range(cols):
                x = col * hex_w + (hex_w // 2 if row % 2 else 0)
                y = row * hex_h
                self._draw_hexagon(painter, x, y, 28)

    def _draw_hexagon(self, painter: QPainter, cx: int, cy: int, r: int):
        path = QPainterPath()
        for i in range(6):
            angle = math.radians(60 * i - 30)
            px = cx + r * math.cos(angle)
            py = cy + r * math.sin(angle)
            if i == 0:
                path.moveTo(px, py)
            else:
                path.lineTo(px, py)
        path.closeSubpath()
        painter.drawPath(path)

    def _draw_scanner_ring(self, painter: QPainter, cx: int, cy: int, r: int):
        """Anneau de scanner rotatif avec cône lumineux."""
        # Arc de base
        painter.setPen(QPen(QColor(224, 32, 32, 30), 1.5))
        painter.setBrush(Qt.BrushStyle.NoBrush)
        painter.drawEllipse(QRectF(cx - r, cy - r, r * 2, r * 2))

        # Cône rotatif (conical gradient simulé via path)
        save = painter.transform()
        painter.translate(cx, cy)
        painter.rotate(self._angle)

        # Secteur lumineux
        path = QPainterPath()
        path.moveTo(0, 0)
        for a in range(0, 75, 2):
            rad = math.radians(a - 37)
            px = r * math.cos(rad)
            py = r * math.sin(rad)
            path.lineTo(px, py)
        path.closeSubpath()

        grad = QRadialGradient(0, 0, r)
        grad.setColorAt(0, QColor(224, 32, 32, 50))
        grad.setColorAt(0.8, QColor(224, 32, 32, 15))
        grad.setColorAt(1, QColor(0, 0, 0, 0))
        painter.setPen(Qt.PenStyle.NoPen)
        painter.setBrush(QBrush(grad))
        painter.drawPath(path)

        # Ligne de scan principale
        painter.setPen(QPen(QColor(255, 60, 60, 160), 1.5))
        painter.drawLine(0, 0, r, 0)

        painter.setTransform(save)
