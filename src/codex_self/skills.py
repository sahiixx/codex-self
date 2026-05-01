"""Skill registry: load, validate, and advertise Codex skills."""
from __future__ import annotations

import json
from pathlib import Path
from typing import Dict, Any, List, Optional
from dataclasses import dataclass, field

from codex_self.config import settings


@dataclass
class Skill:
    name: str
    description: str
    version: str = "1.0.0"
    author: str = ""
    triggers: List[str] = field(default_factory=list)
    parameters: Dict[str, Any] = field(default_factory=dict)
    metadata: Dict[str, Any] = field(default_factory=dict)

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "Skill":
        return cls(
            name=data["name"],
            description=data.get("description", ""),
            version=data.get("version", "1.0.0"),
            author=data.get("author", ""),
            triggers=data.get("triggers", []),
            parameters=data.get("parameters", {}),
            metadata=data.get("metadata", {}),
        )

    def to_dict(self) -> Dict[str, Any]:
        return {
            "name": self.name,
            "description": self.description,
            "version": self.version,
            "author": self.author,
            "triggers": self.triggers,
            "parameters": self.parameters,
            "metadata": self.metadata,
        }


class SkillRegistry:
    def __init__(self, skill_dirs: Optional[List[Path]] = None) -> None:
        self._skills: Dict[str, Skill] = {}
        self._skill_dirs = skill_dirs or [
            Path.home() / ".codex" / "skills",
            Path(__file__).parent.parent.parent / "skills",
        ]
        self._load_all()

    def _load_all(self) -> None:
        for directory in self._skill_dirs:
            if not directory.exists():
                continue
            for skill_file in directory.rglob("SKILL.md"):
                self._parse_skill(skill_file)
            for json_file in directory.rglob("*.skill"):
                self._load_json_skill(json_file)

    def _parse_skill(self, path: Path) -> None:
        # Simple markdown header parser for SKILL.md files
        lines = path.read_text(encoding="utf-8").splitlines()
        name = path.parent.name
        description = ""
        triggers: List[str] = []
        for line in lines:
            if line.startswith("# ") and not description:
                name = line[2:].strip()
            elif line.startswith("> ") and not description:
                description = line[2:].strip()
            elif line.lower().startswith("- trigger:") or line.lower().startswith("triggers:"):
                rest = line.split(":", 1)[-1].strip()
                if rest:
                    triggers.append(rest)
        skill = Skill(name=name, description=description, triggers=triggers, metadata={"source": str(path)})
        self._skills[skill.name] = skill

    def _load_json_skill(self, path: Path) -> None:
        try:
            data = json.loads(path.read_text(encoding="utf-8"))
            if isinstance(data, dict):
                skill = Skill.from_dict(data)
                self._skills[skill.name] = skill
            elif isinstance(data, list):
                for item in data:
                    skill = Skill.from_dict(item)
                    self._skills[skill.name] = skill
        except Exception:
            pass

    def get(self, name: str) -> Optional[Skill]:
        return self._skills.get(name)

    def list_skills(self) -> List[Skill]:
        return list(self._skills.values())

    def match(self, query: str) -> List[Skill]:
        query_lower = query.lower()
        return [
            s for s in self._skills.values()
            if query_lower in s.name.lower() or any(query_lower in t.lower() for t in s.triggers)
        ]

    def register(self, skill: Skill) -> None:
        self._skills[skill.name] = skill
