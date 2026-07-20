"""Serve moving sample dump1090 and Remote ID responses."""
import json
import threading
import time
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

START = time.monotonic()

def payloads() -> tuple[dict, dict]:
    step = (time.monotonic() - START) * 0.0005
    return (
        {"now": time.time(), "messages": 1, "aircraft": [
            {"hex": "mock01", "flight": "MOCK101", "lat": 37.61 + step, "lon": -122.38 + step,
             "alt_baro": 8500, "gs": 180, "track": 118, "seen": 0.1},
            {"hex": "mock02", "flight": "MOCK202", "lat": 37.70 - step, "lon": -122.30,
             "alt_baro": 4200, "gs": 90, "track": 250, "seen": 0.2},
        ]},
        {"timestamp": time.time(), "drones": [{
            "id": "MOCK-DRONE-1", "id_type": "serial_number", "lat": 37.765 + step,
            "lon": -122.419, "alt_msl_m": 100, "speed_mps": 5, "heading_deg": 270,
            "pilot": {"lat": 37.766, "lon": -122.418, "alt_msl_m": 15}
        }]},
    )

class Handler(BaseHTTPRequestHandler):
    def do_GET(self) -> None:
        aircraft, rid = payloads()
        if self.server.server_port == 8080 and self.path == "/data/aircraft.json":
            body = aircraft
        elif self.server.server_port == 9000 and self.path == "/rid.json":
            body = rid
        else:
            self.send_error(404)
            return
        encoded = json.dumps(body).encode()
        self.send_response(200)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(encoded)))
        self.end_headers()
        self.wfile.write(encoded)

    def log_message(self, *_: object) -> None:
        return

def main() -> None:
    servers = [ThreadingHTTPServer(("0.0.0.0", port), Handler) for port in (8080, 9000)]
    for server in servers:
        threading.Thread(target=server.serve_forever, daemon=True).start()
    print("Mock sources listening on :8080 and :9000")
    try:
        while True:
            time.sleep(3600)
    except KeyboardInterrupt:
        for server in servers:
            server.shutdown()

if __name__ == "__main__":
    main()
