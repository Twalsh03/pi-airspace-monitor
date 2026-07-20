import time

from rid_bridge.parse import parse_message
from rid_bridge.store import DroneStore


def test_parser_drops_sentinels_and_invalid_position() -> None:
    partial = parse_message({
        "mac": "aa:bb",
        "uav id": "DRONE",
        "uav latitude": 0.0,
        "uav longitude": 0.0,
        "uav altitude": -1000,
        "uav speed": 255,
        "uav heading": 361,
    })
    assert partial is not None
    assert "lat" not in partial
    assert "lon" not in partial
    assert partial["alt_msl_m"] is None
    assert partial["speed_mps"] is None
    assert partial["heading_deg"] is None


def test_fragments_merge_and_position_is_retained() -> None:
    store = DroneStore()
    first = parse_message({
        "mac": "aa:bb",
        "uav id": "DRONE",
        "uav latitude": 51.5,
        "uav longitude": -0.12,
    })
    second = parse_message({"mac": "aa:bb", "operator": "OPERATOR"})
    assert first is not None and second is not None
    store.merge(first)
    store.merge(second)
    drone = store.render()["drones"][0]
    assert drone["id"] == "DRONE"
    assert drone["lat"] == 51.5
    assert drone["operator_id"] == "OPERATOR"


def test_keying_uses_id_then_mac() -> None:
    store = DroneStore()
    by_id = parse_message({
        "mac": "aa:bb", "uav id": "DRONE", "uav latitude": 1, "uav longitude": 2
    })
    by_mac = parse_message({"mac": "cc:dd", "uav latitude": 3, "uav longitude": 4})
    assert by_id is not None and by_mac is not None
    store.merge(by_id)
    store.merge(by_mac)
    assert {drone["id"] for drone in store.render()["drones"]} == {"DRONE", "cc:dd"}


def test_prune_removes_old_drone() -> None:
    store = DroneStore(stale_seconds=1)
    partial = parse_message({"mac": "aa:bb", "uav latitude": 1, "uav longitude": 2})
    assert partial is not None
    store.merge(partial)
    store.prune(time.time() + 2)
    assert store.render()["drones"] == []
