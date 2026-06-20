"""
SettingsPage — Paramètres de PATAKS.
Lancement au démarrage, DNS gaming, intervalle monitor,
thème, reset complet.
"""

import logging
import winreg
import subprocess
from pathlib import Path

from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel,
    QPushButton, QScrollArea, QFrame, QCheckBox,
    QComboBox, QSlider, QSpinBox
)
from PyQt6.QtCore import Qt, QTimer
from PyQt6.QtGui import QColor, QFont

from ui.theme import Colors, Typography, Spacing
from ui.components.widgets import GlassCard, SectionHeader, StatusBadge

logger = logging.getLogger(__name__)

PATAKS_REG_KEY = r"SOFTWARE\Microsoft\Windows\CurrentVersion\Run"
PATAKS_APP_NAME = "PATAKS"


class _Toggle(QCheckBox):
    """Checkbox stylisée comme un toggle switch."""

    def __init__(self, label: str = "", parent=None):
        super().__init__(label, parent)
        self.setStyleSheet(f"""
            QCheckBox {{
                color: {Colors.SILVER};
                font-size: 11px;
                spacing: 10px;
            }}
            QCheckBox::indicator {{
                width: 36px; height: 18px;
                border-radius: 9px;
                border: 1px solid {Colors.SILVER_GHOST};
                background: {Colors.BG_ELEVATED};
            }}
            QCheckBox::indicator:checked {{
                background: {Colors.CRIMSON};
                border-color: {Colors.CRIMSON};
            }}
            QCheckBox::indicator:hover {{
                border-color: {Colors.SILVER_DIM};
            }}
        """)


class _SettingRow(QWidget):
    """Ligne paramètre avec label, description et contrôle."""

    def __init__(self, title: str, description: str, control: QWidget, parent=None):
        super().__init__(parent)
        layout = QHBoxLayout(self)
        layout.setContentsMargins(0, 8, 0, 8)
        layout.setSpacing(16)

        text_col = QVBoxLayout()
        text_col.setSpacing(3)
        lbl_title = QLabel(title)
        lbl_title.setFont(Typography.heading(11))
        lbl_title.setStyleSheet(f"color: {Colors.SILVER}; background: transparent;")
        lbl_desc = QLabel(description)
        lbl_desc.setFont(Typography.body(9))
        lbl_desc.setStyleSheet(f"color: {Colors.SILVER_DIM}; background: transparent;")
        text_col.addWidget(lbl_title)
        text_col.addWidget(lbl_desc)
        layout.addLayout(text_col, 1)
        layout.addWidget(control)

        self.setStyleSheet("background: transparent;")


def _sep():
    """Ligne séparatrice."""
    f = QFrame()
    f.setFrameShape(QFrame.Shape.HLine)
    f.setStyleSheet(f"color: {Colors.SILVER_GHOST}; background: {Colors.SILVER_GHOST};")
    f.setFixedHeight(1)
    return f


class SettingsPage(QWidget):
    """Page paramètres complète."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self._build_ui()
        QTimer.singleShot(100, self._load_settings)

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
        layout.addWidget(SectionHeader("Paramètres", "Configuration de PATAKS"))

        # ── SYSTÈME ──────────────────────────────────────────────────
        sys_card = GlassCard()
        sys_l = sys_card.layout()
        sys_l.setSpacing(2)

        lbl_sys = QLabel("SYSTÈME")
        lbl_sys.setFont(Typography.label(8))
        lbl_sys.setStyleSheet(f"color: {Colors.SILVER_DIM}; background: transparent; letter-spacing: 2px;")
        sys_l.addWidget(lbl_sys)
        sys_l.addWidget(_sep())

        # Lancement au démarrage
        self._toggle_startup = _Toggle()
        self._toggle_startup.stateChanged.connect(self._on_startup_changed)
        sys_l.addWidget(_SettingRow(
            "Lancer au démarrage de Windows",
            "PATAKS démarre automatiquement avec Windows (clé registre Run)",
            self._toggle_startup
        ))
        sys_l.addWidget(_sep())

        # Minimiser dans la barre système
        self._toggle_tray = _Toggle()
        self._toggle_tray.setChecked(True)
        sys_l.addWidget(_SettingRow(
            "Minimiser dans la barre système",
            "La fermeture de la fenêtre réduit PATAKS dans le systray",
            self._toggle_tray
        ))
        sys_l.addWidget(_sep())

        # Intervalle de monitoring
        self._spin_interval = QSpinBox()
        self._spin_interval.setRange(1, 5)
        self._spin_interval.setValue(1)
        self._spin_interval.setSuffix(" sec")
        self._spin_interval.setStyleSheet(f"""
            QSpinBox {{
                background: {Colors.BG_ELEVATED};
                color: {Colors.SILVER};
                border: 1px solid {Colors.SILVER_GHOST};
                border-radius: 5px;
                padding: 4px 8px;
                font-size: 11px;
                min-width: 80px;
            }}
        """)
        sys_l.addWidget(_SettingRow(
            "Intervalle de monitoring",
            "Fréquence de collecte des métriques système (1-5 secondes)",
            self._spin_interval
        ))

        layout.addWidget(sys_card)

        # ── RÉSEAU GAMING ─────────────────────────────────────────────
        net_card = GlassCard()
        net_l = net_card.layout()
        net_l.setSpacing(2)

        lbl_net = QLabel("RÉSEAU GAMING")
        lbl_net.setFont(Typography.label(8))
        lbl_net.setStyleSheet(f"color: {Colors.SILVER_DIM}; background: transparent; letter-spacing: 2px;")
        net_l.addWidget(lbl_net)
        net_l.addWidget(_sep())

        # DNS gaming
        self._combo_dns = QComboBox()
        self._combo_dns.addItems([
            "Cloudflare Gaming (1.1.1.1 / 1.0.0.1)",
            "Google (8.8.8.8 / 8.8.4.4)",
            "OpenDNS (208.67.222.222)",
            "DNS automatique (DHCP)",
        ])
        self._combo_dns.setStyleSheet(f"""
            QComboBox {{
                background: {Colors.BG_ELEVATED};
                color: {Colors.SILVER};
                border: 1px solid {Colors.SILVER_GHOST};
                border-radius: 5px;
                padding: 4px 10px;
                font-size: 10px;
                min-width: 260px;
            }}
            QComboBox::drop-down {{ border: none; width: 20px; }}
            QComboBox QAbstractItemView {{
                background: {Colors.BG_ELEVATED};
                color: {Colors.SILVER};
                border: 1px solid {Colors.SILVER_GHOST};
                selection-background-color: {Colors.CRIMSON_DIM};
            }}
        """)
        net_l.addWidget(_SettingRow(
            "DNS Gaming",
            "Serveur DNS optimisé pour réduire la latence réseau en jeu",
            self._combo_dns
        ))
        net_l.addWidget(_sep())

        # Bouton appliquer DNS
        btn_apply_dns = QPushButton("Appliquer le DNS sélectionné")
        btn_apply_dns.setFixedHeight(34)
        btn_apply_dns.setFont(Typography.body(10))
        btn_apply_dns.setCursor(Qt.CursorShape.PointingHandCursor)
        btn_apply_dns.setStyleSheet(f"""
            QPushButton {{
                background: {Colors.BG_ELEVATED};
                color: {Colors.SILVER};
                border: 1px solid {Colors.SILVER_GHOST};
                border-radius: 6px;
                padding: 0 14px;
            }}
            QPushButton:hover {{
                border-color: {Colors.CRIMSON};
                color: {Colors.CRIMSON};
                background: {Colors.CRIMSON_DIM};
            }}
        """)
        btn_apply_dns.clicked.connect(self._apply_dns)
        net_l.addWidget(btn_apply_dns)

        layout.addWidget(net_card)

        # ── OPTIMISATIONS AUTO ─────────────────────────────────────────
        opt_card = GlassCard()
        opt_l = opt_card.layout()
        opt_l.setSpacing(2)

        lbl_opt = QLabel("OPTIMISATIONS AUTOMATIQUES")
        lbl_opt.setFont(Typography.label(8))
        lbl_opt.setStyleSheet(f"color: {Colors.SILVER_DIM}; background: transparent; letter-spacing: 2px;")
        opt_l.addWidget(lbl_opt)
        opt_l.addWidget(_sep())

        self._toggle_auto_boost = _Toggle()
        opt_l.addWidget(_SettingRow(
            "Boost automatique au lancement",
            "Applique le Mode Gaming dès l'ouverture de PATAKS",
            self._toggle_auto_boost
        ))
        opt_l.addWidget(_sep())

        self._toggle_detect_games = _Toggle()
        self._toggle_detect_games.setChecked(True)
        opt_l.addWidget(_SettingRow(
            "Détection des jeux actifs",
            "Priorité CPU élevée automatiquement quand Fortnite, CS2, Valorant... sont détectés",
            self._toggle_detect_games
        ))

        layout.addWidget(opt_card)

        # ── DANGER ZONE ────────────────────────────────────────────────
        danger_card = GlassCard(glow_color=Colors.DANGER)
        danger_card.setStyleSheet(f"""
            background: rgba(61,10,10,0.2);
            border: 1px solid rgba(224,32,32,0.2);
            border-radius: 10px;
        """)
        danger_l = danger_card.layout()

        lbl_danger = QLabel("ZONE DE DANGER")
        lbl_danger.setFont(Typography.label(8))
        lbl_danger.setStyleSheet(f"color: {Colors.DANGER}; background: transparent; letter-spacing: 2px;")
        danger_l.addWidget(lbl_danger)

        btn_reset = QPushButton("↺ Réinitialiser tous les paramètres Windows")
        btn_reset.setFixedHeight(40)
        btn_reset.setFont(Typography.body(11))
        btn_reset.setCursor(Qt.CursorShape.PointingHandCursor)
        btn_reset.setStyleSheet(f"""
            QPushButton {{
                background: transparent;
                color: {Colors.DANGER};
                border: 1px solid rgba(224,32,32,0.4);
                border-radius: 6px;
            }}
            QPushButton:hover {{
                background: {Colors.CRIMSON_DIM};
                border-color: {Colors.DANGER};
            }}
        """)
        btn_reset.clicked.connect(self._reset_all)
        danger_l.addWidget(btn_reset)
        layout.addWidget(danger_card)

        # ── Version ───────────────────────────────────────────────────
        lbl_ver = QLabel("PATAKS v2.0.0  ·  by Petagoria  ·  Optimisation Gaming Windows")
        lbl_ver.setFont(Typography.label(8))
        lbl_ver.setStyleSheet(f"color: {Colors.SILVER_GHOST}; background: transparent;")
        lbl_ver.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(lbl_ver)

        layout.addStretch()
        scroll.setWidget(content)
        root.addWidget(scroll)

    def _load_settings(self):
        """Charge les paramètres actuels depuis le registre."""
        # Vérifier si PATAKS est en démarrage auto
        try:
            key = winreg.OpenKey(winreg.HKEY_CURRENT_USER, PATAKS_REG_KEY)
            try:
                winreg.QueryValueEx(key, PATAKS_APP_NAME)
                self._toggle_startup.setChecked(True)
            except FileNotFoundError:
                self._toggle_startup.setChecked(False)
            winreg.CloseKey(key)
        except Exception:
            self._toggle_startup.setChecked(False)

    def _on_startup_changed(self, state: int):
        """Active/désactive le lancement au démarrage."""
        enabled = state == Qt.CheckState.Checked.value
        try:
            key = winreg.OpenKey(
                winreg.HKEY_CURRENT_USER, PATAKS_REG_KEY,
                0, winreg.KEY_SET_VALUE
            )
            if enabled:
                import sys
                exe_path = sys.executable
                winreg.SetValueEx(key, PATAKS_APP_NAME, 0, winreg.REG_SZ,
                                  f'"{exe_path}" "{__file__}"')
            else:
                try:
                    winreg.DeleteValue(key, PATAKS_APP_NAME)
                except FileNotFoundError:
                    pass
            winreg.CloseKey(key)
        except Exception as e:
            logger.error(f"Erreur startup reg: {e}")

    def _apply_dns(self):
        """Applique le DNS sélectionné sur toutes les interfaces actives."""
        dns_map = {
            0: ("1.1.1.1", "1.0.0.1"),
            1: ("8.8.8.8", "8.8.4.4"),
            2: ("208.67.222.222", "208.67.220.220"),
            3: None,
        }
        idx = self._combo_dns.currentIndex()
        dns = dns_map.get(idx)

        try:
            import psutil
            stats = psutil.net_if_stats()
            for iface, st in stats.items():
                if st.isup:
                    if dns:
                        subprocess.run(
                            ["netsh", "interface", "ip", "set", "dns",
                             f'name="{iface}"', "static", dns[0]],
                            capture_output=True, timeout=10
                        )
                        subprocess.run(
                            ["netsh", "interface", "ip", "add", "dns",
                             f'name="{iface}"', dns[1], "index=2"],
                            capture_output=True, timeout=10
                        )
                    else:
                        subprocess.run(
                            ["netsh", "interface", "ip", "set", "dns",
                             f'name="{iface}"', "dhcp"],
                            capture_output=True, timeout=10
                        )
            logger.info(f"DNS appliqué: {dns}")
        except Exception as e:
            logger.error(f"Erreur DNS: {e}")

    def _reset_all(self):
        """Remet tous les paramètres Windows à leur valeur par défaut."""
        from core.gaming_optimizer import GamingOptimizer
        optimizer = GamingOptimizer()
        optimizer.restore_defaults()
        logger.info("Reset complet effectué")
