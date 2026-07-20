"""Application configuration."""

import os
from dataclasses import dataclass


@dataclass(frozen=True)
class Settings:
    dump1090_url: str = "http://localhost:8080/data/aircraft.json"
    rid_url: str = "http://localhost:9000/rid.json"
    host: str = "0.0.0.0"
    port: int = 8000
    poll_interval: float = 1.0
    stale_seconds: float = 30.0
    http_timeout: float = 2.0

    @classmethod
    def from_env(cls) -> "Settings":
        return cls(
            dump1090_url=os.getenv("DUMP1090_URL", cls.dump1090_url),
            rid_url=os.getenv("RID_URL", cls.rid_url),
            host=os.getenv("HOST", cls.host),
            port=int(os.getenv("PORT", str(cls.port))),
            poll_interval=float(os.getenv("POLL_INTERVAL", str(cls.poll_interval))),
            stale_seconds=float(os.getenv("STALE_SECONDS", str(cls.stale_seconds))),
            http_timeout=float(os.getenv("HTTP_TIMEOUT", str(cls.http_timeout))),
        )
