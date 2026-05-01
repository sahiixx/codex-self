import asyncio
from codex_self.health import HealthEngine


def test_diagnose_returns_report():
    engine = HealthEngine(bus_url="http://127.0.0.1:1")
    report = asyncio.run(engine.diagnose())
    assert report.status in ("healthy", "degraded", "unhealthy")
    assert "cpu_percent" in report.checks
    assert "memory_percent" in report.checks


def test_quick_check_liveness():
    engine = HealthEngine()
    result = engine.quick_check()
    assert result["status"] in ("healthy", "degraded")
    assert "pid" in result
