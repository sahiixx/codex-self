"""Sandbox boundary enforcement and path validation."""
from __future__ import annotations

from pathlib import Path
from typing import List, Set
from dataclasses import dataclass, field
from datetime import datetime, timezone

from codex_self.config import settings


@dataclass
class AccessEvent:
    path: str
    action: str  # read | write | exec
    allowed: bool
    timestamp: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())


class SandboxGuard:
    def __init__(self, writable_roots: List[str] | None = None) -> None:
        self.roots = [Path(r).resolve() for r in (writable_roots or settings.writable_roots)]
        self._audit_log: List[AccessEvent] = []

    def check(self, path: str | Path, action: str = "read") -> bool:
        target = Path(path).resolve()
        for root in self.roots:
            try:
                target.relative_to(root)
                event = AccessEvent(str(target), action, True)
                self._audit_log.append(event)
                return True
            except ValueError:
                continue
        event = AccessEvent(str(target), action, False)
        self._audit_log.append(event)
        return False

    def assert_writable(self, path: str | Path) -> None:
        if not self.check(path, action="write"):
            raise PermissionError(f"Sandbox violation: {path} is outside writable roots: {self.roots}")

    def assert_readable(self, path: str | Path) -> None:
        if not self.check(path, action="read"):
            raise PermissionError(f"Sandbox violation: {path} is outside readable roots: {self.roots}")

    def recent_violations(self, n: int = 10) -> List[AccessEvent]:
        return [e for e in self._audit_log if not e.allowed][-n:]

    def audit_trail(self) -> List[dict]:
        return [
            {"path": e.path, "action": e.action, "allowed": e.allowed, "timestamp": e.timestamp}
            for e in self._audit_log
        ]
