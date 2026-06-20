"""
SecurityPage — Sécurité et backups.
Affiche les sauvegardes créées, le journal d'audit,
et permet de restaurer depuis une sauvegarde.
"""

import logging
from datetime import datetime

from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel,
    QPushButton, QScrollArea, QFrame, QTableWidget,
    QTableWidgetItem, QHeaderView, QAbstractItemView,
    QMessageBox
)
from PyQt6.QtCore import Qt, QThread, pyqtSignal, QTimer
from PyQt6.QtGui import QColor, QFont

from ui.theme import Colors, Typography, Spacing
from ui.components.widgets import GlassCard, SectionHeader, StatusBadge
from security.security_manager import SecurityManager

logger = logging.getLogger(__name__)


class BackupWorker(QThread):
    done = pyqtSignal(bool)

    def run(self):
        sm = SecurityManager()
        ok = sm.create_full_backup("Backup manuel depuis PATAKS")
        self.done.emit(ok)


class RestoreWorker(QThread):
    done = pyqtSignal(bool)

    def __init__(self, timestamp: str):
        super().__init__()
        self._ts = timestamp

    def run(self):
        sm = SecurityManager()
        ok = sm.restore_from_backup(self._ts)
        self.done.emit(ok)


class SecurityPage(QWidget):
    """Page Sécurité — Backups & Audit."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self._sm = SecurityManager()
        self._worker = None
        self._build_ui()
        # Charger les données au démarrage
        QTimer.singleShot(200, self._refresh)

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

        # ── Header ──────────────────────────────────────────────────
        hrow = QHBoxLayout()
        hrow.addWidget(SectionHeader("Sécurité", "Backups & Journal d'audit"))
        hrow.addStretch()

        btn_backup = QPushButton("+ Créer un backup maintenant")
        btn_backup.setFixedHeight(36)
        btn_backup.setFont(Typography.body(10))
        btn_backup.setCursor(Qt.CursorShape.PointingHandCursor)
        btn_backup.setStyleSheet(f"""
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
        btn_backup.clicked.connect(self._create_backup)
        hrow.addWidget(btn_backup)
        layout.addLayout(hrow)

        # ── Info sécurité ────────────────────────────────────────────
        info_card = GlassCard()
        info_l = info_card.layout()
        info_l.setSpacing(Spacing.SM)

        info_row = QHBoxLayout()
        info_row.setSpacing(Spacing.XL)

        for icon, title, desc in [
            ("🔒", "Backup automatique", "Créé avant chaque optimisation"),
            ("📋", "Registre complet",   "7 clés critiques exportées en .reg"),
            ("↺",  "100% réversible",    "Restauration en 1 clic"),
            ("📝", "Journal d'audit",    "Toutes les actions horodatées"),
        ]:
            col = QVBoxLayout()
            col.setSpacing(3)
            lbl_icon = QLabel(icon)
            lbl_icon.setFont(QFont("Segoe UI Emoji", 18))
            lbl_icon.setStyleSheet("background: transparent;")
            lbl_icon.setAlignment(Qt.AlignmentFlag.AlignCenter)
            lbl_title = QLabel(title)
            lbl_title.setFont(Typography.heading(11))
            lbl_title.setStyleSheet(f"color: {Colors.SILVER_BRIGHT}; background: transparent;")
            lbl_title.setAlignment(Qt.AlignmentFlag.AlignCenter)
            lbl_desc = QLabel(desc)
            lbl_desc.setFont(Typography.body(9))
            lbl_desc.setStyleSheet(f"color: {Colors.SILVER_DIM}; background: transparent;")
            lbl_desc.setAlignment(Qt.AlignmentFlag.AlignCenter)
            col.addWidget(lbl_icon)
            col.addWidget(lbl_title)
            col.addWidget(lbl_desc)
            info_row.addLayout(col)

        info_l.addLayout(info_row)
        layout.addWidget(info_card)

        # ── Backups disponibles ──────────────────────────────────────
        layout.addWidget(SectionHeader("Sauvegardes disponibles", ""))

        self._backup_status = QLabel("Chargement...")
        self._backup_status.setFont(Typography.body(10))
        self._backup_status.setStyleSheet(f"color: {Colors.SILVER_DIM}; background: transparent;")
        layout.addWidget(self._backup_status)

        self._backup_table = QTableWidget(0, 4)
        self._backup_table.setHorizontalHeaderLabels(["Date", "Timestamp", "Taille", "Action"])
        self._backup_table.setStyleSheet(f"""
            QTableWidget {{
                background: {Colors.BG_SURFACE};
                border: 1px solid {Colors.SILVER_GHOST};
                border-radius: 8px;
                gridline-color: {Colors.BG_ELEVATED};
                color: {Colors.SILVER};
                font-size: 10px;
            }}
            QTableWidget::item {{
                padding: 8px 12px;
                border: none;
            }}
            QTableWidget::item:selected {{
                background: {Colors.CRIMSON_DIM};
                color: {Colors.SILVER_BRIGHT};
            }}
            QHeaderView::section {{
                background: {Colors.BG_ELEVATED};
                color: {Colors.SILVER_DIM};
                border: none;
                border-bottom: 1px solid {Colors.SILVER_GHOST};
                padding: 8px 12px;
                font-size: 8px;
                font-weight: 600;
                letter-spacing: 1.5px;
                text-transform: uppercase;
            }}
        """)
        self._backup_table.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)
        self._backup_table.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)
        self._backup_table.horizontalHeader().setSectionResizeMode(0, QHeaderView.ResizeMode.Stretch)
        self._backup_table.horizontalHeader().setSectionResizeMode(1, QHeaderView.ResizeMode.ResizeToContents)
        self._backup_table.horizontalHeader().setSectionResizeMode(2, QHeaderView.ResizeMode.ResizeToContents)
        self._backup_table.horizontalHeader().setSectionResizeMode(3, QHeaderView.ResizeMode.Fixed)
        self._backup_table.setColumnWidth(3, 130)
        self._backup_table.setFixedHeight(200)
        self._backup_table.verticalHeader().setVisible(False)
        layout.addWidget(self._backup_table)

        # ── Journal d'audit ─────────────────────────────────────────
        layout.addWidget(SectionHeader("Journal d'audit", "50 dernières actions"))

        self._audit_table = QTableWidget(0, 3)
        self._audit_table.setHorizontalHeaderLabels(["Horodatage", "Événement", "Détail"])
        self._audit_table.setStyleSheet(self._backup_table.styleSheet())
        self._audit_table.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)
        self._audit_table.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)
        self._audit_table.horizontalHeader().setSectionResizeMode(0, QHeaderView.ResizeMode.ResizeToContents)
        self._audit_table.horizontalHeader().setSectionResizeMode(1, QHeaderView.ResizeMode.ResizeToContents)
        self._audit_table.horizontalHeader().setSectionResizeMode(2, QHeaderView.ResizeMode.Stretch)
        self._audit_table.verticalHeader().setVisible(False)
        self._audit_table.setFixedHeight(250)
        layout.addWidget(self._audit_table)

        layout.addStretch()
        scroll.setWidget(content)
        root.addWidget(scroll)

    def _refresh(self):
        """Recharge backups et journal."""
        try:
            backups = self._sm.list_backups()
            self._load_backups(backups)
        except Exception as e:
            logger.error(f"Erreur chargement backups: {e}")
            self._backup_status.setText(f"Dossier de backups : {self._sm.backup_dir}")

        try:
            audit = self._sm.get_audit_log(50)
            self._load_audit(audit)
        except Exception as e:
            logger.error(f"Erreur chargement audit: {e}")

    def _load_backups(self, backups: list):
        self._backup_table.setRowCount(0)
        if not backups:
            self._backup_status.setText(
                f"Aucun backup trouvé. Les backups sont créés automatiquement avant chaque optimisation."
            )
            return

        self._backup_status.setText(f"{len(backups)} sauvegarde(s) disponible(s) — {self._sm.backup_dir}")

        for b in backups:
            row = self._backup_table.rowCount()
            self._backup_table.insertRow(row)

            date_item = QTableWidgetItem(b.get("date", "—"))
            date_item.setForeground(QColor(Colors.SILVER))
            self._backup_table.setItem(row, 0, date_item)

            ts_item = QTableWidgetItem(b.get("timestamp", "—"))
            ts_item.setForeground(QColor(Colors.SILVER_DIM))
            self._backup_table.setItem(row, 1, ts_item)

            size_item = QTableWidgetItem(f"{b.get('size_kb', 0)} KB")
            size_item.setForeground(QColor(Colors.SILVER_DIM))
            size_item.setTextAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
            self._backup_table.setItem(row, 2, size_item)

            # Bouton restaurer
            btn = QPushButton("↺ Restaurer")
            btn.setStyleSheet(f"""
                QPushButton {{
                    background: {Colors.BG_ELEVATED};
                    color: {Colors.SILVER_DIM};
                    border: 1px solid {Colors.SILVER_GHOST};
                    border-radius: 4px;
                    padding: 4px 10px;
                    font-size: 9px;
                }}
                QPushButton:hover {{
                    border-color: {Colors.WARNING};
                    color: {Colors.WARNING};
                }}
            """)
            ts = b.get("timestamp", "")
            btn.clicked.connect(lambda _, t=ts: self._restore_backup(t))
            self._backup_table.setCellWidget(row, 3, btn)

    def _load_audit(self, entries: list):
        self._audit_table.setRowCount(0)
        for entry in reversed(entries):  # Plus récent en premier
            row = self._audit_table.rowCount()
            self._audit_table.insertRow(row)

            ts = entry.get("timestamp", "")
            try:
                dt = datetime.fromisoformat(ts)
                ts_fmt = dt.strftime("%d/%m %H:%M:%S")
            except Exception:
                ts_fmt = ts[:19] if ts else "—"

            ts_item = QTableWidgetItem(ts_fmt)
            ts_item.setForeground(QColor(Colors.SILVER_DIM))
            self._audit_table.setItem(row, 0, ts_item)

            event_item = QTableWidgetItem(entry.get("event", "—"))
            event_color = {
                "BACKUP_CREATED": Colors.SUCCESS,
                "RESTORE_PERFORMED": Colors.WARNING,
                "OPTIMIZATION": Colors.INFO,
            }.get(entry.get("event", ""), Colors.SILVER)
            event_item.setForeground(QColor(event_color))
            self._audit_table.setItem(row, 1, event_item)

            detail_item = QTableWidgetItem(entry.get("description", ""))
            detail_item.setForeground(QColor(Colors.SILVER_DIM))
            self._audit_table.setItem(row, 2, detail_item)

    def _create_backup(self):
        self._worker = BackupWorker()
        self._worker.done.connect(self._on_backup_done)
        self._worker.start()

    def _on_backup_done(self, ok: bool):
        if ok:
            self._refresh()
        else:
            logger.warning("Backup échoué")

    def _restore_backup(self, timestamp: str):
        self._worker = RestoreWorker(timestamp)
        self._worker.done.connect(lambda ok: self._refresh() if ok else None)
        self._worker.start()

    def refresh(self):
        """Appelé quand la page devient visible."""
        self._refresh()
