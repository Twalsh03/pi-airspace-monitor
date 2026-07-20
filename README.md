# Raspberry Pi Airspace Monitor

The Raspberry Pi Airspace Monitor is a passive, receive-only dashboard for live
manned aircraft (ADS-B) and drones (OpenDroneID-style Remote ID). It does not
transmit, control aircraft, jam signals, or interact with aircraft systems.
Use it in accordance with local aviation, radio, privacy, and data-protection
rules.

## Architecture

One Python process runs an async poller, FastAPI API/WebSocket server, and the
static Leaflet UI:

```
dump1090-fa ─┐
             ├─> async Aggregator ─> FastAPI /api/state + /ws ─> Leaflet map
Remote ID ───┘
```

The single process and one systemd service serve both API and UI, which keeps
deployment simple. The dashboard is intended for a local network; it can be
put behind an authenticated reverse proxy later if remote access is needed.

## Install and run

Requires Python 3.11+:

```sh
python3 -m venv .venv
. .venv/bin/activate
pip install -r requirements.txt
python -m airspace_monitor
```

Open `http://localhost:8000/`. With real sources, set `DUMP1090_URL` to the
dump1090-fa `data/aircraft.json` endpoint and `RID_URL` to the receiver endpoint.

### Local mock sources

In one terminal:

```sh
python tools/mock_sources.py
```

In another terminal:

```sh
python -m airspace_monitor
```

The mock serves moving aircraft at `http://localhost:8080/data/aircraft.json`
and moving Remote ID data at `http://localhost:9000/rid.json`.

## Configuration

| Environment variable | Default | Meaning |
| --- | --- | --- |
| `DUMP1090_URL` | `http://localhost:8080/data/aircraft.json` | dump1090 endpoint |
| `RID_URL` | `http://localhost:9000/rid.json` | Remote ID endpoint |
| `HOST` | `0.0.0.0` | Web server bind address |
| `PORT` | `8000` | Web server port |
| `POLL_INTERVAL` | `1.0` | Source polling interval, seconds |
| `STALE_SECONDS` | `30.0` | Track expiry age, seconds |
| `HTTP_TIMEOUT` | `2.0` | Source HTTP timeout, seconds |

## Input schemas

### dump1090-fa

The monitor consumes the standard object with an `aircraft` array. Each
aircraft needs numeric `lat`, `lon`, and string `hex`; optional fields include
`flight`, `alt_baro` (feet, or `"ground"`), `gs` (knots), `track`, `seen`,
`seen_pos`, and `squawk`. Aircraft without position are skipped. Altitude is
normalized to meters and ground speed to meters per second.
See `examples/aircraft.json`.

### Remote ID

The RID receiver contract is an object with a numeric `timestamp` and `drones`
array:

```json
{
  "timestamp": 1758400000.0,
  "drones": [{
    "id": "1596F3B3AA1EX9K",
    "id_type": "serial_number",
    "lat": 37.7649, "lon": -122.4194,
    "alt_msl_m": 120.5, "height_agl_m": 95.0,
    "speed_mps": 6.2, "vertical_speed_mps": 0.5,
    "heading_deg": 275.0, "rssi": -68,
    "operator_id": "FA3ABC123DEF", "description": "DJI Mavic 3",
    "pilot": {"lat": 37.766, "lon": -122.418, "alt_msl_m": 15.0},
    "last_seen": 1758400000.0
  }]
}
```

`id_type` is `serial_number`, `caa_registration`, or `utm_uuid`.
`height_agl_m`, signal/operator/description fields, `pilot`, and `last_seen`
are optional. A drone with a pilot location produces a separate pilot track
whose ID is `<drone id>:pilot`; pilot extras include `drone_id`.
See `examples/rid.json`.

## Systemd deployment

Copy the unit, then edit `User`, `WorkingDirectory`, and `ExecStart` for the
installation and virtual environment (the supplied placeholders use user
`pi` and `/home/pi/pi-airspace-monitor`):

```sh
sudo cp deploy/airspace-monitor.service /etc/systemd/system/
sudoedit /etc/systemd/system/airspace-monitor.service
sudo systemctl daemon-reload
sudo systemctl enable --now airspace-monitor
systemctl status airspace-monitor
```

An optional `/etc/airspace-monitor.env` is loaded by the unit for environment
configuration.