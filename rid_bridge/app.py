"""FastAPI application for the RID bridge."""

import asyncio
import logging
import time
from collections.abc import AsyncIterator
from contextlib import asynccontextmanager
from typing import Any

from fastapi import FastAPI

from .config import Settings
from .readers import run_stdin, run_udp
from .store import DroneStore

LOGGER = logging.getLogger(__name__)


def create_app(settings: Settings | None = None) -> FastAPI:
    config = settings or Settings.from_env()
    store = DroneStore(config.stale_seconds)

    async def prune_loop() -> None:
        while True:
            await asyncio.sleep(min(config.stale_seconds, 1.0))
            store.prune(time.time())

    @asynccontextmanager
    async def lifespan(_: FastAPI) -> AsyncIterator[None]:
        if config.input_mode == "udp":
            reader = asyncio.create_task(run_udp(store, config.udp_host, config.udp_port))
        elif config.input_mode == "stdin":
            reader = asyncio.create_task(run_stdin(store))
        else:
            raise ValueError(f"Unsupported RID_INPUT: {config.input_mode}")
        pruner = asyncio.create_task(prune_loop())
        try:
            yield
        finally:
            reader.cancel()
            pruner.cancel()
            await asyncio.gather(reader, pruner, return_exceptions=True)

    app = FastAPI(title="RID Bridge", lifespan=lifespan)

    @app.get("/rid.json")
    async def rid() -> dict[str, Any]:
        return store.render()

    @app.get("/health")
    async def health() -> dict[str, str]:
        return {"status": "ok"}

    return app


app = create_app()
