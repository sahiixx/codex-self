"""Self-diagnostic engine: system health, sandbox integrity, ecosystem reachability."""
from __future__ import annotations

import asyncio
import os
import time
from dataclasses import dataclass, field
from typing import Dict, Any, List
from datetime import datetime, timezone

import psutil
import httpx

from codex_self.config import settings


@dataclass
class HealthReport:
    status: str  # healthy | degraded | unhealthy
    timestamp: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    uptime_seconds: float = 0.0
    checks: Dict[str, Any] = field(default_factory=dict)
    warnings: List[str] = field(default_factory=list)


class HealthEngine:
    def __init__(self, bus_url: str = settings.bus_url) -> None:
        self._start = time.time()
        self.bus_url = bus_url
        self._cache: HealthReport | None = None
        self._cache_time = 0.0

    async def diagnose(self) -> HealthReport:
        now = time.time()
        # Cache for 5 seconds to avoid hammering the system
        if self._cache and (now - self._cache_time) < 5.0:
            return self._cache

        report = HealthReport(
            status="healthy",
            uptime_seconds=round(now - self._start, 2),
        )

        # System checks
        report.checks["cpu_percent"] = psutil.cpu_percent(interval=0.1)
        report.checks["memory_percent"] = psutil.virtual_memory().percent
        report.checks["disk_usage_percent"] = psutil.disk_usage("/").percent
        report.checks["open_files"] = len(psutil.Process().open_files())
        report.checks["thread_count"] = psutil.Process().num_threads()

        if report.checks["memory_percent"] > 90:
            report.status = "degraded"
            report.warnings.append("Memory usage > 90%")
        if report.checks["disk_usage_percent"] > 90:
            report.status = "degraded"
            report.warnings.append("Disk usage > 90%")

        # Sandbox integrity
        report.checks["sandbox_roots"] = settings.writable_roots
        report.checks["sandbox_valid"] = all(
            os.path.isdir(r) or os.path.isfile(r) for r in settings.writable_roots
        )
        if not report.checks["sandbox_valid"]:
            report.status = "degraded"
            report.warnings.append("One or more sandbox roots are unreachable")

        # Ecosystem reachability
        report.checks["bus_reachable"] = await self._ping_bus()
        if not report.checks["bus_reachable"]:
            report.status = "degraded"
            report.warnings.append(f"Bus at {self.bus_url} is unreachable")

        self._cache = report
        self._cache_time = now
        return report

    async def _ping_bus(self) -> bool:
        try:
            async with httpx.AsyncClient(timeout=5.0) as client:
                resp = await client.get(f"{self.bus_url}/health")
                return resp.status_code == 200
        except Exception:
            return False

    def quick_check(self) -> Dict[str, Any]:
        """Synchronous subset for liveness probes."""
        return {
            "status": "healthy" if psutil.virtual_memory().percent < 95 else "degraded",
            "pid": os.getpid(),
            "timestamp": datetime.now(timezone.utc).isoformat(),
        }
