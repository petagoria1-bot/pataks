"""
BoostPage — Page principale "Booster mon PC".
12 optimisations réelles appliquées sur la config détectée.
C'est la page HOME de l'application — visible en premier.
"""

from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel,
    QPushButton, QScrollArea, QFrame, QSizePolicy
)
from PyQt6.QtCore import Qt, QThread, pyqtSignal, QTimer
from PyQt6.QtGui import QColor, QFont, QPainter, QLinearGradient, QPainterPath, QBrush, QPen

from ui.theme import Colors, Typography, Spacing
from ui.components.widgets import GlassCard, SectionHeader, StatusBadge
from core.gaming_optimizer import GamingOptimizer, OptimizationReport, OptimizationStatus


class BoostWorker(QThread):
    progress = pyqtSignal(int, int, str)
    finished = pyqtSignal(object)

    def run(self):
        optimizer = GamingOptimizer(
            progress_callback=lambda s, t, m: self.progress.emit(s, t, m)
        )
        report = optimizer.optimize_all()
        self.finished.emit(report)


class RestoreWorker(QThread):
    finished = pyqtSignal(object)

    def run(self):
        optimizer = GamingOptimizer()
        report = optimizer.restore_defaults()
        self.finished.emit(report)


class _HeroButton(QPushButton):
    """Bouton principal BOOSTER MON PC avec effet glow."""

    def __init__(self, text: str, parent=None):
        super().__init__(text, parent)
        self._hover = False
        self.setFixedHeight(56)
        self.setCursor(Qt.CursorShape.PointingHandCursor)
        self.setFont(Typography.font("Inter", 13, QFont.Weight.Bold))

    def enterEvent(self, e):
        self._hover = True
        self.update()

    def leaveEvent(self, e):
        self._hover = False
        self.update()

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        rect = self.rect()

        path = QPainterPath()
        path.addRoundedRect(0, 0, rect.width(), rect.height(), 8, 8)

        if not self.isEnabled():
            painter.fillPath(path, QColor(Colors.CRIMSON_DARK))
        else:
            grad = QLinearGradient(0, 0, 0, rect.height())
            grad.setColorAt(0, QColor("#FF4444" if self._hover else Colors.CRIMSON_GLOW))
            grad.setColorAt(1, QColor(Colors.CRIMSON_GLOW if self._hover else Colors.CRIMSON))
            painter.fillPath(path, QBrush(grad))

        if self._hover and self.isEnabled():
            glow = QColor(Colors.CRIMSON)
            glow.setAlpha(60)
            painter.setPen(QPen(glow, 2))
            painter.drawPath(path)

        painter.setPen(QColor("white"))
        painter.setFont(self.font())
        painter.drawText(rect, Qt.AlignmentFlag.AlignCenter, self.text())


class _ResultRow(QWidget):
    """Ligne résultat d'une optimisation."""

    STATUS_CFG = {
        OptimizationStatus.SUCCESS: ("✓", Colors.SUCCESS,  "#0A1A10"),
        OptimizationStatus.FAILED:  ("✕", Colors.DANGER,   "#1A0505"),
        OptimizationStatus.SKIPPED: ("—", Colors.SILVER_DIM, Colors.BG_ELEVATED),
    }

    def __init__(self, name: str, status: OptimizationStatus, message: str, parent=None):
        super().__init__(parent)
        icon, color, bg = self.STATUS_CFG.get(
            status, ("?", Colors.SILVER_DIM, Colors.BG_ELEVATED)
        )

        layout = QHBoxLayout(self)
        layout.setContentsMargins(12, 8, 12, 8)
        layout.setSpacing(10)

        lbl_icon = QLabel(icon)
        lbl_icon.setFixedWidth(18)
        lbl_icon.setFont(Typography.heading(13))
        lbl_icon.setStyleSheet(f"color: {color}; background: transparent;")
        lbl_icon.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(lbl_icon)

        lbl_name = QLabel(name)
        lbl_name.setFont(Typography.body(11))
        lbl_name.setStyleSheet(f"color: {Colors.SILVER}; background: transparent; font-weight: 600;")
        layout.addWidget(lbl_name, 1)

        lbl_msg = QLabel(message)
        lbl_msg.setFont(Typography.body(10))
        lbl_msg.setStyleSheet(f"color: {Colors.SILVER_DIM}; background: transparent;")
        layout.addWidget(lbl_msg)

        self.setStyleSheet(f"background: transparent;")
        self.setProperty("bg", bg)


class _ProgressWidget(QWidget):
    """Barre de progression avec label."""

    def __init__(self, parent=None):
        super().__init__(parent)
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 8, 0, 0)
        layout.setSpacing(6)

        self.lbl = QLabel("Prêt")
        self.lbl.setFont(Typography.body(10))
        self.lbl.setStyleSheet(f"color: {Colors.SILVER_DIM}; background: transparent;")
        layout.addWidget(self.lbl)

        self._bar = _BarPaint()
        self._bar.setFixedHeight(5)
        layout.addWidget(self._bar)

    def set(self, pct: int, text: str):
        self.lbl.setText(text)
        self._bar.set_value(pct)


class _BarPaint(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self._value = 0.0
        self._anim = 0.0
        QTimer(self, timeout=self._tick, interval=16).start()

    def set_value(self, v):
        self._value = v

    def _tick(self):
        diff = self._value - self._anim
        if abs(diff) > 0.2:
            self._anim += diff * 0.14
            self.update()

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        W, H = self.width(), self.height()
        painter.setPen(Qt.PenStyle.NoPen)
        painter.setBrush(QColor(Colors.BG_ELEVATED))
        painter.drawRoundedRect(0, 0, W, H, 2, 2)
        fw = int(W * self._anim / 100)
        if fw > 0:
            g = QLinearGradient(0, 0, fw, 0)
            g.setColorAt(0, QColor(Colors.CRIMSON_DARK))
            g.setColorAt(1, QColor(Colors.CRIMSON_GLOW))
            painter.setBrush(QBrush(g))
            painter.drawRoundedRect(0, 0, fw, H, 2, 2)


class BoostPage(QWidget):
    """Page Booster mon PC — vue principale de PATAKS."""

    def __init__(self, system_config=None, parent=None):
        super().__init__(parent)
        self._config = system_config
        self._worker = None
        self._build_ui()

    def update_config(self, config):
        """Met à jour la page avec la config détectée."""
        self._config = config
        if config:
            self._lbl_gpu_tag.setText(f"🎮 {config.gpu.name[:30]}")
            self._lbl_cpu_tag.setText(f"🖥 {config.cpu.name.split('@')[0].strip()[:30]}")
            self._lbl_ram_tag.setText(f"💾 {config.ram.name}")

    def _build_ui(self):
        root = QVBoxLayout(self)
        root.setContentsMargins(Spacing.XL, Spacing.XL, Spacing.XL, Spacing.XL)
        root.setSpacing(Spacing.LG)

        # Header
        hrow = QHBoxLayout()
        hrow.addWidget(SectionHeader("Booster mon PC", "Optimisation Gaming 1-clic"))
        hrow.addStretch()
        self._badge = StatusBadge("EN ATTENTE", "info")
        hrow.addWidget(self._badge)
        root.addLayout(hrow)

        # ── Carte Hero ────────────────────────────────────────────────
        hero = GlassCard(glow_color=Colors.CRIMSON)
        hero_l = hero.layout()

        # Top row : icône + titre + desc
        top = QHBoxLayout()
        top.setSpacing(16)

        icon_wrap = QWidget()
        icon_wrap.setFixedSize(70, 70)
        icon_wrap.setStyleSheet(f"""
            background: radial-gradient(circle, rgba(224,32,32,0.25), rgba(224,32,32,0.05));
            border: 2px solid rgba(224,32,32,0.4);
            border-radius: 35px;
        """)
        icon_l = QVBoxLayout(icon_wrap)
        icon_l.setContentsMargins(0, 0, 0, 0)
        lbl_icon = QLabel("⚡")
        lbl_icon.setFont(QFont("Segoe UI Emoji", 24))
        lbl_icon.setAlignment(Qt.AlignmentFlag.AlignCenter)
        lbl_icon.setStyleSheet("background: transparent;")
        icon_l.addWidget(lbl_icon)
        top.addWidget(icon_wrap)

        title_col = QVBoxLayout()
        title_col.setSpacing(4)
        lbl_title = QLabel("MODE GAMING ULTIME")
        lbl_title.setFont(Typography.font("Rajdhani", 24, QFont.Weight.Bold))
        lbl_title.setStyleSheet(f"color: {Colors.SILVER_BRIGHT}; background: transparent;")
        title_col.addWidget(lbl_title)

        lbl_desc = QLabel(
            "12 optimisations réelles et mesurables appliquées sur votre configuration :\n"
            "Plan énergie Ultimate Performance · Services inutiles Windows · Réseau TCP/IP gaming\n"
            "Input lag souris · GPU Hardware Scheduling · Timer 1ms · Algorithme Nagle désactivé..."
        )
        lbl_desc.setFont(Typography.body(10))
        lbl_desc.setStyleSheet(f"color: {Colors.SILVER_DIM}; background: transparent;")
        lbl_desc.setWordWrap(True)
        title_col.addWidget(lbl_desc)
        top.addLayout(title_col, 1)
        hero_l.addLayout(top)

        # Tags optimisations
        tags_row = QHBoxLayout()
        tags_row.setSpacing(8)
        tags = [
            ("⚡ Plan énergie", Colors.CRIMSON, Colors.CRIMSON_DIM),
            ("🔧 Services", Colors.SILVER_DIM, Colors.BG_ELEVATED),
            ("🌐 TCP/IP", Colors.SILVER_DIM, Colors.BG_ELEVATED),
            ("🖱 Input lag", Colors.SILVER_DIM, Colors.BG_ELEVATED),
            ("🎮 GPU HAGS", Colors.SILVER_DIM, Colors.BG_ELEVATED),
            ("⏱ Timer 1ms", Colors.SILVER_DIM, Colors.BG_ELEVATED),
        ]
        for tag_txt, color, bg in tags:
            t = QLabel(tag_txt)
            t.setFont(Typography.label(8))
            t.setStyleSheet(f"""
                color: {color};
                background: {bg};
                border: 1px solid {color}30;
                border-radius: 5px;
                padding: 3px 8px;
            """)
            tags_row.addWidget(t)
        tags_row.addStretch()
        hero_l.addLayout(tags_row)

        # Composants détectés (mis à jour après détection)
        config_row = QHBoxLayout()
        config_row.setSpacing(8)
        self._lbl_cpu_tag = QLabel("🖥 CPU : détection requise")
        self._lbl_gpu_tag = QLabel("🎮 GPU : détection requise")
        self._lbl_ram_tag = QLabel("💾 RAM : détection requise")
        for lbl in [self._lbl_cpu_tag, self._lbl_gpu_tag, self._lbl_ram_tag]:
            lbl.setFont(Typography.body(9))
            lbl.setStyleSheet(f"color: {Colors.SILVER_DIM}; background: transparent;")
            config_row.addWidget(lbl)
        config_row.addStretch()
        hero_l.addLayout(config_row)

        # Boutons
        btns = QHBoxLayout()
        btns.setSpacing(10)
        self._btn_boost = _HeroButton("⚡  BOOSTER MON PC MAINTENANT")
        self._btn_boost.clicked.connect(self._run_boost)
        btns.addWidget(self._btn_boost, 1)

        btn_restore = QPushButton("↺  Restaurer les défauts")
        btn_restore.setFixedHeight(56)
        btn_restore.setFixedWidth(200)
        btn_restore.setFont(Typography.body(11))
        btn_restore.setCursor(Qt.CursorShape.PointingHandCursor)
        btn_restore.setStyleSheet(f"""
            QPushButton {{
                background: {Colors.BG_ELEVATED};
                color: {Colors.SILVER_DIM};
                border: 1px solid {Colors.SILVER_GHOST};
                border-radius: 8px;
            }}
            QPushButton:hover {{
                border-color: {Colors.SILVER_DIM};
                color: {Colors.SILVER};
            }}
        """)
        btn_restore.clicked.connect(self._run_restore)
        btns.addWidget(btn_restore)
        hero_l.addLayout(btns)

        # Progress
        self._progress = _ProgressWidget()
        self._progress.hide()
        hero_l.addWidget(self._progress)

        root.addWidget(hero)

        # ── Sécurité notice ───────────────────────────────────────────
        notice = QWidget()
        notice.setStyleSheet(f"""
            background: {Colors.BG_ELEVATED};
            border: 1px solid {Colors.SILVER_GHOST};
            border-radius: 8px;
        """)
        notice_l = QHBoxLayout(notice)
        notice_l.setContentsMargins(14, 10, 14, 10)
        notice_l.setSpacing(10)
        lbl_lock = QLabel("🔒")
        lbl_lock.setFont(QFont("Segoe UI Emoji", 14))
        lbl_lock.setStyleSheet("background: transparent;")
        notice_l.addWidget(lbl_lock)
        lbl_notice = QLabel(
            "<b style='color:#C4CDD8;'>Sécurité garantie.</b> "
            "Un point de restauration système et une sauvegarde complète du registre Windows "
            "sont créés automatiquement avant chaque optimisation. Tout est 100% réversible."
        )
        lbl_notice.setFont(Typography.body(9))
        lbl_notice.setStyleSheet(f"color: {Colors.SILVER_DIM}; background: transparent;")
        lbl_notice.setWordWrap(True)
        lbl_notice.setOpenExternalLinks(False)
        notice_l.addWidget(lbl_notice, 1)
        root.addWidget(notice)

        # ── Résultats ─────────────────────────────────────────────────
        res_header = QHBoxLayout()
        res_header.addWidget(SectionHeader("Résultats", "Détail de chaque optimisation"))
        self._lbl_summary = QLabel("")
        self._lbl_summary.setFont(Typography.body(10))
        self._lbl_summary.setStyleSheet(f"color: {Colors.SUCCESS}; background: transparent;")
        res_header.addWidget(self._lbl_summary)
        res_header.addStretch()
        root.addLayout(res_header)

        # Scroll résultats
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setStyleSheet("QScrollArea { border: none; background: transparent; }")

        self._results_container = QWidget()
        self._results_container.setStyleSheet(f"""
            background: {Colors.BG_SURFACE};
            border: 1px solid {Colors.SILVER_GHOST};
            border-radius: 10px;
        """)
        self._results_layout = QVBoxLayout(self._results_container)
        self._results_layout.setContentsMargins(0, 4, 0, 4)
        self._results_layout.setSpacing(0)

        lbl_empty = QLabel("  Cliquez sur « BOOSTER MON PC » pour lancer les optimisations.")
        lbl_empty.setFont(Typography.body(10))
        lbl_empty.setStyleSheet(f"color: {Colors.SILVER_GHOST}; padding: 16px;")
        self._results_layout.addWidget(lbl_empty)
        self._results_layout.addStretch()

        scroll.setWidget(self._results_container)
        root.addWidget(scroll, 1)

    def _run_boost(self):
        self._btn_boost.setEnabled(False)
        self._btn_boost.setText("  ◌  OPTIMISATION EN COURS...")
        self._progress.show()
        self._lbl_summary.setText("")
        self._badge.set_status("warning")
        self._badge.setText("EN COURS")
        self._clear_results()

        self._worker = BoostWorker()
        self._worker.progress.connect(self._on_progress)
        self._worker.finished.connect(self._on_done)
        self._worker.start()

    def _run_restore(self):
        self._btn_boost.setEnabled(False)
        self._progress.show()
        self._progress.set(0, "Restauration des paramètres par défaut...")
        self._clear_results()

        self._worker = RestoreWorker()
        self._worker.finished.connect(self._on_restore_done)
        self._worker.start()

    def _on_progress(self, step: int, total: int, msg: str):
        pct = int(step / total * 100) if total > 0 else 0
        self._progress.set(pct, msg)

    def _on_done(self, report: OptimizationReport):
        self._btn_boost.setEnabled(True)
        self._btn_boost.setText("⚡  RE-OPTIMISER")
        self._progress.set(100, f"✓ Terminé — {report.success_count} appliquées · {report.skipped_count} déjà en place")
        self._badge.set_status("ok")
        self._badge.setText("✓ OPTIMISÉ")

        success = report.success_count
        skipped = report.skipped_count
        failed = report.failed_count
        self._lbl_summary.setText(
            f"✓ {success} appliquées  ·  {skipped} déjà en place  ·  {failed} échecs"
        )
        if failed > 0:
            self._lbl_summary.setStyleSheet(f"color: {Colors.WARNING}; background: transparent;")
        else:
            self._lbl_summary.setStyleSheet(f"color: {Colors.SUCCESS}; background: transparent;")

        self._render_results(report)

    def _on_restore_done(self, report: OptimizationReport):
        self._btn_boost.setEnabled(True)
        self._progress.set(100, f"↺ Paramètres Windows restaurés ({report.success_count} éléments)")
        self._badge.set_status("info")
        self._badge.setText("RESTAURÉ")
        self._render_results(report)

    def _render_results(self, report: OptimizationReport):
        self._clear_results()
        for i, result in enumerate(report.results):
            row = _ResultRow(result.name, result.status, result.message)
            self._results_layout.insertWidget(
                self._results_layout.count() - 1, row
            )
            if i < len(report.results) - 1:
                sep = QFrame()
                sep.setFrameShape(QFrame.Shape.HLine)
                sep.setStyleSheet(f"color: {Colors.SILVER_GHOST}; background: {Colors.SILVER_GHOST};")
                sep.setFixedHeight(1)
                self._results_layout.insertWidget(self._results_layout.count() - 1, sep)

    def _clear_results(self):
        while self._results_layout.count() > 1:
            item = self._results_layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()
