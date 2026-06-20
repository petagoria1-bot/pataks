"""
Tests PATAKS — Core modules
Exécuter avec : pytest tests/ -v
"""

import sys
import time
import pytest
from unittest.mock import MagicMock, patch
from pathlib import Path

# Ajouter src au path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))


# ─── SystemMonitor ────────────────────────────────────────────────────────────

class TestSystemSnapshot:
    def test_health_score_default(self):
        from core.system_monitor import SystemSnapshot
        snap = SystemSnapshot()
        assert snap.health_score == 100

    def test_health_score_range(self):
        from core.system_monitor import SystemMonitor
        monitor = SystemMonitor()

        from core.system_monitor import SystemSnapshot
        snap = SystemSnapshot()

        # Score normal
        snap.cpu_percent = 30
        snap.ram_percent = 40
        snap.cpu_temp_c = 60
        snap.gpu_temp_c = 65
        snap.disk_percent = 50
        score = monitor._compute_health(snap)
        assert score == 100, f"Expected 100, got {score}"

        # Score dégradé
        snap.cpu_percent = 95
        snap.ram_percent = 92
        snap.cpu_temp_c = 92
        score_bad = monitor._compute_health(snap)
        assert score_bad < 60, f"Score should be < 60 but got {score_bad}"

    def test_history_maxlen(self):
        from core.system_monitor import HistoricalData
        h = HistoricalData(maxlen=5)
        for i in range(10):
            h.cpu.append(float(i))
        assert len(h.cpu) == 5
        assert list(h.cpu) == [5.0, 6.0, 7.0, 8.0, 9.0]


class TestSystemMonitorCallbacks:
    def test_register_callback(self):
        from core.system_monitor import SystemMonitor, SystemSnapshot
        monitor = SystemMonitor()
        received = []
        monitor.register_callback(lambda s: received.append(s))
        assert len(monitor._callbacks) == 1

    def test_compute_health_penalties(self):
        from core.system_monitor import SystemMonitor, SystemSnapshot
        monitor = SystemMonitor()
        snap = SystemSnapshot()

        snap.cpu_percent = 95  # -20
        snap.ram_percent = 95  # -20
        snap.cpu_temp_c = 92   # -25
        snap.gpu_temp_c = 0
        snap.disk_percent = 50
        score = monitor._compute_health(snap)
        assert score == 35, f"Expected 35, got {score}"


# ─── AIAnalyzer ───────────────────────────────────────────────────────────────

class TestAIAnalyzer:
    def test_compute_score_all_ok(self):
        from core.ai_analyzer import AIAnalyzer, Finding, Severity
        analyzer = AIAnalyzer()
        findings = [
            Finding("CPU", "OK", "desc", Severity.OK, "", ""),
            Finding("RAM", "OK", "desc", Severity.OK, "", ""),
        ]
        score = analyzer._compute_score(findings)
        assert score == 100

    def test_compute_score_with_criticals(self):
        from core.ai_analyzer import AIAnalyzer, Finding, Severity
        analyzer = AIAnalyzer()
        findings = [
            Finding("CPU", "Critique", "desc", Severity.CRITICAL, "", ""),
            Finding("RAM", "Warning", "desc", Severity.WARNING, "", ""),
        ]
        # -20 (critical) - 8 (warning) = 72
        score = analyzer._compute_score(findings)
        assert score == 72, f"Expected 72, got {score}"

    def test_score_minimum_zero(self):
        from core.ai_analyzer import AIAnalyzer, Finding, Severity
        analyzer = AIAnalyzer()
        findings = [
            Finding("X", "C", "d", Severity.CRITICAL, "", "")
        ] * 10  # 10 criticals = -200 → clampé à 0
        score = analyzer._compute_score(findings)
        assert score == 0

    def test_build_summary_excellent(self):
        from core.ai_analyzer import AIAnalyzer, AnalysisReport, Finding, Severity
        analyzer = AIAnalyzer()
        report = AnalysisReport()
        report.score = 90
        report.findings = [
            Finding("X", "OK", "d", Severity.OK, "", ""),
            Finding("Y", "Warn", "d", Severity.WARNING, "", ""),
        ]
        summary = analyzer._build_summary(report)
        assert "90" in summary
        assert "excellente" in summary.lower()

    def test_build_summary_critical(self):
        from core.ai_analyzer import AIAnalyzer, AnalysisReport, Finding, Severity
        analyzer = AIAnalyzer()
        report = AnalysisReport()
        report.score = 30
        report.findings = [
            Finding("X", "Crit", "d", Severity.CRITICAL, "", ""),
            Finding("Y", "Crit", "d", Severity.CRITICAL, "", ""),
        ]
        summary = analyzer._build_summary(report)
        assert "urgente" in summary.lower() or "critique" in summary.lower()


# ─── GamingOptimizer ──────────────────────────────────────────────────────────

class TestOptimizationResult:
    def test_result_status(self):
        from core.gaming_optimizer import OptimizationResult, OptimizationStatus
        r = OptimizationResult("Test", OptimizationStatus.SUCCESS, "OK")
        assert r.status == OptimizationStatus.SUCCESS
        assert r.name == "Test"

    def test_report_counts(self):
        from core.gaming_optimizer import (
            OptimizationReport, OptimizationResult, OptimizationStatus
        )
        report = OptimizationReport()
        report.add(OptimizationResult("A", OptimizationStatus.SUCCESS, "ok"))
        report.add(OptimizationResult("B", OptimizationStatus.SUCCESS, "ok"))
        report.add(OptimizationResult("C", OptimizationStatus.FAILED, "err"))
        report.add(OptimizationResult("D", OptimizationStatus.SKIPPED, "skip"))
        assert report.success_count == 2
        assert report.failed_count == 1
        assert report.skipped_count == 1
        assert len(report.results) == 4


# ─── SecurityManager ──────────────────────────────────────────────────────────

class TestSecurityManager:
    def test_list_backups_empty(self, tmp_path):
        from security.security_manager import SecurityManager
        sm = SecurityManager()
        sm.backup_dir = tmp_path / "backups"
        sm.backup_dir.mkdir()
        backups = sm.list_backups()
        assert backups == []

    def test_audit_log(self, tmp_path):
        from security.security_manager import SecurityManager
        sm = SecurityManager()
        sm.log_dir = tmp_path / "logs"
        sm.log_dir.mkdir()
        sm.audit_log_path = sm.log_dir / "audit.jsonl"

        sm._log_audit_event("TEST_EVENT", "Test description", {"key": "val"})
        entries = sm.get_audit_log()
        assert len(entries) == 1
        assert entries[0]["event"] == "TEST_EVENT"
        assert entries[0]["description"] == "Test description"
        assert entries[0]["extra"]["key"] == "val"

    def test_audit_log_multiple_entries(self, tmp_path):
        from security.security_manager import SecurityManager
        sm = SecurityManager()
        sm.log_dir = tmp_path / "logs"
        sm.log_dir.mkdir()
        sm.audit_log_path = sm.log_dir / "audit.jsonl"

        for i in range(5):
            sm._log_audit_event(f"EVENT_{i}", f"Desc {i}")

        entries = sm.get_audit_log()
        assert len(entries) == 5
        assert entries[-1]["event"] == "EVENT_4"


# ─── Theme ────────────────────────────────────────────────────────────────────

class TestTheme:
    def test_status_color_ok(self):
        from ui.theme import get_status_color, Colors
        assert get_status_color(50) == Colors.SUCCESS

    def test_status_color_warning(self):
        from ui.theme import get_status_color, Colors
        assert get_status_color(75) == Colors.WARNING

    def test_status_color_danger(self):
        from ui.theme import get_status_color, Colors
        assert get_status_color(90) == Colors.DANGER

    def test_temp_color(self):
        from ui.theme import get_temp_color, Colors
        assert get_temp_color(50) == Colors.SUCCESS
        assert get_temp_color(75) == Colors.WARNING
        assert get_temp_color(90) == Colors.DANGER

    def test_colors_defined(self):
        from ui.theme import Colors
        assert Colors.CRIMSON.startswith("#")
        assert Colors.BG_DEEP.startswith("#")
        assert Colors.SILVER.startswith("#")


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
