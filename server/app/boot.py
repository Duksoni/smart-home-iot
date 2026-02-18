"""
Boot-time state hydration.

Reads the latest value for every known sensor and actuator from InfluxDB
and populates HouseState before the server begins serving requests.

This means the REST API returns real data immediately after a restart
instead of showing empty readings until the next MQTT batch arrives.
"""

import time
from datetime import timezone

from influxdb_client import QueryApi

from .config import Settings
from .state import HouseState, _SENSOR_MEASUREMENTS, _ACTUATOR_MEASUREMENTS


def hydrate_state_from_influx(query_api: QueryApi, settings: Settings) -> None:
    """
    Query the last recorded point for every (measurement, code) combination
    in the sensor and actuator measurement sets, then seed HouseState.

    Safe to call even if InfluxDB is empty or unreachable — errors are logged
    and the server continues with an empty (live-only) state.
    """
    house = HouseState()

    try:
        _load_sensors(query_api, settings, house)
        _load_actuators(query_api, settings, house)
        print("[boot] State hydration from InfluxDB complete.")
    except Exception as exc:
        print(f"[boot] State hydration failed (server will start with empty state): {exc}")


# ── Internal helpers ──────────────────────────────────────────────────────────

def _build_flux(bucket: str, measurements: frozenset[str]) -> str:
    """
    Return a Flux query that yields the *last* value point for every
    (measurement, code) combination found within the last 30 days.

    We group by _measurement and code tag so that e.g. DHT1_temperature and
    DHT1_humidity are returned as separate rows even though they share a code.
    """
    measurement_filter = " or ".join(
        f'r._measurement == "{m}"' for m in sorted(measurements)
    )
    return f"""
from(bucket: "{bucket}")
  |> range(start: -30d)
  |> filter(fn: (r) => {measurement_filter})
  |> filter(fn: (r) => r._field == "value")
  |> group(columns: ["_measurement", "code"])
  |> last()
"""


def _record_to_payload(record) -> dict | None:
    """
    Convert a single InfluxDB FluxRecord into a dict that matches the shape
    of an MQTT payload as produced by the simulation components.
    Returns None if the record is missing the mandatory `code` tag.
    """
    code = record.values.get("code")
    if not code:
        return None

    # _time is a datetime with tzinfo; convert to a Unix timestamp float.
    ts = record.get_time()
    received_at = ts.replace(tzinfo=timezone.utc).timestamp() if ts else time.time()

    payload: dict = {
        "measurement": record.get_measurement(),
        "code": code,
        "value": record.get_value(),
        "received_at": received_at,
    }

    # Restore optional tags when present
    for tag in ("simulated", "device", "runs_on", "name", "action", "state"):
        val = record.values.get(tag)
        if val is not None:
            payload[tag] = val

    return payload


def _load_sensors(query_api: QueryApi, settings: Settings, house: HouseState) -> None:
    flux = _build_flux(settings.influxdb_bucket, _SENSOR_MEASUREMENTS)
    tables = query_api.query(flux, org=settings.influxdb_org)
    count = 0
    for table in tables:
        for record in table.records:
            payload = _record_to_payload(record)
            if payload is None:
                continue
            # update_sensor uses {CODE}_{measurement} keying internally
            house.update_sensor(payload["code"].upper(), payload)
            count += 1
    print(f"[boot] Loaded {count} sensor reading(s) from InfluxDB.")


def _load_actuators(query_api: QueryApi, settings: Settings, house: HouseState) -> None:
    flux = _build_flux(settings.influxdb_bucket, _ACTUATOR_MEASUREMENTS)
    tables = query_api.query(flux, org=settings.influxdb_org)
    count = 0
    for table in tables:
        for record in table.records:
            payload = _record_to_payload(record)
            if payload is None:
                continue
            code = payload["code"].upper()
            house.update_actuator(code, payload)
            # Keep the RGB singleton consistent with the stored BRGB state
            if payload["measurement"] == "rgb_led" and code == "BRGB":
                mode = payload.get("value")
                if mode:
                    try:
                        house.set_rgb_mode(str(mode))
                    except ValueError:
                        pass
            count += 1
    print(f"[boot] Loaded {count} actuator state(s) from InfluxDB.")
