"""
Dashboard Page — Vue d'ensemble temps réel.
Affiche CPU, GPU, RAM, températures, disque, réseau, score santé.
"""

from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QGridLayout,
    QLabel, QFrame, QScrollArea, QSizePolicy
)
from PyQt6.QtCore import Qt, QTimer
from PyQt6.QtGui import QPainter, QColor, QLinearGradient, QPen, QFont

from ui.theme import Colors, Typography, Spacing
from ui.components.widgets import (
    MetricWidget, GlassCard, CircularGauge,
    SectionHeader, StatusBadge, MiniSparkline
)
from core.system_monitor import SystemSnapshot


class HealthScoreWidget(QWidget):
    """Widget score santé système — central, grand."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self._score = 100
        self._animated = 100.0
        self.setFixedSize(160, 160)

        timer = QTimer(self)
        timer.timeout.connect(self._tick)
        timer.start(16)

    def set_score(self, score: int):
        self._score = score

    def _tick(self):
        diff = self._score - self._animated
        if abs(diff) > 0.1:
            self._animated += diff * 0.08
            self.update()

    def _score_color(self, s: float) -> QColor:
        if s >= 80:
            return QColor(Colors.SUCCESS)
        elif s >= 50:
            return QColor(Colors.WARNING)
        return QColor(Colors.DANGER)

    def paintEvent(self, event):
        from PyQt6.QtGui import QPainterPath, QConicalGradient, QRadialGradient
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)

        w, h = self.width(), self.height()
        cx, cy = w // 2, h // 2
        r = 65
        pw = 10
        color = self._score_color(self._animated)

        # Fond cercle
        painter.setPen(Qt.PenStyle.NoPen)
        bg = QColor(Colors.BG_SURFACE)
        painter.setBrush(bg)
        painter.drawEllipse(cx - r - pw, cy - r - pw, (r + pw) * 2, (r + pw) * 2)

        # Track arc (gris)
        track_pen = QPen(QColor(Colors.SILVER_GHOST), pw)
        track_pen.setCapStyle(Qt.PenCapStyle.RoundCap)
        painter.setPen(track_pen)
        painter.drawArc(cx - r, cy - r, r * 2, r * 2, 225 * 16, -270 * 16)

        # Arc valeur
        if self._animated > 0:
            span = int(-270 * self._animated / 100 * 16)
            grad = QConicalGradient(cx, cy, 225)
            dark = QColor(color)
            dark.setAlpha(120)
            grad.setColorAt(0, dark)
            grad.setColorAt(0.7, color)
            bright = QColor(color)
            bright.setRed(min(255, bright.red() + 40))
            bright.setGreen(min(255, bright.green() + 40))
            grad.setColorAt(1.0, bright)
            val_pen = QPen(QColor(color), pw)
            from PyQt6.QtGui import QBrush
            val_pen = QPen(QBrush(grad), pw)
            val_pen.setCapStyle(Qt.PenCapStyle.RoundCap)
            painter.setPen(val_pen)
            painter.drawArc(cx - r, cy - r, r * 2, r * 2, 225 * 16, span)

        # Glow intérieur
        glow = QRadialGradient(cx, cy, r - pw // 2)
        glow_c = QColor(color)
        glow_c.setAlpha(15)
        glow.setColorAt(0, glow_c)
        glow.setColorAt(1, QColor(0, 0, 0, 0))
        painter.setPen(Qt.PenStyle.NoPen)
        painter.setBrush(glow)
        painter.drawEllipse(cx - r + pw // 2, cy - r + pw // 2,
                            (r - pw // 2) * 2, (r - pw // 2) * 2)

        # Valeur centrale
        painter.setPen(QPen(QColor(Colors.SILVER_BRIGHT)))
        painter.setFont(Typography.font("JetBrains Mono", 28, QFont.Weight.Bold))
        painter.drawText(0, 0, w, h - 20, Qt.AlignmentFlag.AlignCenter,
                         f"{int(self._animated)}")

        # Label /100
        painter.setFont(Typography.label(9))
        painter.setPen(QPen(QColor(Colors.SILVER_DIM)))
        painter.drawText(0, h // 2 + 14, w, 20, Qt.AlignmentFlag.AlignCenter, "/100")

        # Label SANTÉ SYSTÈME
        painter.setFont(Typography.label(8))
        painter.setPen(QPen(color))
        painter.drawText(0, h - 18, w, 18, Qt.AlignmentFlag.AlignCenter, "SANTÉ SYSTÈME")


class SystemInfoBar(QWidget):
    """Barre d'infos système en haut du dashboard."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setFixedHeight(40)
        self._layout = QHBoxLayout(self)
        self._layout.setContentsMargins(Spacing.LG, 0, Spacing.LG, 0)
        self._layout.setSpacing(Spacing.XL)

        self.setStyleSheet(f"""
            background: {Colors.BG_SURFACE};
            border-bottom: 1px solid {Colors.SILVER_GHOST};
        """)

        self._labels: dict[str, QLabel] = {}
        items = [
            ("cpu_name", "CPU: Chargement..."),
            ("gpu_name", "GPU: N/A"),
            ("os_info", "Windows 11"),
            ("uptime", "Uptime: --"),
        ]
        for key, default in items:
            lbl = QLabel(default)
            lbl.setFont(Typography.body(9))
            lbl.setStyleSheet(f"color: {Colors.SILVER_DIM}; background: transparent;")
            self._labels[key] = lbl
            self._layout.addWidget(lbl)
            if key != "uptime":
                sep = QFrame()
                sep.setFrameShape(QFrame.Shape.VLine)
                sep.setStyleSheet(f"color: {Colors.SILVER_GHOST};")
                self._layout.addWidget(sep)

        self._layout.addStretch()

        # Heure
        self.lbl_time = QLabel("--:--:--")
        self.lbl_time.setFont(Typography.mono(10))
        self.lbl_time.setStyleSheet(f"color: {Colors.SILVER_DIM}; background: transparent;")
        self._layout.addWidget(self.lbl_time)

        # Timer heure
        self._clock_timer = QTimer(self)
        self._clock_timer.timeout.connect(self._update_clock)
        self._clock_timer.start(1000)
        self._update_clock()

    def _update_clock(self):
        from datetime import datetime
        self.lbl_time.setText(datetime.now().strftime("%H:%M:%S"))

    def update_system_info(self, snap: SystemSnapshot):
        if snap.cpu_name:
            short_name = snap.cpu_name.split("@")[0].strip()[:35]
            self._labels["cpu_name"].setText(f"CPU: {short_name}")
        if snap.gpu_name and snap.gpu_name != "N/A":
            short_gpu = snap.gpu_name[:30]
            self._labels["gpu_name"].setText(f"GPU: {short_gpu}")

        import psutil
        boot_time = psutil.boot_time()
        import time
        uptime_sec = int(time.time() - boot_time)
        h, m = divmod(uptime_sec // 60, 60)
        self._labels["uptime"].setText(f"Uptime: {h}h{m:02d}m")


class DashboardPage(QWidget):
    """
    Page Dashboard principale.
    Grille de métriques temps réel + score santé.
    """

    def __init__(self, parent=None):
        super().__init__(parent)
        self._build_ui()

    def _build_ui(self):
        root = QVBoxLayout(self)
        root.setContentsMargins(0, 0, 0, 0)
        root.setSpacing(0)

        # Barre infos système
        self.info_bar = SystemInfoBar()
        root.addWidget(self.info_bar)

        # Contenu scrollable
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        scroll.setStyleSheet("QScrollArea { border: none; background: transparent; }")

        content = QWidget()
        content.setStyleSheet(f"background: {Colors.BG_DEEP};")
        layout = QVBoxLayout(content)
        layout.setContentsMargins(Spacing.XL, Spacing.XL, Spacing.XL, Spacing.XL)
        layout.setSpacing(Spacing.LG)

        # ── Header row ───────────────────────────────────────────────
        header_row = QHBoxLayout()
        header_row.addWidget(SectionHeader("Dashboard", "Vue d'ensemble système"))
        header_row.addStretch()

        self.badge_status = StatusBadge("SYSTÈME OK", "ok")
        header_row.addWidget(self.badge_status)
        layout.addLayout(header_row)

        # ── Score santé + métriques primaires ────────────────────────
        top_row = QHBoxLayout()
        top_row.setSpacing(Spacing.LG)

        # Score santé
        health_card = GlassCard(glow_color=Colors.SUCCESS)
        health_card.setFixedWidth(200)
        health_card.layout().setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.health_score = HealthScoreWidget()
        health_card.layout().addWidget(self.health_score, alignment=Qt.AlignmentFlag.AlignCenter)
        top_row.addWidget(health_card)

        # Métriques primaires (grille 2x2)
        metrics_grid = QGridLayout()
        metrics_grid.setSpacing(Spacing.MD)

        self.w_cpu = MetricWidget("CPU", "%", Colors.CHART_CPU)
        self.w_ram = MetricWidget("RAM", "%", Colors.CHART_RAM)
        self.w_gpu = MetricWidget("GPU", "%", Colors.CHART_GPU)
        self.w_temp = MetricWidget("CPU TEMP", "°C", Colors.CHART_TEMP)

        metrics_grid.addWidget(self.w_cpu, 0, 0)
        metrics_grid.addWidget(self.w_ram, 0, 1)
        metrics_grid.addWidget(self.w_gpu, 1, 0)
        metrics_grid.addWidget(self.w_temp, 1, 1)

        metrics_widget = QWidget()
        metrics_widget.setLayout(metrics_grid)
        top_row.addWidget(metrics_widget, 1)

        layout.addLayout(top_row)

        # ── Métriques secondaires ────────────────────────────────────
        layout.addWidget(SectionHeader("Stockage & Réseau", ""))

        bottom_row = QHBoxLayout()
        bottom_row.setSpacing(Spacing.MD)

        self.w_disk = MetricWidget("DISQUE C:", "%", Colors.WARNING)
        self.w_net_recv = MetricWidget("RÉSEAU DL", "MB/s", Colors.CHART_NET)
        self.w_ping = MetricWidget("PING", "ms", Colors.INFO)
        self.w_gpu_temp = MetricWidget("GPU TEMP", "°C", Colors.CHART_TEMP)

        for w in [self.w_disk, self.w_net_recv, self.w_ping, self.w_gpu_temp]:
            bottom_row.addWidget(w)

        layout.addLayout(bottom_row)

        # ── Jauges circulaires ───────────────────────────────────────
        layout.addWidget(SectionHeader("Charge Temps Réel", ""))

        gauges_row = QHBoxLayout()
        gauges_row.setSpacing(Spacing.MD)

        gauge_card = GlassCard()
        gauge_layout = QHBoxLayout()
        gauge_layout.setSpacing(Spacing.XL)

        self.gauge_cpu = CircularGauge("CPU", Colors.CHART_CPU, 110)
        self.gauge_ram = CircularGauge("RAM", Colors.CHART_RAM, 110)
        self.gauge_gpu = CircularGauge("GPU", Colors.CHART_GPU, 110)
        self.gauge_disk = CircularGauge("DISK", Colors.WARNING, 110)

        for g in [self.gauge_cpu, self.gauge_ram, self.gauge_gpu, self.gauge_disk]:
            gauge_layout.addWidget(g, alignment=Qt.AlignmentFlag.AlignCenter)

        gauge_card.layout().addLayout(gauge_layout)
        layout.addWidget(gauge_card)

        layout.addStretch()
        scroll.setWidget(content)
        root.addWidget(scroll)

    def update_metrics(self, snap: SystemSnapshot):
        """Mise à jour de tous les widgets depuis un snapshot."""
        self.info_bar.update_system_info(snap)

        # Métriques cartes
        self.w_cpu.update_value(snap.cpu_percent, (70, 85))
        self.w_cpu.set_subtitle(f"{snap.cpu_freq_mhz:.0f} MHz")
        self.w_ram.update_value(snap.ram_percent, (75, 90))
        self.w_ram.set_subtitle(f"{snap.ram_used_gb:.1f} / {snap.ram_total_gb:.0f} GB")
        self.w_gpu.update_value(snap.gpu_load_percent, (80, 95))
        self.w_gpu.set_subtitle(snap.gpu_name[:20] if snap.gpu_name != "N/A" else "N/A")
        self.w_temp.update_value(snap.cpu_temp_c, (75, 85))
        self.w_disk.update_value(snap.disk_percent, (85, 95))
        self.w_disk.set_subtitle(f"{snap.disk_used_gb:.0f} / {snap.disk_total_gb:.0f} GB")
        self.w_net_recv.update_value(snap.net_recv_mbps, (500, 900))
        self.w_ping.update_value(snap.ping_ms, (50, 100))
        self.w_gpu_temp.update_value(snap.gpu_temp_c, (80, 90))

        # Jauges
        self.gauge_cpu.set_value(snap.cpu_percent)
        self.gauge_ram.set_value(snap.ram_percent)
        self.gauge_gpu.set_value(snap.gpu_load_percent)
        self.gauge_disk.set_value(snap.disk_percent)

        # Score santé
        self.health_score.set_score(snap.health_score)

        # Badge global
        if snap.health_score >= 80:
            self.badge_status.set_status("ok")
            self.badge_status.setText("SYSTÈME OK")
        elif snap.health_score >= 50:
            self.badge_status.set_status("warning")
            self.badge_status.setText("ATTENTION")
        else:
            self.badge_status.set_status("critical")
            self.badge_status.setText("CRITIQUE")
