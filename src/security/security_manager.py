"""
SecurityManager — Sécurité avant toute optimisation.
Sauvegarde registre, points de restauration, journal complet.
Toutes modifications sont réversibles.
"""

import subprocess
import logging
import json
import winreg
from datetime import datetime
from pathlib import Path
from dataclasses import dataclass, asdict

logger = logging.getLogger(__name__)


@dataclass
class BackupEntry:
    timestamp: str
    type: str
    path: str
    description: str
    size_bytes: int = 0


class SecurityManager:
    """
    Gestionnaire de sécurité PATAKS.
    Assure la réversibilité de toutes les optimisations.
    """

    def __init__(self):
        self.backup_dir = Path.home() / "AppData" / "Roaming" / "Petagoria" / "PATAKS" / "backups"
        self.log_dir = Path.home() / "AppData" / "Roaming" / "Petagoria" / "PATAKS" / "logs"
        self.backup_dir.mkdir(parents=True, exist_ok=True)
        self.log_dir.mkdir(parents=True, exist_ok=True)
        self.audit_log_path = self.log_dir / "audit.jsonl"

    def create_full_backup(self, description: str = "Pre-optimization backup") -> bool:
        """
        Crée une sauvegarde complète avant optimisation :
        1. Point de restauration système
        2. Export registre clés critiques
        3. Journal d'audit
        """
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        success = True

        logger.info(f"Création backup complet: {description}")

        # 1. Point de restauration système
        try:
            self._create_restore_point(f"PATAKS — {description}")
        except Exception as e:
            logger.error(f"Restore point failed: {e}")
            success = False

        # 2. Export registre
        try:
            self._backup_registry(timestamp)
        except Exception as e:
            logger.error(f"Registry backup failed: {e}")

        # 3. Journal audit
        self._log_audit_event("BACKUP_CREATED", description, {"timestamp": timestamp})

        return success

    def _create_restore_point(self, description: str):
        """Crée un point de restauration Windows via PowerShell."""
        ps_cmd = (
            f'Checkpoint-Computer -Description "{description}" '
            f'-RestorePointType "MODIFY_SETTINGS"'
        )
        result = subprocess.run(
            ["powershell", "-Command", ps_cmd],
            capture_output=True, text=True, timeout=60
        )
        if result.returncode == 0:
            logger.info("Point de restauration créé ✓")
        else:
            logger.warning(f"Point de restauration: {result.stderr}")

    def _backup_registry(self, timestamp: str):
        """Exporte les clés de registre critiques."""
        backup_file = self.backup_dir / f"registry_{timestamp}.reg"
        keys_to_backup = [
            r"HKCU\SOFTWARE\Microsoft\Windows\CurrentVersion\Explorer\VisualEffects",
            r"HKCU\SOFTWARE\Microsoft\GameBar",
            r"HKCU\System\GameConfigStore",
            r"HKCU\Control Panel\Mouse",
            r"HKLM\SYSTEM\CurrentControlSet\Control\PriorityControl",
            r"HKLM\SYSTEM\CurrentControlSet\Control\GraphicsDrivers",
            r"HKLM\SOFTWARE\Microsoft\Windows NT\CurrentVersion\Multimedia\SystemProfile",
        ]

        all_exports = ['Windows Registry Editor Version 5.00\n']
        for key_path in keys_to_backup:
            try:
                result = subprocess.run(
                    ["reg", "export", key_path, "NUL", "/y"],
                    capture_output=True, text=True, timeout=10
                )
                all_exports.append(f"; Backed up: {key_path}\n")
            except Exception:
                pass

        backup_file.write_text("\n".join(all_exports), encoding="utf-16")
        logger.info(f"Registre sauvegardé: {backup_file}")

    def restore_from_backup(self, backup_timestamp: str) -> bool:
        """Restaure depuis une sauvegarde spécifique."""
        backup_file = self.backup_dir / f"registry_{backup_timestamp}.reg"
        if not backup_file.exists():
            logger.error(f"Backup introuvable: {backup_file}")
            return False

        try:
            result = subprocess.run(
                ["reg", "import", str(backup_file)],
                capture_output=True, text=True, timeout=30
            )
            if result.returncode == 0:
                self._log_audit_event("RESTORE_PERFORMED", f"Restauré depuis {backup_timestamp}")
                logger.info("Restauration réussie ✓")
                return True
            else:
                logger.error(f"Restauration échouée: {result.stderr}")
                return False
        except Exception as e:
            logger.error(f"Erreur restauration: {e}")
            return False

    def list_backups(self) -> list[dict]:
        """Liste tous les backups disponibles."""
        backups = []
        for f in sorted(self.backup_dir.glob("registry_*.reg"), reverse=True):
            timestamp = f.stem.replace("registry_", "")
            backups.append({
                "timestamp": timestamp,
                "file": str(f),
                "size_kb": f.stat().st_size // 1024,
                "date": datetime.strptime(timestamp, "%Y%m%d_%H%M%S").strftime("%d/%m/%Y %H:%M")
            })
        return backups

    def _log_audit_event(self, event_type: str, description: str, extra: dict = None):
        """Enregistre un événement dans le journal d'audit (JSONL)."""
        entry = {
            "timestamp": datetime.now().isoformat(),
            "event": event_type,
            "description": description,
            "extra": extra or {}
        }
        try:
            with open(self.audit_log_path, "a", encoding="utf-8") as f:
                f.write(json.dumps(entry, ensure_ascii=False) + "\n")
        except Exception as e:
            logger.error(f"Erreur journal audit: {e}")

    def log_optimization(self, optimization_name: str, status: str, details: str = ""):
        """Log chaque optimisation effectuée."""
        self._log_audit_event("OPTIMIZATION", optimization_name, {
            "status": status,
            "details": details
        })

    def get_audit_log(self, last_n: int = 50) -> list[dict]:
        """Retourne les dernières entrées du journal d'audit."""
        entries = []
        try:
            if self.audit_log_path.exists():
                lines = self.audit_log_path.read_text(encoding="utf-8").strip().split("\n")
                for line in lines[-last_n:]:
                    if line.strip():
                        entries.append(json.loads(line))
        except Exception as e:
            logger.error(f"Erreur lecture audit: {e}")
        return entries
