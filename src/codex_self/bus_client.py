"""A2A / MCP bus client for SAHIIXX ecosystem integration."""
from __future__ import annotations

import asyncio
import json
from typing import Any, Dict, Optional
from dataclasses import dataclass

import httpx
from codex_self.config import settings


@dataclass
class BusMessage:
    sender: str
    recipient: str
    action: str
    payload: Dict[str, Any]


class BusClient:
    def __init__(self, bus_url: str = settings.bus_url, agent_name: str = settings.agent_name) -> None:
        self.bus_url = bus_url.rstrip("/")
        self.agent_name = agent_name
        self._client: Optional[httpx.AsyncClient] = None
        self._heartbeat_task: Optional[asyncio.Task] = None
        self._registered = False

    async def _ensure_client(self) -> httpx.AsyncClient:
        if self._client is None or self._client.is_closed:
            self._client = httpx.AsyncClient(timeout=10.0)
        return self._client

    async def register(self, capabilities: list[dict]) -> bool:
        client = await self._ensure_client()
        payload = {
            "agent_id": self.agent_name,
            "version": settings.agent_version,
            "capabilities": capabilities,
            "endpoint": f"http://{settings.agent_name}:{settings.port}",
        }
        try:
            resp = await client.post(f"{self.bus_url}/register", json=payload)
            self._registered = resp.status_code in (200, 201, 202)
            return self._registered
        except Exception:
            return False

    async def heartbeat(self) -> bool:
        if not self._registered:
            return False
        client = await self._ensure_client()
        try:
            resp = await client.post(
                f"{self.bus_url}/heartbeat",
                json={"agent_id": self.agent_name, "timestamp": asyncio.get_event_loop().time()},
            )
            return resp.status_code == 200
        except Exception:
            return False

    async def send(self, message: BusMessage) -> Optional[Dict[str, Any]]:
        client = await self._ensure_client()
        try:
            resp = await client.post(
                f"{self.bus_url}/message",
                json={
                    "sender": message.sender,
                    "recipient": message.recipient,
                    "action": message.action,
                    "payload": message.payload,
                },
            )
            if resp.status_code == 200:
                return resp.json()
        except Exception:
            pass
        return None

    async def start_heartbeat(self, interval: float = 30.0) -> None:
        async def loop() -> None:
            while True:
                await asyncio.sleep(interval)
                await self.heartbeat()

        self._heartbeat_task = asyncio.create_task(loop())

    async def stop(self) -> None:
        if self._heartbeat_task:
            self._heartbeat_task.cancel()
            try:
                await self._heartbeat_task
            except asyncio.CancelledError:
                pass
        if self._client and not self._client.is_closed:
            await self._client.aclose()
