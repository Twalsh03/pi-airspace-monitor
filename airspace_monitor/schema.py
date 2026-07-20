"""Normalized airspace track schema."""

from typing import Any, Literal

from pydantic import BaseModel, ConfigDict

TrackType = Literal["aircraft", "drone", "pilot"]
TrackSource = Literal["dump1090", "rid"]


class Track(BaseModel):
    model_config = ConfigDict(extra="forbid")

    id: str
    type: TrackType
    lat: float
    lon: float
    alt_m: float | None = None
    callsign: str | None = None
    speed_mps: float | None = None
    heading_deg: float | None = None
    extra: dict[str, Any] = {}
    last_seen: float
    source: TrackSource
