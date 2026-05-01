"""Persistent memory: SQLite-backed key-value and conversation state."""
from __future__ import annotations

import asyncio
import json
import sqlite3
from contextlib import contextmanager
from pathlib import Path
from typing import Any, Dict, List, Optional
from dataclasses import dataclass, asdict
from datetime import datetime, timezone

from codex_self.config import settings


@dataclass
class MemoryEntry:
    key: str
    value: Any
    scope: str = "global"      # global | session | project
    ttl: Optional[int] = None  # seconds until expiry
    created_at: str = ""
    updated_at: str = ""

    def __post_init__(self) -> None:
        if not self.created_at:
            self.created_at = datetime.now(timezone.utc).isoformat()
        if not self.updated_at:
            self.updated_at = self.created_at


class MemoryStore:
    def __init__(self, db_path: Path = settings.memory_path) -> None:
        self.db_path = db_path
        self._lock = asyncio.Lock()
        self._ensure_schema()

    def _ensure_schema(self) -> None:
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        with self._connection() as conn:
            conn.execute(
                """
                CREATE TABLE IF NOT EXISTS memory (
                    key TEXT PRIMARY KEY,
                    scope TEXT DEFAULT 'global',
                    value TEXT NOT NULL,
                    ttl INTEGER,
                    created_at TEXT,
                    updated_at TEXT
                )
                """
            )
            conn.execute(
                """
                CREATE TABLE IF NOT EXISTS conversations (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    session_id TEXT,
                    role TEXT,
                    content TEXT,
                    metadata TEXT,
                    timestamp TEXT
                )
                """
            )
            conn.commit()

    @contextmanager
    def _connection(self):
        conn = sqlite3.connect(str(self.db_path), check_same_thread=False)
        try:
            yield conn
        finally:
            conn.close()

    async def get(self, key: str, default: Any = None) -> Any:
        async with self._lock:
            with self._connection() as conn:
                row = conn.execute(
                    "SELECT value, ttl, updated_at FROM memory WHERE key = ?", (key,)
                ).fetchone()
                if not row:
                    return default
                value, ttl, updated_at = row
                if ttl is not None:
                    updated = datetime.fromisoformat(updated_at)
                    age = (datetime.now(timezone.utc) - updated).total_seconds()
                    if age > ttl:
                        conn.execute("DELETE FROM memory WHERE key = ?", (key,))
                        conn.commit()
                        return default
                return json.loads(value)

    async def set(self, key: str, value: Any, scope: str = "global", ttl: Optional[int] = None) -> None:
        async with self._lock:
            now = datetime.now(timezone.utc).isoformat()
            with self._connection() as conn:
                conn.execute(
                    """
                    INSERT INTO memory (key, scope, value, ttl, created_at, updated_at)
                    VALUES (?, ?, ?, ?, ?, ?)
                    ON CONFLICT(key) DO UPDATE SET
                        scope=excluded.scope,
                        value=excluded.value,
                        ttl=excluded.ttl,
                        updated_at=excluded.updated_at
                    """,
                    (key, scope, json.dumps(value), ttl, now, now),
                )
                conn.commit()

    async def delete(self, key: str) -> None:
        async with self._lock:
            with self._connection() as conn:
                conn.execute("DELETE FROM memory WHERE key = ?", (key,))
                conn.commit()

    async def list_keys(self, scope: Optional[str] = None) -> List[str]:
        async with self._lock:
            with self._connection() as conn:
                if scope:
                    rows = conn.execute(
                        "SELECT key FROM memory WHERE scope = ?", (scope,)
                    ).fetchall()
                else:
                    rows = conn.execute("SELECT key FROM memory").fetchall()
                return [r[0] for r in rows]

    async def log_conversation(self, session_id: str, role: str, content: str, metadata: Optional[Dict[str, Any]] = None) -> None:
        async with self._lock:
            with self._connection() as conn:
                conn.execute(
                    "INSERT INTO conversations (session_id, role, content, metadata, timestamp) VALUES (?, ?, ?, ?, ?)",
                    (session_id, role, content, json.dumps(metadata or {}), datetime.now(timezone.utc).isoformat()),
                )
                conn.commit()

    async def get_conversation(self, session_id: str, limit: int = 100) -> List[Dict[str, Any]]:
        async with self._lock:
            with self._connection() as conn:
                rows = conn.execute(
                    "SELECT role, content, metadata, timestamp FROM conversations WHERE session_id = ? ORDER BY id DESC LIMIT ?",
                    (session_id, limit),
                ).fetchall()
                return [
                    {"role": r[0], "content": r[1], "metadata": json.loads(r[2]), "timestamp": r[3]}
                    for r in reversed(rows)
                ]

    async def prune(self, max_age_seconds: int = 86400 * 7) -> int:
        """Remove entries older than max_age_seconds. Returns count deleted."""
        async with self._lock:
            cutoff = datetime.now(timezone.utc).isoformat()
            with self._connection() as conn:
                cur = conn.execute(
                    "DELETE FROM memory WHERE updated_at < datetime(?, '-' || ? || ' seconds')",
                    (cutoff, max_age_seconds),
                )
                conn.commit()
                return cur.rowcount
