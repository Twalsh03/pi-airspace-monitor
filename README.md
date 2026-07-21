Disclaimer:

None of this has been tested as of yet. 

This is a WIP


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

## Hardware

Exact equipment for real reception. Everything is passive receive-only. Two
independent receive chains feed the aggregator:

- ADS-B (manned aircraft, 1090 MHz) → `dump1090-fa` → `/data/aircraft.json`
- Drone Remote ID (BLE + Wi-Fi) → `unix_rid_capture` → `rid_bridge` → `/rid.json`

### Compute (required)

| Qty | Item | Exact model / spec |
| --- | --- | --- |
| 1 | Single-board computer | Raspberry Pi 5, 8 GB (Pi 4 Model B, 4 GB minimum) |
| 1 | Power supply | Official Raspberry Pi 27 W USB-C PD (Pi 5) / 15.3 W USB-C (Pi 4) |
| 1 | Cooling | Raspberry Pi Active Cooler (Pi 5) / heatsink+fan case (Pi 4) |
| 1 | Storage | SanDisk Extreme 32 GB microSD (A2) — or Pi 5 M.2 HAT + 256 GB NVMe |
| 1 | Network | Ethernet cable (keep onboard Wi-Fi free for RID capture) |

OS: Raspberry Pi OS (64-bit, Bookworm).

### ADS-B chain — 1090 MHz (aircraft)

| Qty | Item | Exact model |
| --- | --- | --- |
| 1 | SDR receiver | FlightAware Pro Stick Plus (RTL2832U + built-in 1090 MHz filter + LNA, SMA-female) |
| 1 | Antenna | FlightAware 1090 MHz ADS-B Antenna, 66 cm / 26 in, N-female |
| 1 | Coax | N-male → SMA-male, LMR240/RG6, ~3 m |

- Budget alternative: RTL-SDR Blog V4 dongle + RTL-SDR Blog 1090/978 MHz LNA+filter.
- US-only optional: a second dongle for 978 MHz UAT (`dump978-fa`).
- `dump1090-fa` publishes `aircraft.json` natively — no extra glue.

### Drone Remote ID chain — BLE + Wi-Fi

Remote ID is broadcast over Bluetooth 4 Legacy, Bluetooth 5 Long Range (Coded
PHY), Wi-Fi Beacon (2.4 GHz), and Wi-Fi NAN. Recommended Pi-native capture uses
[`sxjack/unix_rid_capture`](https://github.com/sxjack/unix_rid_capture):

| Qty | Item | Exact model | Purpose |
| --- | --- | --- | --- |
| 1 | Wi-Fi dongle (monitor mode) | Alfa AWUS036ACH (Realtek RTL8812AU) | Wi-Fi Beacon + NAN |
| 1 | BLE sniffer | Nordic nRF52840 Dongle (PCA10059) + nRF Sniffer for BLE | Bluetooth 5 Long Range |
| — | Onboard Bluetooth | Pi's built-in BT via `bluez` | Bluetooth 4 Legacy |

- The RTL8812AU needs the third-party `rtl8812au` driver built/installed.
- Onboard BT catches only BT4 Legacy; the nRF52840 dongle is required for BT5 Long Range.
- Alternatives: an ESP32 (LilyGO TTGO T-Beam) with RID receiver firmware, or the
  official OpenDroneID Android receiver app for bench testing.

A HackRF is **not** needed: a dedicated RTL-SDR is better and cheaper for ADS-B,
and Remote ID is decoded from Bluetooth/Wi-Fi protocols (not raw RF), which a
HackRF cannot provide.

### Bill of Materials — Sources

| Component | Item | Link |
|---|---|---|
| **Compute** | Raspberry Pi 5 (8GB) | https://www.raspberrypi.com/products/raspberry-pi-5/ |
| | Raspberry Pi 4 (4GB, min fallback) | https://www.raspberrypi.com/products/raspberry-pi-4-model-b/ |
| | Official 27W USB-C PSU | https://www.raspberrypi.com/products/27w-power-supply/ |
| | Official Active Cooler | https://www.raspberrypi.com/products/active-cooler/ |
| | Storage (microSD or USB SSD) | e.g. SanDisk Extreme Pro microSD, or Samsung T7 SSD |
| | Ethernet cable | Cat5e/6, any retailer |
| **ADS-B (1090 MHz)** | FlightAware Pro Stick Plus | https://www.flightaware.com/adsb/prostick/ |
| | FlightAware 1090 MHz antenna + coax | https://www.flightaware.com/adsb/antenna/ |
| | Budget alt: RTL-SDR Blog V4 | https://www.rtl-sdr.com/buy-rtl-sdr-dvb-t-dongles/ |
| **Drone Remote ID (BLE + Wi-Fi)** | Alfa AWUS036ACH (RTL8812AU) | https://www.alfa.com.tw/products/awus036ach |
| | Nordic nRF52840 Dongle (PCA10059) | https://www.nordicsemi.com/Products/Development-hardware/nRF52840-Dongle |
| | Onboard BT (BT4 Legacy) | Built into Pi — no purchase |
| **Software** | unix_rid_capture | https://github.com/sxjack/unix_rid_capture |
| | rid_bridge (this repo) | https://github.com/Twalsh03/pi-airspace-monitor |
| | opendroneid reference tools | https://github.com/opendroneid |

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

## Drone Remote ID pipeline

On real hardware, `unix_rid_capture` receives ASTM F3411 / ASD-STAN 4709-002
messages and emits newline-delimited JSON. The bridge merges fragmented
messages and exposes the normalized endpoint consumed by the dashboard:

```
unix_rid_capture → (UDP :32001) → rid_bridge → /rid.json → airspace_monitor
```

Build and run the capture tool according to its project documentation, with
UDP output directed to port `32001`. Then run the bridge:

```sh
python -m rid_bridge
```

The bridge listens on UDP `0.0.0.0:32001` and serves `http://localhost:9000/rid.json`.
For a pipe instead of UDP, use:

```sh
RID_INPUT=stdin rid_capture -x | python -m rid_bridge
```

The bridge maps `uav id` to `id` (falling back to `mac`), UAV latitude/longitude
to the drone position, altitude/speed/heading to metric fields, `operator` to
`operator_id`, and base latitude/longitude to the pilot position. ASTM
unknown sentinels (`-1000` altitude, `255` speed, `361` heading, and `(0, 0)`
position) are omitted. Fields from separate messages for the same ID are
merged, and stale records expire.

Bridge environment variables:

| Environment variable | Default | Meaning |
| --- | --- | --- |
| `RID_BRIDGE_HOST` | `0.0.0.0` | HTTP bind address |
| `RID_BRIDGE_PORT` | `9000` | HTTP port |
| `RID_INPUT` | `udp` | `udp` or `stdin` |
| `RID_UDP_HOST` | `0.0.0.0` | UDP bind address |
| `RID_UDP_PORT` | `32001` | UDP input port |
| `STALE_SECONDS` | `30.0` | Record expiry age |

Install `deploy/rid-bridge.service` alongside the main service, editing the
placeholder user and paths. The unit loads optional
`/etc/airspace-monitor.env`, restarts on failure, and runs as `pi`.

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