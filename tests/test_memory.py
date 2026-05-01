import asyncio
from pathlib import Path
from codex_self.memory import MemoryStore


def test_memory_roundtrip(tmp_path):
    store = MemoryStore(db_path=tmp_path / "test.db")
    asyncio.run(store.set("key1", {"foo": "bar"}, scope="session"))
    val = asyncio.run(store.get("key1"))
    assert val == {"foo": "bar"}


def test_memory_ttl_expiry(tmp_path):
    store = MemoryStore(db_path=tmp_path / "test.db")
    asyncio.run(store.set("key2", "val", ttl=-1))
    val = asyncio.run(store.get("key2"))
    assert val is None


def test_memory_delete(tmp_path):
    store = MemoryStore(db_path=tmp_path / "test.db")
    asyncio.run(store.set("key3", "val"))
    asyncio.run(store.delete("key3"))
    assert asyncio.run(store.get("key3")) is None


def test_conversation_log(tmp_path):
    store = MemoryStore(db_path=tmp_path / "test.db")
    asyncio.run(store.log_conversation("sess-1", "user", "hello"))
    asyncio.run(store.log_conversation("sess-1", "assistant", "hi"))
    conv = asyncio.run(store.get_conversation("sess-1"))
    assert len(conv) == 2
    assert conv[0]["role"] == "user"
