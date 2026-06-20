"""
SystemMonitor — Collecte temps réel des métriques système.
Utilise psutil + WMI + pywin32 pour des données précises.
"""

import threading
import time
import logging
from dataclasses import dataclass, field
from typing import Callable, Optional
from collections import deque

import psutil

logger = logging.getLogger(__name__)

# WMI optionnel (Windows uniquement)
try:
    import wmi
    WMI_AVAILABLE = True
except ImportError:
    WMI_AVAILABLE = False
    logger.warning("WMI non disponible — températures GPU désactivées")


@dataclass
class SystemSnapshot:
    """Snapshot complet des métriques système à un instant T."""
    timestamp: float = 0.0

    # CPU
    cpu_percent: float = 0.0
    cpu_freq_mhz: float = 0.0
    cpu_temp_c: float = 0.0
    cpu_cores: int = 0
    cpu_threads: int = 0
    cpu_name: str = ""

    # RAM
    ram_total_gb: float = 0.0
    ram_used_gb: float = 0.0
    ram_percent: float = 0.0
    ram_available_gb: float = 0.0

    # GPU (via WMI/nvml)
    gpu_name: str = "N/A"
    gpu_load_percent: float = 0.0
    gpu_temp_c: float = 0.0
    gpu_vram_used_gb: float = 0.0
    gpu_vram_total_gb: float = 0.0

    # Disque
    disk_total_gb: float = 0.0
    disk_used_gb: float = 0.0
    disk_percent: float = 0.0
    disk_read_mbps: float = 0.0
    disk_write_mbps: float = 0.0

    # Réseau
    net_sent_mbps: float = 0.0
    net_recv_mbps: float = 0.0
    ping_ms: float = 0.0

    # Score santé global (0-100)
    health_score: int = 100


@dataclass
class HistoricalData:
    """Historique glissant des métriques pour les graphiques."""
    maxlen: int = 60  # 60 secondes d'historique

    cpu: deque = field(default_factory=lambda: deque(maxlen=60))
    ram: deque = field(default_factory=lambda: deque(maxlen=60))
    gpu: deque = field(default_factory=lambda: deque(maxlen=60))
    gpu_temp: deque = field(default_factory=lambda: deque(maxlen=60))
    cpu_temp: deque = field(default_factory=lambda: deque(maxlen=60))
    ping: deque = field(default_factory=lambda: deque(maxlen=60))
    net_recv: deque = field(default_factory=lambda: deque(maxlen=60))


class SystemMonitor:
    """
    Moniteur système temps réel.
    Collecte les métriques toutes les secondes dans un thread dédié.
    """

    def __init__(self, interval_sec: float = 1.0):
        self.interval = interval_sec
        self._running = False
        self._thread: Optional[threading.Thread] = None
        self._lock = threading.Lock()

        self.snapshot = SystemSnapshot()
        self.history = HistoricalData()
        self._callbacks: list[Callable[[SystemSnapshot], None]] = []

        # État pour calcul delta I/O
        self._prev_disk_io = None
        self._prev_net_io = None
        self._prev_time = None

        # WMI pour GPU/températures
        self._wmi: Optional[object] = None
        if WMI_AVAILABLE:
            try:
                self._wmi = wmi.WMI(namespace="root\\OpenHardwareMonitor")
            except Exception:
                try:
                    self._wmi = wmi.WMI()
                except Exception:
                    self._wmi = None

        # Infos statiques CPU
        self._init_static_info()

    def _init_static_info(self):
        """Collecte les infos statiques une seule fois au démarrage."""
        try:
            info = psutil.cpu_count(logical=False)
            self.snapshot.cpu_cores = info or 1
            self.snapshot.cpu_threads = psutil.cpu_count(logical=True) or 1

            # Nom CPU via WMI ou registre
            if WMI_AVAILABLE:
                try:
                    c = wmi.WMI()
                    for cpu in c.Win32_Processor():
                        self.snapshot.cpu_name = cpu.Name.strip()
                        break
                except Exception:
                    pass

            # RAM totale
            mem = psutil.virtual_memory()
            self.snapshot.ram_total_gb = round(mem.total / (1024**3), 1)

            # Disque C:
            disk = psutil.disk_usage("C:\\")
            self.snapshot.disk_total_gb = round(disk.total / (1024**3), 1)

        except Exception as e:
            logger.error(f"Erreur init statique: {e}")

    def register_callback(self, cb: Callable[[SystemSnapshot], None]):
        """Enregistre un callback appelé à chaque nouvelle mesure."""
        self._callbacks.append(cb)

    def start(self):
        """Démarre la collecte en arrière-plan."""
        if self._running:
            return
        self._running = True
        self._thread = threading.Thread(target=self._loop, daemon=True, name="SystemMonitor")
        self._thread.start()
        logger.info("SystemMonitor démarré")

    def stop(self):
        """Arrête la collecte."""
        self._running = False
        if self._thread:
            self._thread.join(timeout=3)
        logger.info("SystemMonitor arrêté")

    def _loop(self):
        """Boucle principale de collecte."""
        try:
            import pythoncom
            pythoncom.CoInitialize()
            _com_initialized = True
        except Exception:
            _com_initialized = False

        while self._running:
            try:
                snap = self._collect()
                with self._lock:
                    self.snapshot = snap
                    self._update_history(snap)
                for cb in self._callbacks:
                    try:
                        cb(snap)
                    except Exception as e:
                        logger.error(f"Erreur callback: {e}")
            except Exception as e:
                logger.error(f"Erreur collecte: {e}")
            time.sleep(self.interval)

        if _com_initialized:
            try:
                import pythoncom
                pythoncom.CoUninitialize()
            except Exception:
                pass

    def _collect(self) -> SystemSnapshot:
        """Collecte toutes les métriques système."""
        now = time.time()
        snap = SystemSnapshot(timestamp=now)

        # ── CPU ──────────────────────────────────────────────────────
        snap.cpu_percent = psutil.cpu_percent(interval=None)
        snap.cpu_cores = self.snapshot.cpu_cores
        snap.cpu_threads = self.snapshot.cpu_threads
        snap.cpu_name = self.snapshot.cpu_name

        freq = psutil.cpu_freq()
        if freq:
            snap.cpu_freq_mhz = round(freq.current, 0)

        snap.cpu_temp_c = self._get_cpu_temp()

        # ── RAM ──────────────────────────────────────────────────────
        mem = psutil.virtual_memory()
        snap.ram_total_gb = self.snapshot.ram_total_gb
        snap.ram_used_gb = round(mem.used / (1024**3), 2)
        snap.ram_available_gb = round(mem.available / (1024**3), 2)
        snap.ram_percent = mem.percent

        # ── GPU ──────────────────────────────────────────────────────
        gpu_data = self._get_gpu_data()
        snap.gpu_name = gpu_data.get("name", "N/A")
        snap.gpu_load_percent = gpu_data.get("load", 0.0)
        snap.gpu_temp_c = gpu_data.get("temp", 0.0)
        snap.gpu_vram_used_gb = gpu_data.get("vram_used", 0.0)
        snap.gpu_vram_total_gb = gpu_data.get("vram_total", 0.0)

        # ── DISQUE ───────────────────────────────────────────────────
        try:
            disk = psutil.disk_usage("C:\\")
            snap.disk_total_gb = self.snapshot.disk_total_gb
            snap.disk_used_gb = round(disk.used / (1024**3), 1)
            snap.disk_percent = disk.percent

            disk_io = psutil.disk_io_counters()
            if disk_io and self._prev_disk_io and self._prev_time:
                dt = now - self._prev_time
                snap.disk_read_mbps = round(
                    (disk_io.read_bytes - self._prev_disk_io.read_bytes) / (dt * 1024**2), 2
                )
                snap.disk_write_mbps = round(
                    (disk_io.write_bytes - self._prev_disk_io.write_bytes) / (dt * 1024**2), 2
                )
            self._prev_disk_io = disk_io
        except Exception:
            pass

        # ── RÉSEAU ───────────────────────────────────────────────────
        try:
            net_io = psutil.net_io_counters()
            if net_io and self._prev_net_io and self._prev_time:
                dt = now - self._prev_time
                snap.net_sent_mbps = round(
                    (net_io.bytes_sent - self._prev_net_io.bytes_sent) / (dt * 1024**2), 2
                )
                snap.net_recv_mbps = round(
                    (net_io.bytes_recv - self._prev_net_io.bytes_recv) / (dt * 1024**2), 2
                )
            self._prev_net_io = net_io
        except Exception:
            pass

        self._prev_time = now

        # ── SCORE SANTÉ ──────────────────────────────────────────────
        snap.health_score = self._compute_health(snap)

        return snap

    def _get_cpu_temp(self) -> float:
        """Récupère la température CPU via WMI/OpenHardwareMonitor."""
        try:
            if self._wmi:
                sensors = self._wmi.Sensor()
                for s in sensors:
                    if s.SensorType == "Temperature" and "CPU" in s.Name:
                        return round(float(s.Value), 1)
        except Exception:
            pass

        # Fallback psutil (Linux/certains Windows)
        try:
            temps = psutil.sensors_temperatures()
            if temps:
                for key in ("coretemp", "k10temp", "cpu_thermal"):
                    if key in temps:
                        entries = temps[key]
                        if entries:
                            return round(entries[0].current, 1)
        except Exception:
            pass

        return 0.0

    def _get_gpu_data(self) -> dict:
        """Récupère les données GPU via WMI/OpenHardwareMonitor ou nvidia-smi."""
        result = {"name": "N/A", "load": 0.0, "temp": 0.0, "vram_used": 0.0, "vram_total": 0.0}

        # Essai via WMI OpenHardwareMonitor
        try:
            if self._wmi:
                sensors = self._wmi.Sensor()
                for s in sensors:
                    if s.SensorType == "Load" and "GPU" in s.Name:
                        result["load"] = round(float(s.Value), 1)
                    elif s.SensorType == "Temperature" and "GPU" in s.Name:
                        result["temp"] = round(float(s.Value), 1)
        except Exception:
            pass

        # Nom GPU via Win32
        try:
            if WMI_AVAILABLE:
                c = wmi.WMI()
                for gpu in c.Win32_VideoController():
                    result["name"] = gpu.Name
                    ram = getattr(gpu, "AdapterRAM", 0) or 0
                    result["vram_total"] = round(ram / (1024**3), 1)
                    break
        except Exception:
            pass

        return result

    def _compute_health(self, snap: SystemSnapshot) -> int:
        """
        Calcule un score de santé système de 0 à 100.
        Basé sur : CPU charge, RAM utilisation, températures, disque.
        """
        score = 100
        penalties = []

        if snap.cpu_percent > 90:
            penalties.append(20)
        elif snap.cpu_percent > 75:
            penalties.append(10)

        if snap.ram_percent > 90:
            penalties.append(20)
        elif snap.ram_percent > 75:
            penalties.append(10)

        if snap.cpu_temp_c > 90:
            penalties.append(25)
        elif snap.cpu_temp_c > 80:
            penalties.append(15)
        elif snap.cpu_temp_c > 70:
            penalties.append(5)

        if snap.gpu_temp_c > 90:
            penalties.append(20)
        elif snap.gpu_temp_c > 80:
            penalties.append(10)

        if snap.disk_percent > 95:
            penalties.append(15)
        elif snap.disk_percent > 85:
            penalties.append(5)

        score = max(0, score - sum(penalties))
        return score

    def _update_history(self, snap: SystemSnapshot):
        """Met à jour les deques d'historique."""
        self.history.cpu.append(snap.cpu_percent)
        self.history.ram.append(snap.ram_percent)
        self.history.gpu.append(snap.gpu_load_percent)
        self.history.gpu_temp.append(snap.gpu_temp_c)
        self.history.cpu_temp.append(snap.cpu_temp_c)
        self.history.net_recv.append(snap.net_recv_mbps)

    def get_snapshot(self) -> SystemSnapshot:
        """Retourne le dernier snapshot thread-safe."""
        with self._lock:
            return self.snapshot

    def get_history(self) -> HistoricalData:
        """Retourne l'historique thread-safe."""
        with self._lock:
            return self.history
