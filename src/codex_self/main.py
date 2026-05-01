"""FastAPI ASGI application with WebSocket dashboard and ecosystem integration."""
from __future__ import annotations

import asyncio
import json
import os
from contextlib import asynccontextmanager
from typing import Any, Dict, List, Optional

from fastapi import FastAPI, WebSocket, WebSocketDisconnect, HTTPException
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware

from codex_self.config import settings
from codex_self.agent import build_identity, AgentIdentity
from codex_self.health import HealthEngine
from codex_self.memory import MemoryStore, MemoryEntry
from codex_self.sandbox import SandboxGuard
from codex_self.skills import SkillRegistry, Skill
from codex_self.bus_client import BusClient, BusMessage

# ── Global singletons ──────────────────────────────────────────
identity: AgentIdentity = build_identity(settings.agent_name, settings.agent_version, settings.agent_role)
health_engine = HealthEngine()
memory_store = MemoryStore()
sandbox_guard = SandboxGuard()
skill_registry = SkillRegistry()
bus_client = BusClient()

# WebSocket connection manager
class ConnectionManager:
    def __init__(self) -> None:
        self.active: List[WebSocket] = []

    async def connect(self, websocket: WebSocket) -> None:
        await websocket.accept()
        self.active.append(websocket)

    def disconnect(self, websocket: WebSocket) -> None:
        if websocket in self.active:
            self.active.remove(websocket)

    async def broadcast(self, message: Dict[str, Any]) -> None:
        dead: List[WebSocket] = []
        for ws in self.active:
            try:
                await ws.send_json(message)
            except Exception:
                dead.append(ws)
        for ws in dead:
            self.active.remove(ws)

manager = ConnectionManager()

# ── Lifespan ─────────────────────────────────────────────────────
@asynccontextmanager
async def lifespan(app: FastAPI):
    # Fire-and-forget bus registration so DNS delays don't block startup
    async def _register() -> None:
        try:
            ok = await bus_client.register(identity.to_dict()["capabilities"])
            if ok:
                await bus_client.start_heartbeat(interval=30.0)
        except Exception:
            pass

    asyncio.create_task(_register())
    yield
    # Shutdown
    try:
        await bus_client.stop()
    except Exception:
        pass

app = FastAPI(
    title="Codex Self",
    description="Self-aware agent runtime and dashboard for the SAHIIXX ecosystem.",
    version=settings.agent_version,
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Serve dashboard static files if they exist
dashboard_dir = os.path.join(os.path.dirname(__file__), "..", "..", "dashboard")
if os.path.isdir(dashboard_dir):
    app.mount("/dashboard", StaticFiles(directory=dashboard_dir, html=True), name="dashboard")

# ── Health & Diagnostics ──────────────────────────────────────
@app.get("/health", tags=["health"])
async def health() -> JSONResponse:
    return JSONResponse(content=health_engine.quick_check())

@app.get("/diagnose", tags=["health"])
async def diagnose() -> JSONResponse:
    report = await health_engine.diagnose()
    await manager.broadcast({"event": "diagnose", "report": report.__dict__})
    return JSONResponse(content=report.__dict__)

# ── Identity ─────────────────────────────────────────────────────
@app.get("/identity", tags=["identity"])
async def get_identity() -> JSONResponse:
    return JSONResponse(content=identity.to_dict())

@app.get("/capabilities", tags=["identity"])
async def get_capabilities() -> JSONResponse:
    return JSONResponse(content=[c.__dict__ for c in identity.capabilities])

# ── Skills ───────────────────────────────────────────────────────
@app.get("/skills", tags=["skills"])
async def list_skills(query: Optional[str] = None) -> JSONResponse:
    skills = skill_registry.list_skills()
    if query:
        skills = skill_registry.match(query)
    return JSONResponse(content=[s.to_dict() for s in skills])

@app.post("/skills", tags=["skills"])
async def register_skill(skill_data: Dict[str, Any]) -> JSONResponse:
    skill = Skill.from_dict(skill_data)
    skill_registry.register(skill)
    return JSONResponse(content={"registered": skill.name})

# ── Memory ───────────────────────────────────────────────────────
@app.get("/memory/{key}", tags=["memory"])
async def memory_get(key: str) -> JSONResponse:
    value = await memory_store.get(key)
    if value is None:
        raise HTTPException(status_code=404, detail="Key not found")
    return JSONResponse(content={"key": key, "value": value})

@app.post("/memory/{key}", tags=["memory"])
async def memory_set(key: str, body: Dict[str, Any]) -> JSONResponse:
    scope = body.get("scope", "global")
    ttl = body.get("ttl")
    await memory_store.set(key, body.get("value"), scope=scope, ttl=ttl)
    return JSONResponse(content={"key": key, "status": "stored"})

@app.delete("/memory/{key}", tags=["memory"])
async def memory_delete(key: str) -> JSONResponse:
    await memory_store.delete(key)
    return JSONResponse(content={"key": key, "status": "deleted"})

@app.get("/memory", tags=["memory"])
async def memory_list(scope: Optional[str] = None) -> JSONResponse:
    keys = await memory_store.list_keys(scope)
    return JSONResponse(content={"keys": keys, "scope": scope})

@app.post("/memory/prune", tags=["memory"])
async def memory_prune(max_age: int = 604800) -> JSONResponse:
    deleted = await memory_store.prune(max_age)
    return JSONResponse(content={"deleted": deleted})

# ── Sandbox ──────────────────────────────────────────────────────
@app.post("/sandbox/check", tags=["sandbox"])
async def sandbox_check(body: Dict[str, Any]) -> JSONResponse:
    path = body.get("path", "")
    action = body.get("action", "read")
    allowed = sandbox_guard.check(path, action)
    return JSONResponse(content={"path": path, "action": action, "allowed": allowed})

@app.get("/sandbox/audit", tags=["sandbox"])
async def sandbox_audit(limit: int = 50) -> JSONResponse:
    trail = sandbox_guard.audit_trail()
    return JSONResponse(content={"events": trail[-limit:]})

# ── Bus ──────────────────────────────────────────────────────────
@app.get("/bus/status", tags=["bus"])
async def bus_status() -> JSONResponse:
    reachable = await bus_client.heartbeat()
    return JSONResponse(content={"bus_url": settings.bus_url, "reachable": reachable, "registered": bus_client._registered})

@app.post("/bus/register", tags=["bus"])
async def bus_register() -> JSONResponse:
    ok = await bus_client.register(identity.to_dict()["capabilities"])
    return JSONResponse(content={"registered": ok})

@app.post("/bus/send", tags=["bus"])
async def bus_send(body: Dict[str, Any]) -> JSONResponse:
    msg = BusMessage(
        sender=body.get("sender", settings.agent_name),
        recipient=body["recipient"],
        action=body["action"],
        payload=body.get("payload", {}),
    )
    resp = await bus_client.send(msg)
    return JSONResponse(content={"response": resp})

# ── WebSocket ────────────────────────────────────────────────────
@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket) -> None:
    await manager.connect(websocket)
    try:
        await websocket.send_json({"event": "connected", "agent": identity.to_dict()})
        while True:
            data = await websocket.receive_json()
            action = data.get("action")
            if action == "ping":
                await websocket.send_json({"event": "pong", "timestamp": asyncio.get_event_loop().time()})
            elif action == "diagnose":
                report = await health_engine.diagnose()
                await websocket.send_json({"event": "diagnose", "report": report.__dict__})
            elif action == "memory.get":
                key = data.get("key")
                val = await memory_store.get(key) if key else None
                await websocket.send_json({"event": "memory.get", "key": key, "value": val})
            elif action == "identity":
                await websocket.send_json({"event": "identity", "agent": identity.to_dict()})
            else:
                await websocket.send_json({"event": "error", "message": f"Unknown action: {action}"})
    except WebSocketDisconnect:
        manager.disconnect(websocket)
    except Exception as e:
        manager.disconnect(websocket)
        try:
            await websocket.close(code=1011)
        except Exception:
            pass

# ── Dashboard fallback ─────────────────────────────────────────
@app.get("/", tags=["dashboard"])
async def root() -> HTMLResponse:
    html_path = os.path.join(dashboard_dir, "index.html")
    if os.path.isfile(html_path):
        with open(html_path, "r", encoding="utf-8") as f:
            return HTMLResponse(content=f.read())
    return HTMLResponse(content="<h1>Codex Self is running</h1><p>Dashboard files not found.</p>")

# ── CLI entry ───────────────────────────────────────────────────
def cli_entry() -> None:
    import uvicorn
    uvicorn.run(
        "codex_self.main:app",
        host=settings.host,
        port=settings.port,
        log_level=settings.log_level,
        reload=False,
    )

if __name__ == "__main__":
    cli_entry()
