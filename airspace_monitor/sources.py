"""Input adapters for dump1090 and Remote ID receivers."""

import logging
import time
from typing import Any

import httpx

from .schema import Track

LOGGER = logging.getLogger(__name__)


def _number(value: Any) -> float | None:
    if isinstance(value, bool):
        return None
    if isinstance(value, (int, float)):
        return float(value)
    return None


async def _get_json(client: httpx.AsyncClient, url: str, source: str) -> Any:
    try:
        response = await client.get(url)
        response.raise_for_status()
        return response.json()
    except (httpx.HTTPError, ValueError) as exc:
        LOGGER.warning("%s source unavailable or invalid: %s", source, exc)
        return None


async def fetch_aircraft(client: httpx.AsyncClient, url: str) -> list[Track]:
    payload = await _get_json(client, url, "dump1090")
    if not isinstance(payload, dict) or not isinstance(payload.get("aircraft"), list):
        LOGGER.warning("dump1090 response has no aircraft list")
        return []
    ingest_time = _number(payload.get("now")) or time.time()
    tracks: list[Track] = []
    for aircraft in payload["aircraft"]:
        if not isinstance(aircraft, dict):
            continue
        lat = _number(aircraft.get("lat"))
        lon = _number(aircraft.get("lon"))
        aircraft_id = aircraft.get("hex")
        if lat is None or lon is None or not isinstance(aircraft_id, str):
            continue
        altitude = _number(aircraft.get("alt_baro"))
        speed = _number(aircraft.get("gs"))
        flight = aircraft.get("flight")
        tracks.append(
            Track(
                id=aircraft_id,
                type="aircraft",
                lat=lat,
                lon=lon,
                alt_m=altitude * 0.3048 if altitude is not None else None,
                callsign=flight.strip() or None if isinstance(flight, str) else None,
                speed_mps=speed * 0.514444 if speed is not None else None,
                heading_deg=_number(aircraft.get("track")),
                extra={
                    key: aircraft[key]
                    for key in ("squawk", "seen", "seen_pos")
                    if key in aircraft
                },
                last_seen=ingest_time,
                source="dump1090",
            )
        )
    return tracks


async def fetch_rid(client: httpx.AsyncClient, url: str) -> list[Track]:
    payload = await _get_json(client, url, "rid")
    if not isinstance(payload, dict) or not isinstance(payload.get("drones"), list):
        LOGGER.warning("RID response has no drones list")
        return []
    ingest_time = time.time()
    source_timestamp = _number(payload.get("timestamp"))
    tracks: list[Track] = []
    for drone in payload["drones"]:
        if not isinstance(drone, dict):
            continue
        drone_id = drone.get("id")
        lat = _number(drone.get("lat"))
        lon = _number(drone.get("lon"))
        if not isinstance(drone_id, str) or lat is None or lon is None:
            continue
        last_seen = _number(drone.get("last_seen")) or source_timestamp or ingest_time
        tracks.append(
            Track(
                id=drone_id,
                type="drone",
                lat=lat,
                lon=lon,
                alt_m=_number(drone.get("alt_msl_m")),
                speed_mps=_number(drone.get("speed_mps")),
                heading_deg=_number(drone.get("heading_deg")),
                extra={
                    key: drone[key]
                    for key in ("id_type", "height_agl_m", "vertical_speed_mps", "rssi",
                                "operator_id", "description")
                    if key in drone
                },
                last_seen=last_seen,
                source="rid",
            )
        )
        pilot = drone.get("pilot")
        if isinstance(pilot, dict):
            pilot_lat = _number(pilot.get("lat"))
            pilot_lon = _number(pilot.get("lon"))
            if pilot_lat is not None and pilot_lon is not None:
                tracks.append(
                    Track(
                        id=f"{drone_id}:pilot",
                        type="pilot",
                        lat=pilot_lat,
                        lon=pilot_lon,
                        alt_m=_number(pilot.get("alt_msl_m")),
                        extra={"drone_id": drone_id},
                        last_seen=last_seen,
                        source="rid",
                    )
                )
    return tracks
