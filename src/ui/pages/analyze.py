"""
Analyze Page — Page d'analyse IA.
Interface : bouton "Analyser mon PC" + rapport détaillé avec catégories.
"""

from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel,
    QScrollArea, QFrame, QProgressBar, QSizePolicy
)
from PyQt6.QtCore import Qt, QThread, pyqtSignal, QTimer
from PyQt6.QtGui import QColor, QPainter, QLinearGradient, QFont

from ui.theme import Colors, Typography, Spacing, Radius
from ui.components.widgets import (
    GlassCard, GlowButton, SectionHeader, StatusBadge
)
from core.ai_analyzer import AIAnalyzer, AnalysisReport, Finding, Severity


# ─── WORKER THREAD ────────────────────────────────────────────────────────────

class AnalysisWorker(QThread):
    """Thread dédié à l'analyse (ne bloque pas l'UI)."""

    progress = pyqtSignal(int, int, str)
    finished = pyqtSignal(object)

    def run(self):
        analyzer = AIAnalyzer()
        report = analyzer.analyze(progress_callback=self.progress.emit)
        self.finished.emit(report)


# ─── FINDING CARD ─────────────────────────────────────────────────────────────

class FindingCard(GlassCard):
    """Carte affichant un Finding de l'analyse."""

    SEVERITY_CONFIG = {
        Severity.OK:       (Colors.SUCCESS,  "✓", "OK"),
        Severity.INFO:     ("#2090E0",        "i", "INFO"),
        Severity.WARNING:  (Colors.WARNING,   "!", "ATTENTION"),
        Severity.CRITICAL: (Colors.DANGER,    "✕", "CRITIQUE"),
    }

    def __init__(self, finding: Finding, parent=None):
        color, _, _ = self.SEVERITY_CONFIG.get(finding.severity,
                                                 (Colors.SILVER_DIM, "?", "?"))
        super().__init__(parent, glow_color=color)
        self._build(finding)

    def _build(self, f: Finding):
        layout = self.layout()

        color, icon, label = self.SEVERITY_CONFIG.get(
            f.severity, (Colors.SILVER_DIM, "?", "UNKNOWN")
        )

        # ── Header ────────────────────────────────────────────────
        header = QHBoxLayout()
        header.setSpacing(Spacing.SM)

        # Icône + badge
        badge = StatusBadge(f"{icon} {label}", f.severity.value)
        header.addWidget(badge)

        # Catégorie
        cat = QLabel(f.category.upper())
        cat.setFont(Typography.label(8))
        cat.setStyleSheet(f"color: {Colors.SILVER_GHOST}; background: transparent; letter-spacing: 1px;")
        header.addWidget(cat)
        header.addStretch()

        # Auto-fix badge
        if f.auto_fixable:
            fix_badge = QLabel("⚡ AUTO-FIX")
            fix_badge.setFont(Typography.label(8))
            fix_badge.setStyleSheet(f"""
                color: {Colors.CRIMSON};
                background: {Colors.CRIMSON_DIM};
                border: 1px solid {Colors.CRIMSON}40;
                border-radius: 8px;
                padding: 2px 8px;
            """)
            header.addWidget(fix_badge)

        layout.addLayout(header)

        # ── Titre ─────────────────────────────────────────────────
        lbl_title = QLabel(f.title)
        lbl_title.setFont(Typography.heading(12))
        lbl_title.setStyleSheet(f"color: {Colors.SILVER_BRIGHT}; background: transparent;")
        lbl_title.setWordWrap(True)
        layout.addWidget(lbl_title)

        # ── Description ───────────────────────────────────────────
        lbl_desc = QLabel(f.description)
        lbl_desc.setFont(Typography.body(10))
        lbl_desc.setStyleSheet(f"color: {Colors.SILVER_DIM}; background: transparent;")
        lbl_desc.setWordWrap(True)
        layout.addWidget(lbl_desc)

        # ── Impact + recommandation (si pertinent) ────────────────
        if f.recommendation or f.impact:
            sep = QFrame()
            sep.setFrameShape(QFrame.Shape.HLine)
            sep.setStyleSheet(f"color: {Colors.SILVER_GHOST};")
            layout.addWidget(sep)

            detail_layout = QHBoxLayout()

            if f.impact:
                impact_col = QVBoxLayout()
                lbl_impact_title = QLabel("IMPACT ESTIMÉ")
                lbl_impact_title.setFont(Typography.label(8))
                lbl_impact_title.setStyleSheet(
                    f"color: {Colors.SILVER_GHOST}; background: transparent; letter-spacing: 1px;"
                )
                lbl_impact_val = QLabel(f.impact)
                lbl_impact_val.setFont(Typography.body(10))
                lbl_impact_val.setStyleSheet(f"color: {color}; background: transparent;")
                lbl_impact_val.setWordWrap(True)
                impact_col.addWidget(lbl_impact_title)
                impact_col.addWidget(lbl_impact_val)
                detail_layout.addLayout(impact_col)

            if f.recommendation:
                rec_col = QVBoxLayout()
                lbl_rec_title = QLabel("RECOMMANDATION")
                lbl_rec_title.setFont(Typography.label(8))
                lbl_rec_title.setStyleSheet(
                    f"color: {Colors.SILVER_GHOST}; background: transparent; letter-spacing: 1px;"
                )
                lbl_rec_val = QLabel(f.recommendation)
                lbl_rec_val.setFont(Typography.body(10))
                lbl_rec_val.setStyleSheet(f"color: {Colors.SILVER_DIM}; background: transparent;")
                lbl_rec_val.setWordWrap(True)
                rec_col.addWidget(lbl_rec_title)
                rec_col.addWidget(lbl_rec_val)
                detail_layout.addLayout(rec_col, 1)

            layout.addLayout(detail_layout)


# ─── SCORE BAR ────────────────────────────────────────────────────────────────

class ScoreBarWidget(QWidget):
    """Grande barre de score post-analyse."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setFixedHeight(100)
        self._score = 0
        self._animated = 0.0
        self._summary = ""

        layout = QVBoxLayout(self)
        layout.setContentsMargins(Spacing.XL, Spacing.LG, Spacing.XL, Spacing.LG)
        layout.setSpacing(Spacing.SM)

        top_row = QHBoxLayout()
        self.lbl_score = QLabel("--")
        self.lbl_score.setFont(Typography.font("JetBrains Mono", 36, QFont.Weight.Bold))
        self.lbl_score.setStyleSheet(f"color: {Colors.SILVER_BRIGHT};")

        self.lbl_summary = QLabel("Cliquez sur 'Analyser mon PC' pour démarrer")
        self.lbl_summary.setFont(Typography.body(11))
        self.lbl_summary.setStyleSheet(f"color: {Colors.SILVER_DIM};")
        self.lbl_summary.setWordWrap(True)

        top_row.addWidget(self.lbl_score)
        lbl_unit = QLabel("/100")
        lbl_unit.setFont(Typography.body(14))
        lbl_unit.setStyleSheet(f"color: {Colors.SILVER_DIM}; padding-top: 14px;")
        top_row.addWidget(lbl_unit, alignment=Qt.AlignmentFlag.AlignBottom)
        top_row.addWidget(self.lbl_summary, 1)

        self.bar = QProgressBar()
        self.bar.setFixedHeight(8)
        self.bar.setRange(0, 100)
        self.bar.setValue(0)
        self.bar.setTextVisible(False)

        layout.addLayout(top_row)
        layout.addWidget(self.bar)

        self._timer = QTimer(self)
        self._timer.timeout.connect(self._tick)
        self._timer.start(16)

    def hideEvent(self, event):
        self._timer.stop()
        super().hideEvent(event)

    def showEvent(self, event):
        if not self._timer.isActive():
            self._timer.start(16)
        super().showEvent(event)

    def closeEvent(self, event):
        self._timer.stop()
        super().closeEvent(event)

    def set_score(self, score: int, summary: str):
        self._score = score
        self._summary = summary
        self.lbl_summary.setText(summary)
        color = Colors.SUCCESS if score >= 80 else Colors.WARNING if score >= 50 else Colors.DANGER
        self.lbl_score.setStyleSheet(f"color: {color};")
        self.bar.setStyleSheet(f"""
            QProgressBar {{ background: {Colors.BG_ELEVATED}; border-radius: 4px; }}
            QProgressBar::chunk {{ background: {color}; border-radius: 4px; }}
        """)

    def _tick(self):
        diff = self._score - self._animated
        if abs(diff) > 0.1:
            self._animated += diff * 0.08
            self.lbl_score.setText(f"{int(self._animated)}")
            self.bar.setValue(int(self._animated))


# ─── ANALYZE PAGE ─────────────────────────────────────────────────────────────

class AnalyzePage(QWidget):
    """Page principale d'analyse IA."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self._worker: AnalysisWorker = None
        self._build_ui()

    def _build_ui(self):
        root = QVBoxLayout(self)
        root.setContentsMargins(Spacing.XL, Spacing.XL, Spacing.XL, Spacing.XL)
        root.setSpacing(Spacing.LG)

        # Header
        header_row = QHBoxLayout()
        header_row.addWidget(SectionHeader("Analyse IA", "Diagnostic complet du système"))
        header_row.addStretch()

        self.btn_analyze = GlowButton("  ◈  ANALYSER MON PC", Colors.CRIMSON)
        self.btn_analyze.setFixedSize(200, 44)
        self.btn_analyze.clicked.connect(self._start_analysis)
        header_row.addWidget(self.btn_analyze)

        root.addLayout(header_row)

        # Score bar (collapsé initialement)
        score_card = GlassCard()
        self.score_bar = ScoreBarWidget()
        score_card.layout().addWidget(self.score_bar)
        root.addWidget(score_card)

        # Progress (visible pendant analyse)
        self.progress_card = GlassCard()
        progress_layout = self.progress_card.layout()

        self.lbl_progress = QLabel("Prêt à analyser...")
        self.lbl_progress.setFont(Typography.body(11))
        self.lbl_progress.setStyleSheet(f"color: {Colors.SILVER_DIM};")

        self.progress_bar = QProgressBar()
        self.progress_bar.setFixedHeight(6)
        self.progress_bar.setRange(0, 100)
        self.progress_bar.setValue(0)
        self.progress_bar.setTextVisible(False)
        self.progress_bar.setStyleSheet(f"""
            QProgressBar {{
                background: {Colors.BG_ELEVATED};
                border-radius: 3px;
                border: none;
            }}
            QProgressBar::chunk {{
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                    stop:0 {Colors.CRIMSON_DARK}, stop:1 {Colors.CRIMSON_GLOW});
                border-radius: 3px;
            }}
        """)

        progress_layout.addWidget(self.lbl_progress)
        progress_layout.addWidget(self.progress_bar)
        self.progress_card.hide()
        root.addWidget(self.progress_card)

        # Résultats (scrollable)
        self.scroll = QScrollArea()
        self.scroll.setWidgetResizable(True)
        self.scroll.setStyleSheet("QScrollArea { border: none; background: transparent; }")

        self.results_container = QWidget()
        self.results_container.setStyleSheet("background: transparent;")
        self.results_layout = QVBoxLayout(self.results_container)
        self.results_layout.setSpacing(Spacing.SM)
        self.results_layout.addStretch()

        self.scroll.setWidget(self.results_container)
        root.addWidget(self.scroll, 1)

    def _start_analysis(self):
        """Démarre l'analyse dans un thread dédié."""
        self.btn_analyze.setEnabled(False)
        self.btn_analyze.setText("  ◌  ANALYSE EN COURS...")
        self.progress_card.show()
        self._clear_results()

        self._worker = AnalysisWorker()
        self._worker.progress.connect(self._on_progress)
        self._worker.finished.connect(self._on_finished)
        self._worker.start()

    def _on_progress(self, step: int, total: int, message: str):
        self.lbl_progress.setText(message)
        if total > 0:
            self.progress_bar.setValue(int(step / total * 100))

    def _on_finished(self, report: AnalysisReport):
        self.progress_bar.setValue(100)
        self.progress_card.hide()
        self.btn_analyze.setEnabled(True)
        self.btn_analyze.setText("  ◈  RE-ANALYSER")
        self._render_report(report)

    def _render_report(self, report: AnalysisReport):
        """Affiche le rapport complet."""
        self._clear_results()

        # Score
        self.score_bar.set_score(report.score, report.summary)

        # Tri : critiques en premier, puis warnings, info, ok
        severity_order = {
            Severity.CRITICAL: 0,
            Severity.WARNING: 1,
            Severity.INFO: 2,
            Severity.OK: 3,
        }
        sorted_findings = sorted(
            report.findings,
            key=lambda f: severity_order.get(f.severity, 4)
        )

        # Stats rapides
        stats_row = QHBoxLayout()
        for label, count, color in [
            ("CRITIQUES", report.critical_count, Colors.DANGER),
            ("AVERTISSEMENTS", report.warning_count, Colors.WARNING),
            ("OK", report.ok_count, Colors.SUCCESS),
        ]:
            stat_card = GlassCard()
            stat_card.setFixedHeight(70)
            stat_card.layout().setAlignment(Qt.AlignmentFlag.AlignCenter)
            lbl_n = QLabel(str(count))
            lbl_n.setFont(Typography.font("JetBrains Mono", 24, QFont.Weight.Bold))
            lbl_n.setStyleSheet(f"color: {color}; background: transparent;")
            lbl_n.setAlignment(Qt.AlignmentFlag.AlignCenter)
            lbl_t = QLabel(label)
            lbl_t.setFont(Typography.label(8))
            lbl_t.setStyleSheet(f"color: {Colors.SILVER_DIM}; background: transparent; letter-spacing: 1.5px;")
            lbl_t.setAlignment(Qt.AlignmentFlag.AlignCenter)
            stat_card.layout().addWidget(lbl_n)
            stat_card.layout().addWidget(lbl_t)
            stats_row.addWidget(stat_card)

        stats_widget = QWidget()
        stats_widget.setLayout(stats_row)
        self.results_layout.insertWidget(0, stats_widget)

        # Findings
        for finding in sorted_findings:
            if finding.severity != Severity.OK:
                card = FindingCard(finding)
                self.results_layout.insertWidget(
                    self.results_layout.count() - 1, card
                )

        # Section OK (collapsed par défaut)
        ok_findings = [f for f in sorted_findings if f.severity == Severity.OK]
        if ok_findings:
            ok_label = QLabel(f"  ✓  {len(ok_findings)} vérifications OK")
            ok_label.setFont(Typography.body(10))
            ok_label.setStyleSheet(f"color: {Colors.SUCCESS}; padding: 8px 0;")
            self.results_layout.insertWidget(
                self.results_layout.count() - 1, ok_label
            )

        # Durée
        duration_lbl = QLabel(
            f"Analyse complète en {report.analysis_duration_sec:.1f}s — "
            f"{len(report.findings)} vérifications effectuées"
        )
        duration_lbl.setFont(Typography.label(8))
        duration_lbl.setStyleSheet(f"color: {Colors.SILVER_GHOST}; padding: 4px 0; letter-spacing: 1px;")
        self.results_layout.insertWidget(self.results_layout.count() - 1, duration_lbl)

    def _clear_results(self):
        """Vide les résultats précédents."""
        while self.results_layout.count() > 1:
            item = self.results_layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()
