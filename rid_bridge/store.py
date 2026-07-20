"""Merged and expiring Remote ID state."""

import time
from typing import Any


class DroneStore:
    def __init__(self, stale_seconds: float = 30.0) -> None:
        self.stale_seconds = stale_seconds
        self._drones: dict[str, dict[str, Any]] = {}

    def merge(self, partial: dict[str, Any]) -> None:
        key = partial.get("key") or partial.get("id")
        if not isinstance(key, str) or not key:
            return
        mac = partial.get("mac")
        if isinstance(mac, str) and key not in self._drones:
            for existing_key, existing in self._drones.items():
                if existing.get("mac") == mac:
                    if key == mac and existing.get("id") not in (None, mac):
                        key = existing_key
                    else:
                        self._drones[key] = self._drones.pop(existing_key)
                    break
        current = self._drones.setdefault(key, {"key": key})
        for field, value in partial.items():
            if field != "key" and value is not None:
                if field == "id" and value == mac and current.get("id") not in (None, mac):
                    continue
                current[field] = value
        current["last_seen"] = time.time()

    def prune(self, now: float) -> None:
        cutoff = now - self.stale_seconds
        self._drones = {
            key: drone
            for key, drone in self._drones.items()
            if float(drone["last_seen"]) >= cutoff
        }

    def render(self) -> dict[str, Any]:
        drones: list[dict[str, Any]] = []
        for drone in self._drones.values():
            if not isinstance(drone.get("lat"), (int, float)) or not isinstance(
                drone.get("lon"), (int, float)
            ):
                continue
            output: dict[str, Any] = {
                "id": drone["id"],
                "id_type": drone.get("id_type", "serial_number"),
                "lat": drone["lat"],
                "lon": drone["lon"],
                "last_seen": drone["last_seen"],
            }
            for field in ("alt_msl_m", "speed_mps", "heading_deg", "operator_id", "mac"):
                if drone.get(field) is not None:
                    output[field] = drone[field]
            pilot = drone.get("pilot")
            if isinstance(pilot, dict):
                output["pilot"] = pilot
            drones.append(output)
        return {"timestamp": time.time(), "drones": drones}
