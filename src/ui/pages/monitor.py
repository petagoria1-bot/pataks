"""
MonitorPage — Moniteur temps réel avancé.
Graphiques CPU, GPU, RAM, Réseau sur 60 secondes.
Températures, fréquences, I/O disque.
Données 100% réelles via SystemMonitor.
"""

import math
from collections import deque

from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel,
    QGridLayout, QScrollArea, QFrame, QSizePolicy
)
from PyQt6.QtCore import Qt, QTimer, QRectF, QPointF
from PyQt6.QtGui import (
    QPainter, QColor, QPen, QBrush, QFont,
    QLinearGradient, QPainterPath
)

from ui.theme import Colors, Typography, Spacing
from ui.components.widgets import GlassCard, SectionHeader, StatusBadge
from core.system_monitor import SystemSnapshot


# ─── LIVE GRAPH ───────────────────────────────────────────────────────────────

class LiveGraph(QWidget):
    """
    Graphique temps réel 60 secondes.
    Ligne principale + gradient fill + grille + valeur courante.
    """

    def __init__(self, title: str, unit: str, color: str,
                 y_max: float = 100.0, y_min: float = 0.0,
                 parent=None):
        super().__init__(parent)
        self.title = title
        self.unit = unit
        self.color = QColor(color)
        self.y_max = y_max
        self.y_min = y_min
        self._data: deque = deque(maxlen=60)
        self._current = 0.0
        self.setMinimumHeight(120)
        self.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)

        # Pré-remplir avec des zéros
        for _ in range(60):
            self._data.append(0.0)

    def push(self, value: float):
        self._current = value
        self._data.append(value)
        self.update()

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)

        W, H = self.width(), self.height()
        pad_l, pad_r, pad_t, pad_b = 44, 12, 28, 24
        gW = W - pad_l - pad_r
        gH = H - pad_t - pad_b

        # Fond
        painter.fillRect(0, 0, W, H, QColor(Colors.BG_SURFACE))

        # Titre + valeur courante
        painter.setFont(Typography.label(8))
        painter.setPen(QColor(Colors.SILVER_DIM))
        painter.drawText(pad_l, 14, self.title.upper())

        val_str = f"{self._current:.1f}{self.unit}" if self.y_max <= 200 else f"{self._current:.0f}{self.unit}"
        painter.setFont(Typography.font("JetBrains Mono", 11, QFont.Weight.Bold))
        painter.setPen(self.color)
        painter.drawText(W - 80, 14, val_str)

        if gW <= 0 or gH <= 0:
            return

        # Grille horizontale (4 lignes)
        painter.setFont(Typography.label(7))
        painter.setPen(QPen(QColor(Colors.SILVER_GHOST), 1, Qt.PenStyle.SolidLine))
        for i in range(5):
            y = pad_t + i * gH // 4
            painter.drawLine(pad_l, y, pad_l + gW, y)
            val_label = self.y_max - (i * (self.y_max - self.y_min) / 4)
            painter.setPen(QColor(Colors.SILVER_GHOST))
            painter.drawText(2, y + 4, f"{val_label:.0f}")
            painter.setPen(QPen(QColor(Colors.SILVER_GHOST), 1))

        # Axe X
        painter.setPen(QPen(QColor(Colors.SILVER_GHOST), 1))
        painter.drawLine(pad_l, pad_t + gH, pad_l + gW, pad_t + gH)

        data = list(self._data)
        n = len(data)
        if n < 2:
            return

        rng = self.y_max - self.y_min
        if rng == 0:
            rng = 1

        def to_xy(i: int, v: float):
            x = pad_l + i * gW / (n - 1)
            y = pad_t + gH - (v - self.y_min) / rng * gH
            return x, max(pad_t, min(pad_t + gH, y))

        pts = [to_xy(i, v) for i, v in enumerate(data)]

        # Fill gradient
        fill_path = QPainterPath()
        fill_path.moveTo(pts[0][0], pad_t + gH)
        for x, y in pts:
            fill_path.lineTo(x, y)
        fill_path.lineTo(pts[-1][0], pad_t + gH)
        fill_path.closeSubpath()

        grad = QLinearGradient(0, pad_t, 0, pad_t + gH)
        c0 = QColor(self.color)
        c0.setAlpha(55)
        c1 = QColor(self.color)
        c1.setAlpha(5)
        grad.setColorAt(0, c0)
        grad.setColorAt(1, c1)
        painter.fillPath(fill_path, QBrush(grad))

        # Ligne principale
        line_path = QPainterPath()
        line_path.moveTo(*pts[0])
        for x, y in pts[1:]:
            line_path.lineTo(x, y)

        pen = QPen(self.color, 1.8)
        pen.setCapStyle(Qt.PenCapStyle.RoundCap)
        pen.setJoinStyle(Qt.PenJoinStyle.RoundJoin)
        painter.setPen(pen)
        painter.setBrush(Qt.BrushStyle.NoBrush)
        painter.drawPath(line_path)

        # Dot dernier point
        lx, ly = pts[-1]
        painter.setPen(Qt.PenStyle.NoPen)
        dot_glow = QColor(self.color)
        dot_glow.setAlpha(60)
        painter.setBrush(dot_glow)
        painter.drawEllipse(QRectF(lx - 5, ly - 5, 10, 10))
        painter.setBrush(self.color)
        painter.drawEllipse(QRectF(lx - 2.5, ly - 2.5, 5, 5))


# ─── STAT CHIP ────────────────────────────────────────────────────────────────

class StatChip(QWidget):
    """Petite puce affichant une valeur statique."""

    def __init__(self, label: str, value: str = "—", unit: str = "",
                 color: str = Colors.SILVER, parent=None):
        super().__init__(parent)
        self.color = color
        layout = QVBoxLayout(self)
        layout.setContentsMargins(12, 10, 12, 10)
        layout.setSpacing(3)

        self.lbl_label = QLabel(label.upper())
        self.lbl_label.setFont(Typography.label(7))
        self.lbl_label.setStyleSheet(f"color: {Colors.SILVER_DIM}; background: transparent; letter-spacing: 1.5px;")
        layout.addWidget(self.lbl_label)

        val_row = QHBoxLayout()
        val_row.setSpacing(3)
        self.lbl_value = QLabel(value)
        self.lbl_value.setFont(Typography.font("JetBrains Mono", 16, QFont.Weight.Bold))
        self.lbl_value.setStyleSheet(f"color: {color}; background: transparent;")
        val_row.addWidget(self.lbl_value)

        if unit:
            lbl_unit = QLabel(unit)
            lbl_unit.setFont(Typography.body(9))
            lbl_unit.setStyleSheet(f"color: {Colors.SILVER_DIM}; background: transparent; padding-top: 4px;")
            val_row.addWidget(lbl_unit)
        val_row.addStretch()
        layout.addLayout(val_row)

        self.setStyleSheet(f"""
            background: {Colors.BG_ELEVATED};
            border: 1px solid {Colors.SILVER_GHOST};
            border-radius: 8px;
        """)

    def set_value(self, value: str, color: str = None):
        self.lbl_value.setText(value)
        if color:
            self.lbl_value.setStyleSheet(f"color: {color}; background: transparent;")


# ─── MONITOR PAGE ─────────────────────────────────────────────────────────────

class MonitorPage(QWidget):
    """Page de monitoring temps réel complète."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self._snapshot = None
        self._build_ui()

    def _build_ui(self):
        root = QVBoxLayout(self)
        root.setContentsMargins(0, 0, 0, 0)
        root.setSpacing(0)
        self.setStyleSheet(f"background: {Colors.BG_DEEP};")

        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setStyleSheet("QScrollArea { border: none; background: transparent; }")

        content = QWidget()
        content.setStyleSheet(f"background: {Colors.BG_DEEP};")
        layout = QVBoxLayout(content)
        layout.setContentsMargins(Spacing.XL, Spacing.XL, Spacing.XL, Spacing.XL)
        layout.setSpacing(Spacing.LG)

        # Header
        hrow = QHBoxLayout()
        hrow.addWidget(SectionHeader("Moniteur Temps Réel", "Graphiques 60 secondes glissants"))
        hrow.addStretch()
        self._badge = StatusBadge("LIVE", "ok")
        hrow.addWidget(self._badge)
        layout.addLayout(hrow)

        # ── Chips stats rapides ─────────────────────────────────────
        chips_row = QHBoxLayout()
        chips_row.setSpacing(Spacing.SM)
        self._chips = {}
        chip_defs = [
            ("cpu_val",   "CPU",          "—", "%",   Colors.CHART_CPU),
            ("gpu_val",   "GPU",          "—", "%",   Colors.CHART_GPU),
            ("ram_val",   "RAM",          "—", "%",   Colors.CHART_RAM),
            ("cpu_temp",  "Temp CPU",     "—", "°C",  Colors.CHART_TEMP),
            ("gpu_temp",  "Temp GPU",     "—", "°C",  Colors.CHART_TEMP),
            ("ping_val",  "Ping",         "—", "ms",  Colors.INFO),
            ("disk_read", "Disque Lect.", "—", "MB/s",Colors.WARNING),
            ("net_recv",  "Réseau DL",    "—", "MB/s",Colors.CHART_RAM),
        ]
        for key, label, val, unit, color in chip_defs:
            chip = StatChip(label, val, unit, color)
            self._chips[key] = chip
            chips_row.addWidget(chip)
        layout.addLayout(chips_row)

        # ── Graphiques ─────────────────────────────────────────────
        layout.addWidget(SectionHeader("CPU & GPU", ""))

        cpu_gpu_row = QHBoxLayout()
        cpu_gpu_row.setSpacing(Spacing.MD)

        self._graph_cpu = LiveGraph("Charge CPU", "%", Colors.CHART_CPU)
        self._graph_gpu = LiveGraph("Charge GPU", "%", Colors.CHART_GPU)

        wrap_cpu = GlassCard()
        wrap_cpu.layout().setContentsMargins(4, 8, 4, 4)
        wrap_cpu.layout().addWidget(self._graph_cpu)

        wrap_gpu = GlassCard()
        wrap_gpu.layout().setContentsMargins(4, 8, 4, 4)
        wrap_gpu.layout().addWidget(self._graph_gpu)

        cpu_gpu_row.addWidget(wrap_cpu)
        cpu_gpu_row.addWidget(wrap_gpu)
        layout.addLayout(cpu_gpu_row)

        layout.addWidget(SectionHeader("RAM & Réseau", ""))

        ram_net_row = QHBoxLayout()
        ram_net_row.setSpacing(Spacing.MD)

        self._graph_ram = LiveGraph("Utilisation RAM", "%", Colors.CHART_RAM)
        self._graph_net = LiveGraph("Réseau Download", "MB/s", Colors.INFO, y_max=50, y_min=0)

        wrap_ram = GlassCard()
        wrap_ram.layout().setContentsMargins(4, 8, 4, 4)
        wrap_ram.layout().addWidget(self._graph_ram)

        wrap_net = GlassCard()
        wrap_net.layout().setContentsMargins(4, 8, 4, 4)
        wrap_net.layout().addWidget(self._graph_net)

        ram_net_row.addWidget(wrap_ram)
        ram_net_row.addWidget(wrap_net)
        layout.addLayout(ram_net_row)

        layout.addWidget(SectionHeader("Températures", ""))

        temp_row = QHBoxLayout()
        temp_row.setSpacing(Spacing.MD)
        self._graph_cpu_temp = LiveGraph("Température CPU", "°C", Colors.CHART_TEMP, y_max=100, y_min=20)
        self._graph_gpu_temp = LiveGraph("Température GPU", "°C", Colors.WARNING, y_max=100, y_min=20)

        wrap_ct = GlassCard()
        wrap_ct.layout().setContentsMargins(4, 8, 4, 4)
        wrap_ct.layout().addWidget(self._graph_cpu_temp)

        wrap_gt = GlassCard()
        wrap_gt.layout().setContentsMargins(4, 8, 4, 4)
        wrap_gt.layout().addWidget(self._graph_gpu_temp)

        temp_row.addWidget(wrap_ct)
        temp_row.addWidget(wrap_gt)
        layout.addLayout(temp_row)

        layout.addStretch()
        scroll.setWidget(content)
        root.addWidget(scroll)

    def update_metrics(self, snap: SystemSnapshot):
        """Met à jour tous les graphiques et chips depuis un snapshot réel."""
        self._snapshot = snap

        # Chips
        self._chips["cpu_val"].set_value(f"{snap.cpu_percent:.0f}",
            self._pct_color(snap.cpu_percent, 70, 85))
        self._chips["gpu_val"].set_value(f"{snap.gpu_load_percent:.0f}",
            self._pct_color(snap.gpu_load_percent, 80, 92))
        self._chips["ram_val"].set_value(f"{snap.ram_percent:.0f}",
            self._pct_color(snap.ram_percent, 75, 90))
        self._chips["cpu_temp"].set_value(
            f"{snap.cpu_temp_c:.0f}" if snap.cpu_temp_c > 0 else "—",
            self._temp_color(snap.cpu_temp_c))
        self._chips["gpu_temp"].set_value(
            f"{snap.gpu_temp_c:.0f}" if snap.gpu_temp_c > 0 else "—",
            self._temp_color(snap.gpu_temp_c))
        self._chips["ping_val"].set_value(
            f"{snap.ping_ms:.0f}" if snap.ping_ms > 0 else "—",
            Colors.SUCCESS if snap.ping_ms < 30 else Colors.WARNING if snap.ping_ms < 80 else Colors.DANGER)
        self._chips["disk_read"].set_value(f"{snap.disk_read_mbps:.1f}")
        self._chips["net_recv"].set_value(f"{snap.net_recv_mbps:.2f}")

        # Graphiques
        self._graph_cpu.push(snap.cpu_percent)
        self._graph_gpu.push(snap.gpu_load_percent)
        self._graph_ram.push(snap.ram_percent)
        self._graph_net.push(snap.net_recv_mbps)
        self._graph_cpu_temp.push(snap.cpu_temp_c)
        self._graph_gpu_temp.push(snap.gpu_temp_c)

    @staticmethod
    def _pct_color(v: float, w: float, c: float) -> str:
        return Colors.DANGER if v >= c else Colors.WARNING if v >= w else Colors.SUCCESS

    @staticmethod
    def _temp_color(t: float) -> str:
        return Colors.DANGER if t >= 85 else Colors.WARNING if t >= 70 else Colors.SUCCESS
