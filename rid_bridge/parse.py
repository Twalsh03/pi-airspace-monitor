"""Pure parsing of unix_rid_capture messages."""

from typing import Any


def _number(value: Any) -> float | None:
    if isinstance(value, bool):
        return None
    if isinstance(value, (int, float)):
        return float(value)
    return None


def _text(value: Any) -> str | None:
    if isinstance(value, str) and value.strip():
        return value.strip()
    return None


def _position(latitude: Any, longitude: Any) -> tuple[float, float] | None:
    lat = _number(latitude)
    lon = _number(longitude)
    if lat is None or lon is None or (lat == 0.0 and lon == 0.0):
        return None
    return lat, lon


def parse_message(message: dict[str, Any]) -> dict[str, Any] | None:
    """Map one capture object to a partial normalized drone record."""
    drone_id = _text(message.get("uav id"))
    mac = _text(message.get("mac"))
    key = drone_id or mac
    if key is None:
        return None

    partial: dict[str, Any] = {
        "key": key,
        "id": drone_id or mac,
        "id_type": "serial_number",
        "mac": mac,
        "operator_id": _text(message.get("operator")),
        "alt_msl_m": _number(message.get("uav altitude")),
        "speed_mps": _number(message.get("uav speed")),
        "heading_deg": _number(message.get("uav heading")),
        "last_seen": _number(message.get("unix time")),
    }
    if partial["alt_msl_m"] == -1000:
        partial["alt_msl_m"] = None
    if partial["speed_mps"] == 255:
        partial["speed_mps"] = None
    if partial["heading_deg"] == 361:
        partial["heading_deg"] = None

    position = _position(message.get("uav latitude"), message.get("uav longitude"))
    if position is not None:
        partial["lat"], partial["lon"] = position

    pilot_position = _position(message.get("base latitude"), message.get("base longitude"))
    if pilot_position is not None:
        partial["pilot"] = {"lat": pilot_position[0], "lon": pilot_position[1]}

    return partial
