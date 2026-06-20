"""
Optimize Page — Mode Gaming 1-clic.
Affiche chaque optimisation en temps réel avec son résultat.
"""

from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel,
    QScrollArea, QFrame, QProgressBar, QCheckBox
)
from PyQt6.QtCore import Qt, QThread, pyqtSignal, QTimer
from PyQt6.QtGui import QColor, QFont

from ui.theme import Colors, Typography, Spacing
from ui.components.widgets import GlassCard, GlowButton, SectionHeader, StatusBadge
from core.gaming_optimizer import GamingOptimizer, OptimizationResult, OptimizationStatus


# ─── WORKER ───────────────────────────────────────────────────────────────────

class OptimizationWorker(QThread):
    step_done = pyqtSignal(object)   # OptimizationResult
    progress  = pyqtSignal(int, int, str)
    finished  = pyqtSignal(object)   # OptimizationReport

    def run(self):
        results_live = []
        def progress_cb(step, total, msg):
            self.progress.emit(step, total, msg)

        optimizer = GamingOptimizer(progress_callback=progress_cb)
        report = optimizer.optimize_all()
        self.finished.emit(report)


class RestoreWorker(QThread):
    finished = pyqtSignal(object)

    def run(self):
        optimizer = GamingOptimizer()
        report = optimizer.restore_defaults()
        self.finished.emit(report)


# ─── RESULT ROW ───────────────────────────────────────────────────────────────

class ResultRow(QWidget):
    """Ligne de résultat d'une optimisation."""

    def __init__(self, result: OptimizationResult, parent=None):
        super().__init__(parent)
        layout = QHBoxLayout(self)
        layout.setContentsMargins(Spacing.SM, Spacing.XS, Spacing.SM, Spacing.XS)
        layout.setSpacing(Spacing.SM)

        # Icône statut
        icons = {
            OptimizationStatus.SUCCESS: ("✓", Colors.SUCCESS),
            OptimizationStatus.FAILED:  ("✕", Colors.DANGER),
            OptimizationStatus.SKIPPED: ("—", Colors.SILVER_GHOST),
            OptimizationStatus.RUNNING: ("◌", Colors.WARNING),
        }
        icon, color = icons.get(result.status, ("?", Colors.SILVER_DIM))

        lbl_icon = QLabel(icon)
        lbl_icon.setFixedWidth(20)
        lbl_icon.setFont(Typography.heading(12))
        lbl_icon.setStyleSheet(f"color: {color}; background: transparent;")
        lbl_icon.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(lbl_icon)

        # Nom
        lbl_name = QLabel(result.name)
        lbl_name.setFont(Typography.body(11))
        lbl_name.setStyleSheet(f"color: {Colors.SILVER}; background: transparent;")
        layout.addWidget(lbl_name, 1)

        # Message
        lbl_msg = QLabel(result.message)
        lbl_msg.setFont(Typography.body(10))
        lbl_msg.setStyleSheet(f"color: {Colors.SILVER_DIM}; background: transparent;")
        layout.addWidget(lbl_msg)

        self.setStyleSheet(f"background: transparent;")


# ─── OPTIMIZE PAGE ────────────────────────────────────────────────────────────

class OptimizePage(QWidget):
    """Page d'optimisation gaming 1-clic."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self._worker = None
        self._build_ui()

    def _build_ui(self):
        root = QVBoxLayout(self)
        root.setContentsMargins(Spacing.XL, Spacing.XL, Spacing.XL, Spacing.XL)
        root.setSpacing(Spacing.LG)

        # Header
        header_row = QHBoxLayout()
        header_row.addWidget(SectionHeader("Optimisation Gaming", "Mode 1-clic — 12 optimisations"))
        header_row.addStretch()
        root.addLayout(header_row)

        # Hero card — bouton principal
        hero_card = GlassCard(glow_color=Colors.CRIMSON)
        hero_layout = hero_card.layout()
        hero_layout.setSpacing(Spacing.LG)

        # Titre hero
        hero_title = QLabel("⚡  MODE GAMING ULTIME")
        hero_title.setFont(Typography.display(20))
        hero_title.setStyleSheet(f"color: {Colors.SILVER_BRIGHT}; background: transparent;")
        hero_layout.addWidget(hero_title)

        hero_sub = QLabel(
            "Applique automatiquement 12 optimisations réelles et mesurables :\n"
            "plan Ultimate Performance • services inutiles • réseau TCP/IP • "
            "input lag souris • GPU scheduling • timer résolution • Nagle TCP..."
        )
        hero_sub.setFont(Typography.body(10))
        hero_sub.setStyleSheet(f"color: {Colors.SILVER_DIM}; background: transparent;")
        hero_sub.setWordWrap(True)
        hero_layout.addWidget(hero_sub)

        # Boutons
        btn_row = QHBoxLayout()
        self.btn_optimize = GlowButton("⚡  OPTIMISER MAINTENANT", Colors.CRIMSON)
        self.btn_optimize.setFixedHeight(50)
        self.btn_optimize.clicked.connect(self._start_optimization)

        self.btn_restore = GlowButton("↺  Restaurer les défauts", Colors.SILVER_DIM)
        self.btn_restore.setFixedHeight(50)
        self.btn_restore.setFixedWidth(200)
        self.btn_restore.clicked.connect(self._start_restore)

        btn_row.addWidget(self.btn_optimize, 1)
        btn_row.addWidget(self.btn_restore)
        hero_layout.addLayout(btn_row)

        root.addWidget(hero_card)

        # Progress card
        self.progress_card = GlassCard()
        prog_layout = self.progress_card.layout()

        self.lbl_step = QLabel("Prêt")
        self.lbl_step.setFont(Typography.body(11))
        self.lbl_step.setStyleSheet(f"color: {Colors.SILVER_DIM}; background: transparent;")

        self.progress_bar = QProgressBar()
        self.progress_bar.setFixedHeight(6)
        self.progress_bar.setRange(0, 100)
        self.progress_bar.setTextVisible(False)
        self.progress_bar.setStyleSheet(f"""
            QProgressBar {{ background: {Colors.BG_ELEVATED}; border-radius: 3px; border: none; }}
            QProgressBar::chunk {{
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                    stop:0 {Colors.CRIMSON_DARK}, stop:1 {Colors.CRIMSON_GLOW});
                border-radius: 3px;
            }}
        """)
        prog_layout.addWidget(self.lbl_step)
        prog_layout.addWidget(self.progress_bar)
        self.progress_card.hide()
        root.addWidget(self.progress_card)

        # Summary card (post-optimisation)
        self.summary_card = GlassCard()
        self.summary_card.hide()
        summary_layout = self.summary_card.layout()

        self.lbl_summary = QLabel("")
        self.lbl_summary.setFont(Typography.heading(13))
        self.lbl_summary.setStyleSheet(f"color: {Colors.SUCCESS}; background: transparent;")
        summary_layout.addWidget(self.lbl_summary)

        root.addWidget(self.summary_card)

        # Résultats détaillés
        results_title = SectionHeader("Résultats détaillés", "")
        root.addWidget(results_title)

        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setStyleSheet("QScrollArea { border: none; background: transparent; }")

        self.results_container = QWidget()
        self.results_container.setStyleSheet(f"background: {Colors.BG_SURFACE}; border-radius: 8px;")
        self.results_layout = QVBoxLayout(self.results_container)
        self.results_layout.setContentsMargins(4, 4, 4, 4)
        self.results_layout.setSpacing(2)
        self.results_layout.addStretch()

        scroll.setWidget(self.results_container)
        root.addWidget(scroll, 1)

        # Avertissement sécurité
        warn = QLabel("🔒  Toutes les modifications sont sauvegardées avant application et entièrement réversibles.")
        warn.setFont(Typography.label(9))
        warn.setStyleSheet(f"color: {Colors.SILVER_DIM}; letter-spacing: 0.5px;")
        root.addWidget(warn)

    def _start_optimization(self):
        self.btn_optimize.setEnabled(False)
        self.btn_restore.setEnabled(False)
        self.btn_optimize.setText("  ◌  OPTIMISATION EN COURS...")
        self.progress_card.show()
        self.summary_card.hide()
        self._clear_results()

        self._worker = OptimizationWorker()
        self._worker.progress.connect(self._on_progress)
        self._worker.finished.connect(self._on_finished)
        self._worker.start()

    def _start_restore(self):
        self.btn_optimize.setEnabled(False)
        self.btn_restore.setEnabled(False)
        self.btn_restore.setText("  ◌  Restauration...")
        self.progress_card.show()
        self._clear_results()

        self._worker = RestoreWorker()
        self._worker.finished.connect(self._on_restore_finished)
        self._worker.start()

    def _on_progress(self, step: int, total: int, msg: str):
        self.lbl_step.setText(msg)
        if total > 0:
            self.progress_bar.setValue(int(step / total * 100))

    def _on_finished(self, report):
        self.progress_card.hide()
        self.progress_bar.setValue(100)
        self.btn_optimize.setEnabled(True)
        self.btn_restore.setEnabled(True)
        self.btn_optimize.setText("⚡  RE-OPTIMISER")

        # Summary
        self.summary_card.show()
        color = Colors.SUCCESS if report.failed_count == 0 else Colors.WARNING
        self.lbl_summary.setStyleSheet(f"color: {color}; background: transparent;")
        self.lbl_summary.setText(
            f"✓  {report.success_count} optimisations appliquées  •  "
            f"{report.skipped_count} déjà en place  •  "
            f"{report.failed_count} échecs"
        )

        for result in report.results:
            row = ResultRow(result)
            self.results_layout.insertWidget(
                self.results_layout.count() - 1, row
            )
            # Séparateur
            sep = QFrame()
            sep.setFrameShape(QFrame.Shape.HLine)
            sep.setStyleSheet(f"color: {Colors.SILVER_GHOST};")
            self.results_layout.insertWidget(self.results_layout.count() - 1, sep)

    def _on_restore_finished(self, report):
        self.progress_card.hide()
        self.btn_optimize.setEnabled(True)
        self.btn_restore.setEnabled(True)
        self.btn_restore.setText("↺  Restaurer les défauts")
        self.summary_card.show()
        self.lbl_summary.setStyleSheet(f"color: {Colors.INFO}; background: transparent;")
        self.lbl_summary.setText(
            f"↺  Paramètres Windows restaurés ({report.success_count} éléments)"
        )
        for result in report.results:
            row = ResultRow(result)
            self.results_layout.insertWidget(self.results_layout.count() - 1, row)

    def _clear_results(self):
        while self.results_layout.count() > 1:
            item = self.results_layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()
