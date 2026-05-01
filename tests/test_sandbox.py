import pytest
from pathlib import Path
from codex_self.sandbox import SandboxGuard


def test_sandbox_allows_writable_root(tmp_path):
    guard = SandboxGuard(writable_roots=[str(tmp_path)])
    test_file = tmp_path / "test.txt"
    test_file.write_text("hello")
    assert guard.check(test_file, "read") is True
    assert guard.check(test_file, "write") is True


def test_sandbox_denies_outside_path(tmp_path):
    guard = SandboxGuard(writable_roots=[str(tmp_path)])
    assert guard.check("/etc/passwd", "read") is False
    assert guard.check("/tmp/hack", "write") is False


def test_sandbox_assert_writable_raises(tmp_path):
    guard = SandboxGuard(writable_roots=[str(tmp_path)])
    with pytest.raises(PermissionError):
        guard.assert_writable("/etc/passwd")


def test_audit_trail_records_events(tmp_path):
    guard = SandboxGuard(writable_roots=[str(tmp_path)])
    guard.check("/etc/passwd", "read")
    violations = guard.recent_violations()
    assert len(violations) == 1
    assert violations[0].allowed is False
