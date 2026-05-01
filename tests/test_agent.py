import pytest
from codex_self.agent import build_identity, default_capabilities


def test_identity_has_name():
    agent = build_identity(name="test-agent", version="0.0.1", role="tester")
    d = agent.to_dict()
    assert d["name"] == "test-agent"
    assert d["version"] == "0.0.1"
    assert d["role"] == "tester"
    assert d["runtime"] == "openai-codex"
    assert "capabilities" in d


def test_default_capabilities_non_empty():
    caps = default_capabilities()
    assert len(caps) >= 5
    names = [c.name for c in caps]
    assert "file-io" in names
    assert "shell-exec" in names
