"""Async readers for unix_rid_capture output."""

import asyncio
import json
import logging
import sys

from .parse import parse_message
from .store import DroneStore

LOGGER = logging.getLogger(__name__)


def _consume_line(line: str, store: DroneStore) -> None:
    try:
        message = json.loads(line)
    except json.JSONDecodeError:
        LOGGER.debug("Ignoring malformed RID line")
        return
    if not isinstance(message, dict):
        LOGGER.debug("Ignoring non-object RID line")
        return
    partial = parse_message(message)
    if partial is None:
        LOGGER.debug("Ignoring RID line without drone identity")
        return
    store.merge(partial)


class _DatagramProtocol(asyncio.DatagramProtocol):
    def __init__(self, store: DroneStore) -> None:
        self.store = store

    def datagram_received(self, data: bytes, _: tuple[str, int]) -> None:
        for line in data.decode("utf-8", errors="replace").splitlines():
            _consume_line(line, self.store)

    def error_received(self, exc: Exception) -> None:
        LOGGER.warning("RID UDP error: %s", exc)


async def run_udp(store: DroneStore, host: str, port: int) -> None:
    loop = asyncio.get_running_loop()
    transport, _ = await loop.create_datagram_endpoint(
        lambda: _DatagramProtocol(store),
        local_addr=(host, port),
    )
    try:
        await asyncio.Future()
    finally:
        transport.close()


async def run_stdin(store: DroneStore) -> None:
    while True:
        line = await asyncio.to_thread(sys.stdin.readline)
        if not line:
            return
        _consume_line(line, store)
