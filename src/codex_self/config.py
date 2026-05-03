"""Runtime configuration."""
from __future__ import annotations

import os
from pathlib import Path
from typing import List


def _env_list(key: str, default: List[str]) -> List[str]:
    val = os.getenv(key)
    if val is None:
        return default
    return [v.strip() for v in val.split(",") if v.strip()]


class Settings:
    agent_name: str = os.getenv("AGENT_NAME", "codex-self")
    agent_version: str = os.getenv("AGENT_VERSION", "2.0.0")
    agent_role: str = os.getenv("AGENT_ROLE", "cli-assistant")
    host: str = os.getenv("CODEX_SELF_HOST", "0.0.0.0")
    port: int = int(os.getenv("CODEX_SELF_PORT", "9001"))
    bus_url: str = os.getenv("SAHIIXX_BUS_URL", "http://sahiixx-bus:9000")
    writable_roots: List[str] = _env_list(
        "CODEX_WRITABLE_ROOTS",
        [str(Path.home() / ".codex" / "memories"), str(Path.home()), "/tmp"],
    )
    memory_path: Path = Path(os.getenv("CODEX_MEMORY_PATH", str(Path.home() / ".codex" / "memories" / "codex_self.db")))
    log_level: str = os.getenv("LOG_LEVEL", "info")
    openai_api_key: str | None = os.getenv("OPENAI_API_KEY")

    def is_writable(self, path: str | Path) -> bool:
        """Check whether a path is inside any declared writable root."""
        target = Path(path).resolve()
        for root in self.writable_roots:
            root_path = Path(root).resolve()
            try:
                target.relative_to(root_path)
                return True
            except ValueError:
                continue
        return False


settings = Settings()
