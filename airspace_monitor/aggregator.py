"""In-memory track aggregation and pruning."""

import asyncio
import logging
import time
from collections.abc import Awaitable, Callable

import httpx

from .config import Settings
from .schema import Track
from .sources import fetch_aircraft, fetch_rid

LOGGER = logging.getLogger(__name__)
SnapshotCallback = Callable[[list[Track]], Awaitable[None]]


class Aggregator:
    def __init__(self, settings: Settings) -> None:
        self.settings = settings
        self.tracks: dict[str, Track] = {}

    def ingest(self, tracks: list[Track]) -> None:
        now = time.time()
        for track in tracks:
            self.tracks[track.id] = track.model_copy(update={"last_seen": now})

    def prune(self, now: float) -> None:
        cutoff = now - self.settings.stale_seconds
        self.tracks = {
            track_id: track
            for track_id, track in self.tracks.items()
            if track.last_seen >= cutoff
        }

    def snapshot(self) -> list[Track]:
        return list(self.tracks.values())

    async def run(self, client: httpx.AsyncClient, on_update: SnapshotCallback) -> None:
        while True:
            try:
                aircraft, rid = await asyncio.gather(
                    fetch_aircraft(client, self.settings.dump1090_url),
                    fetch_rid(client, self.settings.rid_url),
                )
                self.ingest(aircraft + rid)
                self.prune(time.time())
                await on_update(self.snapshot())
            except asyncio.CancelledError:
                raise
            except Exception:
                LOGGER.exception("aggregator cycle failed")
            await asyncio.sleep(self.settings.poll_interval)
