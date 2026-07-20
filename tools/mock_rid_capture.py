"""Replay fragmented unix_rid_capture messages to stdout or UDP."""

import argparse
import json
import socket
import sys
import time
from typing import Any

MESSAGES: list[dict[str, Any]] = [
    {
        "mac": "ac:67:b2:09:50:d4",
        "uav id": "SERIAL123",
        "uav latitude": 51.5,
        "uav longitude": -0.12,
        "uav altitude": -1000,
        "uav heading": 361,
        "uav speed": 255,
        "seconds": 5,
    },
    {
        "mac": "ac:67:b2:09:50:d4",
        "operator": "GBR-OP-ZZZZZZZZZZZZ",
        "uav altitude": 120,
        "uav heading": 270,
        "uav speed": 6,
        "base latitude": 51.49,
        "base longitude": -0.11,
        "unix time": 1546300800,
    },
    {"debug": "rx packets 92 (0)"},
    {
        "mac": "bb:11:22:33:44:55",
        "uav latitude": 0.0,
        "uav longitude": 0.0,
        "uav altitude": 80,
    },
    {
        "mac": "bb:11:22:33:44:55",
        "uav id": "MAC-FALLBACK-DRONE",
        "uav latitude": 51.51,
        "uav longitude": -0.1,
    },
]


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--udp", action="store_true", help="send JSON lines to UDP")
    parser.add_argument("--host", default="127.0.0.1")
    parser.add_argument("--port", type=int, default=32001)
    parser.add_argument("--delay", type=float, default=0.1)
    args = parser.parse_args()
    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM) if args.udp else None
    try:
        for message in MESSAGES:
            line = (json.dumps(message) + "\n").encode()
            if sock is None:
                sys.stdout.buffer.write(line)
                sys.stdout.buffer.flush()
            else:
                sock.sendto(line, (args.host, args.port))
            time.sleep(args.delay)
    finally:
        if sock is not None:
            sock.close()


if __name__ == "__main__":
    main()
