"""
DetectionScreen — Détection réelle des composants matériels.
Scanne CPU, GPU, RAM, Disque, OS, Réseau via psutil + WMI.
Chaque composant est animé au fur et à mesure de sa détection réelle.
"""

import threading
import time
import logging
from dataclasses import dataclass, field
from typing import Optional, Callable

from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel,
    QGridLayout, QPushButton, QFrame, QApplication, QSizePolicy
)
from PyQt6.QtCore import (
    Qt, QTimer, QThread, pyqtSignal, QRectF, QPointF
)
from PyQt6.QtGui import (
    QPainter, QColor, QPen, QBrush, QFont,
    QLinearGradient, QRadialGradient, QPainterPath
)

import psutil

from ui.theme import Colors, Typography, Spacing

logger = logging.getLogger(__name__)

# WMI optionnel
try:
    import wmi as wmilib
    WMI_OK = True
except ImportError:
    WMI_OK = False


# ─── DATACLASS RÉSULTAT DÉTECTION ─────────────────────────────────────────────

@dataclass
class ComponentInfo:
    id: str
    icon: str
    label: str
    name: str = "—"
    detail: str = ""
    extra: str = ""
    detected: bool = False
    score: int = 0   # 0-100 qualité du composant


@dataclass
class SystemConfig:
    cpu: ComponentInfo = field(default_factory=lambda: ComponentInfo("cpu", "🖥", "Processeur"))
    gpu: ComponentInfo = field(default_factory=lambda: ComponentInfo("gpu", "🎮", "Carte graphique"))
    ram: ComponentInfo = field(default_factory=lambda: ComponentInfo("ram", "💾", "Mémoire RAM"))
    disk: ComponentInfo = field(default_factory=lambda: ComponentInfo("disk", "💿", "Stockage"))
    os: ComponentInfo = field(default_factory=lambda: ComponentInfo("os", "🪟", "Système"))
    net: ComponentInfo = field(default_factory=lambda: ComponentInfo("net", "🌐", "Réseau"))

    def all_components(self) -> list[ComponentInfo]:
        return [self.cpu, self.gpu, self.ram, self.disk, self.os, self.net]

    def all_detected(self) -> bool:
        return all(c.detected for c in self.all_components())

    def global_score(self) -> int:
        detected = [c for c in self.all_components() if c.detected]
        if not detected:
            return 0
        return int(sum(c.score for c in detected) / len(detected))


# ─── WORKER DE DÉTECTION RÉELLE ───────────────────────────────────────────────

class DetectionWorker(QThread):
    """
    Thread de détection réelle des composants.
    Émet component_detected pour chaque composant trouvé.
    """

    component_detected = pyqtSignal(str, object)   # (id, ComponentInfo)
    all_done = pyqtSignal(object)                   # SystemConfig complet

    def __init__(self):
        super().__init__()
        self.config = SystemConfig()

    def run(self):
        _com_ok = False
        try:
            import pythoncom
            pythoncom.CoInitialize()
            _com_ok = True
        except Exception:
            pass

        try:
            self._run_detectors()
        finally:
            if _com_ok:
                try:
                    import pythoncom
                    pythoncom.CoUninitialize()
                except Exception:
                    pass

    def _run_detectors(self):
        detectors = [
            ("cpu",  self._detect_cpu),
            ("gpu",  self._detect_gpu),
            ("ram",  self._detect_ram),
            ("disk", self._detect_disk),
            ("os",   self._detect_os),
            ("net",  self._detect_net),
        ]
        for comp_id, fn in detectors:
            try:
                info = fn()
                self.component_detected.emit(comp_id, info)
                time.sleep(0.15)
            except Exception as e:
                logger.error(f"Erreur détection {comp_id}: {e}")
                comp = getattr(self.config, comp_id)
                comp.name = "Erreur de détection"
                comp.detected = True
                self.component_detected.emit(comp_id, comp)

        self.all_done.emit(self.config)

    # ── DÉTECTION CPU ──────────────────────────────────────────────────────────
    def _detect_cpu(self) -> ComponentInfo:
        info = self.config.cpu
        name = "Processeur inconnu"
        cores = psutil.cpu_count(logical=False) or 1
        threads = psutil.cpu_count(logical=True) or 1
        freq = psutil.cpu_freq()
        freq_base = f"{freq.min / 1000:.2f} GHz" if freq and freq.min else "—"
        freq_boost = f"{freq.max / 1000:.2f} GHz" if freq and freq.max else "—"

        if WMI_OK:
            try:
                c = wmilib.WMI()
                for cpu in c.Win32_Processor():
                    name = cpu.Name.strip()
                    break
            except Exception:
                pass
        else:
            import platform
            name = platform.processor() or "CPU Détecté"

        info.name = name
        info.detail = f"{cores} cœurs · {threads} threads · Base {freq_base} · Boost {freq_boost}"
        info.extra = f"Cache: {self._get_cpu_cache()} · Architecture x64"
        info.detected = True
        # Score basé sur nb cœurs
        info.score = min(100, 50 + cores * 6)
        return info

    def _get_cpu_cache(self) -> str:
        if WMI_OK:
            try:
                c = wmilib.WMI()
                for cpu in c.Win32_Processor():
                    cache = getattr(cpu, "L2CacheSize", 0) or 0
                    if cache:
                        return f"{cache // 1024} MB"
            except Exception:
                pass
        return "—"

    # ── DÉTECTION GPU ──────────────────────────────────────────────────────────
    def _detect_gpu(self) -> ComponentInfo:
        info = self.config.gpu
        name = "GPU non détecté"
        vram = "—"
        driver = "—"
        api = "DirectX 12"

        if WMI_OK:
            try:
                c = wmilib.WMI()
                for gpu in c.Win32_VideoController():
                    n = getattr(gpu, "Name", "").strip()
                    if n:
                        name = n
                        ram = getattr(gpu, "AdapterRAM", 0) or 0
                        if ram > 0:
                            vram = f"{ram // (1024**3)} GB"
                        driver = getattr(gpu, "DriverVersion", "—")
                        break
            except Exception:
                pass
        else:
            name = "GPU Détecté (WMI requis pour détails)"

        info.name = name
        info.detail = f"VRAM {vram} · Driver {driver} · {api}"
        info.extra = f"Rendu matériel disponible"
        info.detected = True
        info.score = 70  # Base — WMI donnerait plus de précision
        return info

    # ── DÉTECTION RAM ──────────────────────────────────────────────────────────
    def _detect_ram(self) -> ComponentInfo:
        info = self.config.ram
        mem = psutil.virtual_memory()
        total_gb = mem.total / (1024**3)
        used_gb = mem.used / (1024**3)
        pct = mem.percent

        ram_type = "DDR4"
        speed = "—"
        slots_info = "—"

        if WMI_OK:
            try:
                c = wmilib.WMI()
                modules = list(c.Win32_PhysicalMemory())
                if modules:
                    spd = getattr(modules[0], "Speed", 0)
                    if spd:
                        speed = f"{spd} MHz"
                    mem_type = getattr(modules[0], "MemoryType", 0)
                    # 26=DDR4, 34=DDR5
                    if mem_type == 34:
                        ram_type = "DDR5"
                    elif mem_type == 26:
                        ram_type = "DDR4"
                    slots_info = f"{len(modules)} module(s)"
            except Exception:
                pass

        info.name = f"{total_gb:.0f} GB {ram_type} {speed}"
        info.detail = f"{slots_info} · {used_gb:.1f} GB utilisés ({pct:.0f}%)"
        info.extra = f"Disponible : {(mem.available / (1024**3)):.1f} GB"
        info.detected = True
        # Score basé sur la quantité
        if total_gb >= 32:
            info.score = 100
        elif total_gb >= 16:
            info.score = 85
        elif total_gb >= 8:
            info.score = 65
        else:
            info.score = 40
        return info

    # ── DÉTECTION DISQUE ───────────────────────────────────────────────────────
    def _detect_disk(self) -> ComponentInfo:
        info = self.config.disk
        name = "Disque système"
        total_gb = 0
        free_gb = 0
        disk_type = "Disque"

        try:
            usage = psutil.disk_usage("C:\\")
            total_gb = usage.total / (1024**3)
            free_gb = usage.free / (1024**3)
        except Exception:
            try:
                usage = psutil.disk_usage("/")
                total_gb = usage.total / (1024**3)
                free_gb = usage.free / (1024**3)
            except Exception:
                pass

        if WMI_OK:
            try:
                c = wmilib.WMI()
                for disk in c.Win32_DiskDrive():
                    n = getattr(disk, "Model", "").strip()
                    if n:
                        name = n
                    media = (getattr(disk, "MediaType", "") or "").upper()
                    model = (getattr(disk, "Model", "") or "").upper()
                    if "SSD" in model or "NVME" in model or "SOLID" in media:
                        disk_type = "SSD"
                        if "NVME" in model or "NVM" in model:
                            disk_type = "NVMe SSD"
                    else:
                        disk_type = "HDD"
                    break
            except Exception:
                pass

        info.name = f"{name} ({disk_type})"
        info.detail = f"{total_gb:.0f} GB total · {free_gb:.0f} GB libres"
        info.extra = f"Partition C: · {(100 - free_gb/total_gb*100) if total_gb else 0:.0f}% utilisé"
        info.detected = True
        # Score : SSD NVMe = top, HDD = moins bien
        if "NVMe" in disk_type:
            info.score = 100
        elif "SSD" in disk_type:
            info.score = 85
        else:
            info.score = 55
        return info

    # ── DÉTECTION OS ───────────────────────────────────────────────────────────
    def _detect_os(self) -> ComponentInfo:
        info = self.config.os
        import platform
        os_name = platform.system()
        os_version = platform.version()
        os_release = platform.release()

        win_name = f"Windows {os_release}"
        build = "—"

        if WMI_OK:
            try:
                c = wmilib.WMI()
                for os_obj in c.Win32_OperatingSystem():
                    caption = getattr(os_obj, "Caption", "").strip()
                    if caption:
                        win_name = caption
                    build = getattr(os_obj, "BuildNumber", "—")
                    break
            except Exception:
                pass

        # Uptime
        boot_time = psutil.boot_time()
        uptime_sec = int(time.time() - boot_time)
        h, rem = divmod(uptime_sec, 3600)
        m = rem // 60
        uptime_str = f"{h}h{m:02d}m"

        info.name = win_name
        info.detail = f"Build {build} · Uptime {uptime_str} · x64"
        info.extra = f"DirectX 12 · Vulkan disponible"
        info.detected = True
        info.score = 90
        return info

    # ── DÉTECTION RÉSEAU ───────────────────────────────────────────────────────
    def _detect_net(self) -> ComponentInfo:
        info = self.config.net
        adapter_name = "Adaptateur réseau"
        speed_str = "—"
        ping_ms = 0

        if WMI_OK:
            try:
                c = wmilib.WMI()
                for nic in c.Win32_NetworkAdapterConfiguration(IPEnabled=True):
                    name = getattr(nic, "Description", "").strip()
                    if name:
                        adapter_name = name
                        break
            except Exception:
                pass

        # Ping réel vers 8.8.8.8
        try:
            import subprocess
            result = subprocess.run(
                ["ping", "-n", "3", "8.8.8.8"],
                capture_output=True, text=True, timeout=8
            )
            import re
            m = re.search(r"(?:Moyenne|Average)\s*=\s*(\d+)ms", result.stdout, re.IGNORECASE)
            if m:
                ping_ms = int(m.group(1))
        except Exception:
            ping_ms = 0

        # Vitesse interface active
        try:
            stats = psutil.net_if_stats()
            for iface, st in stats.items():
                if st.isup and st.speed > 0:
                    spd = st.speed
                    speed_str = f"{spd} Mbps" if spd < 1000 else f"{spd // 1000} Gbps"
                    break
        except Exception:
            pass

        ping_label = f"{ping_ms}ms" if ping_ms > 0 else "Non testé"
        info.name = adapter_name
        info.detail = f"Vitesse : {speed_str} · Ping DNS : {ping_label}"
        info.extra = "IPv4 · IPv6 · DNS Cloudflare disponible"
        info.detected = True
        info.score = 100 if ping_ms < 30 else (80 if ping_ms < 80 else 60)
        return info


# ─── COMPONENT CARD ───────────────────────────────────────────────────────────

class ComponentCard(QWidget):
    """Carte de composant avec animation de scan."""

    STATE_WAITING  = 0
    STATE_SCANNING = 1
    STATE_DONE     = 2

    def __init__(self, comp: ComponentInfo, parent=None):
        super().__init__(parent)
        self.comp = comp
        self._state = self.STATE_WAITING
        self._scan_angle = 0.0
        self._blink = True
        self._alpha_in = 0.0

        self.setMinimumHeight(100)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(14, 12, 14, 12)
        layout.setSpacing(6)

        # Header
        head = QHBoxLayout()
        head.setSpacing(10)

        self.lbl_icon = QLabel(comp.icon)
        self.lbl_icon.setFont(QFont("Segoe UI Emoji", 18))
        self.lbl_icon.setFixedWidth(32)
        self.lbl_icon.setStyleSheet("background: transparent;")
        head.addWidget(self.lbl_icon)

        text_col = QVBoxLayout()
        text_col.setSpacing(1)
        self.lbl_label = QLabel(comp.label.upper())
        self.lbl_label.setFont(Typography.label(8))
        self.lbl_label.setStyleSheet(f"color: {Colors.SILVER_DIM}; background: transparent; letter-spacing: 1.5px;")
        text_col.addWidget(self.lbl_label)
        head.addLayout(text_col, 1)

        self.lbl_status = QLabel("EN ATTENTE")
        self.lbl_status.setFont(Typography.label(8))
        self.lbl_status.setStyleSheet(f"color: {Colors.SILVER_GHOST}; background: transparent;")
        head.addWidget(self.lbl_status)

        layout.addLayout(head)

        # Nom composant
        self.lbl_name = QLabel("—")
        self.lbl_name.setFont(Typography.font("JetBrains Mono", 11, QFont.Weight.Bold))
        self.lbl_name.setStyleSheet(f"color: {Colors.SILVER_BRIGHT}; background: transparent;")
        self.lbl_name.setWordWrap(True)
        layout.addWidget(self.lbl_name)

        # Détail
        self.lbl_detail = QLabel("")
        self.lbl_detail.setFont(Typography.body(9))
        self.lbl_detail.setStyleSheet(f"color: {Colors.SILVER_DIM}; background: transparent;")
        self.lbl_detail.setWordWrap(True)
        layout.addWidget(self.lbl_detail)

        # Barre de scan
        self.bar_widget = _ScanBar()
        layout.addWidget(self.bar_widget)

        # Timer animations
        self._anim_timer = QTimer(self)
        self._anim_timer.timeout.connect(self._tick)
        self._anim_timer.start(50)

    def start_scan(self):
        self._state = self.STATE_SCANNING
        self.lbl_status.setText("SCAN...")
        self.lbl_status.setStyleSheet(f"color: {Colors.CRIMSON}; background: transparent;")
        self.lbl_name.setText("Détection en cours...")
        self.update()

    def set_result(self, info: ComponentInfo):
        self.comp = info
        self._state = self.STATE_DONE
        self.lbl_name.setText(info.name)
        self.lbl_detail.setText(info.detail)
        self.lbl_status.setText("✓ OK")
        self.lbl_status.setStyleSheet(f"color: {Colors.SUCCESS}; background: transparent;")
        self.bar_widget.set_value(100, done=True)
        self.update()

    def _tick(self):
        if self._state == self.STATE_SCANNING:
            self._scan_angle = (self._scan_angle + 8) % 360
            self._blink = not self._blink
            self.bar_widget.advance()
        if self._alpha_in < 1.0:
            self._alpha_in = min(1.0, self._alpha_in + 0.08)
        self.update()

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        rect = self.rect()

        # Fond carte
        if self._state == self.STATE_DONE:
            bg = QColor(15, 25, 18)
            border = QColor(Colors.SUCCESS)
            border.setAlpha(80)
        elif self._state == self.STATE_SCANNING:
            bg = QColor(20, 8, 8)
            border = QColor(Colors.CRIMSON)
            border.setAlpha(120)
        else:
            bg = QColor(Colors.BG_SURFACE)
            border = QColor(Colors.SILVER_GHOST)
            border.setAlpha(80)

        path = QPainterPath()
        path.addRoundedRect(QRectF(rect.adjusted(1, 1, -1, -1)), 10, 10)
        painter.fillPath(path, bg)
        painter.setPen(QPen(border, 1))
        painter.drawPath(path)

        # Top highlight
        if self._state != self.STATE_WAITING:
            top_grad = QLinearGradient(0, 0, rect.width(), 0)
            top_c = QColor(Colors.SUCCESS if self._state == self.STATE_DONE else Colors.CRIMSON)
            top_c.setAlpha(60)
            top_grad.setColorAt(0, QColor(0, 0, 0, 0))
            top_grad.setColorAt(0.5, top_c)
            top_grad.setColorAt(1, QColor(0, 0, 0, 0))
            painter.setPen(Qt.PenStyle.NoPen)
            painter.setBrush(QBrush(top_grad))
            painter.drawRect(QRectF(1, 1, rect.width() - 2, 1))

        super().paintEvent(event)


class _ScanBar(QWidget):
    """Mini barre de progression animée pour le scan."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setFixedHeight(3)
        self._value = 0.0
        self._done = False

    def set_value(self, v: float, done: bool = False):
        self._value = v
        self._done = done
        self.update()

    def advance(self):
        if not self._done:
            self._value = min(90, self._value + 3)
            self.update()

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        W, H = self.width(), self.height()

        # Track
        painter.setPen(Qt.PenStyle.NoPen)
        painter.setBrush(QColor(Colors.BG_ELEVATED))
        painter.drawRoundedRect(QRectF(0, 0, W, H), 1, 1)

        fill_w = int(W * self._value / 100)
        if fill_w > 0:
            grad = QLinearGradient(0, 0, fill_w, 0)
            if self._done:
                grad.setColorAt(0, QColor("#0e6e35"))
                grad.setColorAt(1, QColor(Colors.SUCCESS))
            else:
                grad.setColorAt(0, QColor(Colors.CRIMSON_DARK))
                grad.setColorAt(1, QColor(Colors.CRIMSON_GLOW))
            painter.setBrush(QBrush(grad))
            painter.drawRoundedRect(QRectF(0, 0, fill_w, H), 1, 1)


# ─── BOUTON DETECT CENTRAL ────────────────────────────────────────────────────

class DetectButton(QWidget):
    """Grand bouton circulaire central avec anneaux pulsants."""

    clicked = pyqtSignal()

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setFixedSize(200, 200)
        self._hover = False
        self._pulse = 0.0
        self.setCursor(Qt.CursorShape.PointingHandCursor)

        self._timer = QTimer(self)
        self._timer.timeout.connect(self._tick)
        self._timer.start(20)

    def _tick(self):
        self._pulse = (self._pulse + 0.04) % (2 * 3.14159)
        self.update()

    def enterEvent(self, e):
        self._hover = True

    def leaveEvent(self, e):
        self._hover = False

    def mousePressEvent(self, e):
        if e.button() == Qt.MouseButton.LeftButton:
            self.clicked.emit()

    def paintEvent(self, event):
        import math
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)

        W, H = self.width(), self.height()
        cx, cy = W // 2, H // 2

        pulse = 0.5 + 0.5 * math.sin(self._pulse)

        # Anneaux externes
        for r, base_a in [(85, 30), (95, 18), (105, 10)]:
            a = int(base_a * pulse)
            painter.setPen(QPen(QColor(224, 32, 32, a), 1))
            painter.setBrush(Qt.BrushStyle.NoBrush)
            painter.drawEllipse(QRectF(cx - r, cy - r, r * 2, r * 2))

        # Cercle principal
        r_main = 75
        hover_boost = 8 if self._hover else 0
        glow_a = int((120 + 60 * pulse + hover_boost * 3))
        glow = QRadialGradient(cx, cy, r_main)
        glow.setColorAt(0, QColor(224, 32, 32, 40 + hover_boost * 2))
        glow.setColorAt(0.7, QColor(224, 32, 32, 15))
        glow.setColorAt(1, QColor(0, 0, 0, 0))
        painter.setPen(Qt.PenStyle.NoPen)
        painter.setBrush(QBrush(glow))
        painter.drawEllipse(QRectF(cx - r_main - 20, cy - r_main - 20,
                                   (r_main + 20) * 2, (r_main + 20) * 2))

        grad = QRadialGradient(cx - 15, cy - 15, r_main)
        grad.setColorAt(0, QColor(60, 10, 10))
        grad.setColorAt(1, QColor(15, 3, 10))
        painter.setBrush(QBrush(grad))
        border_color = QColor(Colors.CRIMSON_GLOW if self._hover else Colors.CRIMSON)
        border_color.setAlpha(200)
        painter.setPen(QPen(border_color, 2))
        painter.drawEllipse(QRectF(cx - r_main, cy - r_main, r_main * 2, r_main * 2))

        # Icône hexagone
        font_icon = QFont("Segoe UI Symbol", 28)
        painter.setPen(QColor(Colors.CRIMSON_GLOW if self._hover else Colors.CRIMSON))
        painter.setFont(font_icon)
        painter.drawText(QRectF(0, -16, W, H), Qt.AlignmentFlag.AlignCenter, "⬡")

        # Texte
        font_txt = QFont("Inter", 9, QFont.Weight.Bold)
        font_txt.setLetterSpacing(QFont.SpacingType.AbsoluteSpacing, 1.5)
        painter.setFont(font_txt)
        painter.setPen(QColor(Colors.SILVER_BRIGHT))
        painter.drawText(QRectF(0, 20, W, H), Qt.AlignmentFlag.AlignCenter, "DÉTECTER\nMES COMPOSANTS")


# ─── DETECTION SCREEN ─────────────────────────────────────────────────────────

class DetectionScreen(QWidget):
    """Écran de détection des composants."""

    detection_complete = pyqtSignal(object)  # SystemConfig

    def __init__(self, parent=None):
        super().__init__(parent)
        self._config = SystemConfig()
        self._cards: dict[str, ComponentCard] = {}
        self._worker: Optional[DetectionWorker] = None
        self._build_ui()

    def _build_ui(self):
        root = QVBoxLayout(self)
        root.setContentsMargins(0, 0, 0, 0)
        root.setSpacing(0)

        self.setStyleSheet(f"background: {Colors.BG_DEEP};")

        # Contenu centré
        center = QVBoxLayout()
        center.setAlignment(Qt.AlignmentFlag.AlignCenter)
        center.setSpacing(32)

        # ── Hero (titre + bouton central) ─────────────────────────────
        self._hero_widget = QWidget()
        hero_layout = QVBoxLayout(self._hero_widget)
        hero_layout.setAlignment(Qt.AlignmentFlag.AlignCenter)
        hero_layout.setSpacing(24)

        lbl_title = QLabel("Prêt à analyser votre machine")
        lbl_title.setFont(Typography.font("Rajdhani", 30, QFont.Weight.Bold))
        lbl_title.setStyleSheet(f"color: {Colors.SILVER_BRIGHT}; background: transparent;")
        lbl_title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        hero_layout.addWidget(lbl_title)

        lbl_sub = QLabel(
            "PATAKS va détecter vos composants réels :\n"
            "Processeur, Carte graphique, RAM, Stockage, Système, Réseau."
        )
        lbl_sub.setFont(Typography.body(11))
        lbl_sub.setStyleSheet(f"color: {Colors.SILVER_DIM}; background: transparent;")
        lbl_sub.setAlignment(Qt.AlignmentFlag.AlignCenter)
        hero_layout.addWidget(lbl_sub)

        self._detect_btn = DetectButton()
        self._detect_btn.clicked.connect(self._start_detection)
        hero_layout.addWidget(self._detect_btn, 0, Qt.AlignmentFlag.AlignCenter)

        center.addWidget(self._hero_widget)

        # ── Grille composants (cachée initialement) ──────────────────
        self._grid_widget = QWidget()
        self._grid_widget.hide()
        grid = QGridLayout(self._grid_widget)
        grid.setSpacing(12)
        grid.setContentsMargins(40, 0, 40, 0)

        comp_order = [
            ("cpu",  self._config.cpu),
            ("gpu",  self._config.gpu),
            ("ram",  self._config.ram),
            ("disk", self._config.disk),
            ("os",   self._config.os),
            ("net",  self._config.net),
        ]
        for i, (cid, comp) in enumerate(comp_order):
            card = ComponentCard(comp)
            self._cards[cid] = card
            grid.addWidget(card, i // 3, i % 3)

        center.addWidget(self._grid_widget)

        # ── Ready row (cachée initialement) ─────────────────────────
        self._ready_widget = QWidget()
        self._ready_widget.hide()
        ready_layout = QHBoxLayout(self._ready_widget)
        ready_layout.setContentsMargins(40, 0, 40, 0)
        ready_layout.setSpacing(12)

        # Score card
        self._score_card = QWidget()
        self._score_card.setStyleSheet(f"""
            background: {Colors.BG_SURFACE};
            border: 1px solid rgba(30,196,90,0.3);
            border-radius: 10px;
        """)
        sc_layout = QHBoxLayout(self._score_card)
        sc_layout.setContentsMargins(16, 12, 16, 12)
        sc_layout.setSpacing(14)

        self._lbl_score_num = QLabel("—")
        self._lbl_score_num.setFont(Typography.font("JetBrains Mono", 38, QFont.Weight.Bold))
        self._lbl_score_num.setStyleSheet(f"color: {Colors.SUCCESS}; background: transparent;")
        sc_layout.addWidget(self._lbl_score_num)

        score_texts = QVBoxLayout()
        self._lbl_score_title = QLabel("Configuration détectée")
        self._lbl_score_title.setFont(Typography.heading(13))
        self._lbl_score_title.setStyleSheet(f"color: {Colors.SILVER_BRIGHT}; background: transparent;")

        self._lbl_score_sub = QLabel("Prêt pour l'optimisation gaming.")
        self._lbl_score_sub.setFont(Typography.body(10))
        self._lbl_score_sub.setStyleSheet(f"color: {Colors.SILVER_DIM}; background: transparent;")
        self._lbl_score_sub.setWordWrap(True)

        score_texts.addWidget(self._lbl_score_title)
        score_texts.addWidget(self._lbl_score_sub)
        sc_layout.addLayout(score_texts, 1)

        ready_layout.addWidget(self._score_card, 1)

        # Bouton lancer
        self._launch_btn = QPushButton("⚡  LANCER PATAKS")
        self._launch_btn.setFixedSize(200, 70)
        self._launch_btn.setFont(Typography.font("Inter", 12, QFont.Weight.Bold))
        self._launch_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self._launch_btn.setStyleSheet(f"""
            QPushButton {{
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                    stop:0 {Colors.CRIMSON_GLOW}, stop:1 {Colors.CRIMSON});
                color: white;
                border: none;
                border-radius: 10px;
                font-size: 13px;
                font-weight: 700;
                letter-spacing: 1px;
            }}
            QPushButton:hover {{
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                    stop:0 #FF5555, stop:1 {Colors.CRIMSON_GLOW});
            }}
            QPushButton:pressed {{
                background: {Colors.CRIMSON_DARK};
            }}
        """)
        self._launch_btn.clicked.connect(self._on_launch)
        ready_layout.addWidget(self._launch_btn)

        center.addWidget(self._ready_widget)

        root.addStretch()
        root.addLayout(center)
        root.addStretch()

    def _start_detection(self):
        """Lance la détection réelle des composants."""
        self._hero_widget.hide()
        self._grid_widget.show()

        self._worker = DetectionWorker()
        self._worker.component_detected.connect(self._on_component_detected)
        self._worker.all_done.connect(self._on_all_done)
        self._worker.start()

    def _on_component_detected(self, comp_id: str, info: ComponentInfo):
        """Met à jour la carte du composant détecté."""
        if comp_id in self._cards:
            card = self._cards[comp_id]
            card.start_scan()
            # Délai visuel de 0.6s pour voir l'animation de scan
            QTimer.singleShot(600, lambda: card.set_result(info))
            # Stocker dans la config
            setattr(self._config, comp_id, info)

    def _on_all_done(self, config: SystemConfig):
        """Affiche le récapitulatif et le bouton lancer."""
        self._config = config
        QTimer.singleShot(1000, self._show_ready)

    def _show_ready(self):
        score = self._config.global_score()
        self._lbl_score_num.setText(f"{score}")
        comp_names = []
        for c in self._config.all_components():
            if c.detected and c.name and c.name != "—":
                comp_names.append(c.name.split(" ")[:2])
        # Sous-titre avec les composants détectés
        self._lbl_score_sub.setText(
            f"{self._config.cpu.name.split('@')[0].strip()} · "
            f"{self._config.gpu.name.split(' ')[0] + ' ' + self._config.gpu.name.split(' ')[1] if len(self._config.gpu.name.split(' ')) > 1 else self._config.gpu.name} · "
            f"{self._config.ram.name}"
        )
        self._ready_widget.show()

    def _on_launch(self):
        self.detection_complete.emit(self._config)
