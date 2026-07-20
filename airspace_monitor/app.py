"""FastAPI application and live WebSocket feed."""

import asyncio
import time
from collections.abc import AsyncIterator
from contextlib import asynccontextmanager
from pathlib import Path
from typing import Any

import httpx
from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.staticfiles import StaticFiles

from .aggregator import Aggregator
from .config import Settings
from .schema import Track


class ConnectionManager:
    def __init__(self) -> None:
        self.connections: set[WebSocket] = set()

    async def connect(self, websocket: WebSocket) -> None:
        await websocket.accept()
        self.connections.add(websocket)

    def disconnect(self, websocket: WebSocket) -> None:
        self.connections.discard(websocket)

    async def broadcast(self, message: dict[str, Any]) -> None:
        disconnected: list[WebSocket] = []
        for websocket in list(self.connections):
            try:
                await websocket.send_json(message)
            except Exception:
                disconnected.append(websocket)
        for websocket in disconnected:
            self.disconnect(websocket)


def create_app(settings: Settings | None = None) -> FastAPI:
    config = settings or Settings.from_env()
    manager = ConnectionManager()
    aggregator = Aggregator(config)

    async def on_update(tracks: list[Track]) -> None:
        await manager.broadcast(
            {"type": "state", "server_time": time.time(),
             "tracks": [track.model_dump() for track in tracks]}
        )

    @asynccontextmanager
    async def lifespan(_: FastAPI) -> AsyncIterator[None]:
        client = httpx.AsyncClient(timeout=config.http_timeout)
        task = asyncio.create_task(aggregator.run(client, on_update))
        try:
            yield
        finally:
            task.cancel()
            await asyncio.gather(task, return_exceptions=True)
            await client.aclose()

    app = FastAPI(title="Raspberry Pi Airspace Monitor", lifespan=lifespan)

    @app.get("/api/health")
    async def health() -> dict[str, str]:
        return {"status": "ok"}

    @app.get("/api/state")
    async def state() -> dict[str, Any]:
        return {
            "tracks": [track.model_dump() for track in aggregator.snapshot()],
            "server_time": time.time(),
        }

    @app.websocket("/ws")
    async def websocket_feed(websocket: WebSocket) -> None:
        await manager.connect(websocket)
        await websocket.send_json(
            {"type": "state", "server_time": time.time(),
             "tracks": [track.model_dump() for track in aggregator.snapshot()]}
        )
        try:
            while True:
                await websocket.receive_text()
        except WebSocketDisconnect:
            manager.disconnect(websocket)
        except Exception:
            manager.disconnect(websocket)

    static_dir = Path(__file__).parent / "static"
    app.mount("/", StaticFiles(directory=static_dir, html=True), name="static")
    return app


app = create_app()
