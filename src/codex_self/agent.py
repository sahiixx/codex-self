"""Agent identity, capability registry, and self-description."""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Dict, List, Any
from datetime import datetime, timezone
import platform
import os


@dataclass
class Capability:
    name: str
    description: str
    enabled: bool = True
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class AgentIdentity:
    name: str
    version: str
    role: str
    runtime: str = "openai-codex"
    platform: str = field(default_factory=lambda: platform.platform())
    python_version: str = field(default_factory=lambda: platform.python_version())
    pid: int = field(default_factory=os.getpid)
    start_time: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    capabilities: List[Capability] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "name": self.name,
            "version": self.version,
            "role": self.role,
            "runtime": self.runtime,
            "platform": self.platform,
            "python_version": self.python_version,
            "pid": self.pid,
            "start_time": self.start_time,
            "capabilities": [
                {"name": c.name, "description": c.description, "enabled": c.enabled, "metadata": c.metadata}
                for c in self.capabilities
            ],
        }


def default_capabilities() -> List[Capability]:
    return [
        Capability("file-io", "Read and write files within sandbox boundaries"),
        Capability("shell-exec", "Execute shell commands in a PTY with approval gates"),
        Capability("patch-apply", "Apply unified-diff patches to source files"),
        Capability("agent-spawn", "Spawn explorer and worker sub-agents"),
        Capability("mcp-client", "Interact with MCP servers and resources"),
        Capability("health-check", "Self-diagnostic and ecosystem health reporting"),
        Capability("memory-persist", "Store and retrieve conversation state and preferences"),
        Capability("bus-register", "Register and heartbeat with the SAHIIXX A2A bus"),
        Capability("websocket-stream", "Real-time bidirectional dashboard communication"),
        Capability("skill-registry", "Load, advertise, and execute Codex skills"),
    ]


def build_identity(name: str = "codex-self", version: str = "2.0.0", role: str = "cli-assistant") -> AgentIdentity:
    agent = AgentIdentity(name=name, version=version, role=role)
    agent.capabilities = default_capabilities()
    return agent
