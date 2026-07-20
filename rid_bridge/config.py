"""RID bridge configuration."""

import os
from dataclasses import dataclass


@dataclass(frozen=True)
class Settings:
    host: str = "0.0.0.0"
    port: int = 9000
    input_mode: str = "udp"
    udp_host: str = "0.0.0.0"
    udp_port: int = 32001
    stale_seconds: float = 30.0

    @classmethod
    def from_env(cls) -> "Settings":
        return cls(
            host=os.getenv("RID_BRIDGE_HOST", cls.host),
            port=int(os.getenv("RID_BRIDGE_PORT", str(cls.port))),
            input_mode=os.getenv("RID_INPUT", cls.input_mode).lower(),
            udp_host=os.getenv("RID_UDP_HOST", cls.udp_host),
            udp_port=int(os.getenv("RID_UDP_PORT", str(cls.udp_port))),
            stale_seconds=float(os.getenv("STALE_SECONDS", str(cls.stale_seconds))),
        )
