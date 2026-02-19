import json

import paho.mqtt.client as mqtt
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from influxdb_client import InfluxDBClient, Point
from influxdb_client.client.write_api import SYNCHRONOUS

from .alarm_logic import AlarmLogic
from .api import api_router
from .boot import hydrate_state_from_influx
from .config import get_settings
from .dependencies import AppDependencies
from .state import _ACTUATOR_MEASUREMENTS, _SENSOR_MEASUREMENTS, HouseState

settings = get_settings()

# ── InfluxDB ──────────────────────────────────────────────────────────────────

_influx = InfluxDBClient(
    url=settings.influxdb_url,
    token=settings.influxdb_admin_token,
    org=settings.influxdb_org,
)
_write_api = _influx.write_api(write_options=SYNCHRONOUS)
_query_api = _influx.query_api()

AppDependencies().set_query_api(_query_api)
AppDependencies().set_write_api(_write_api)

# ── Boot: seed state from InfluxDB before accepting requests ──────────────────

hydrate_state_from_influx(_query_api, settings)

# ── MQTT ──────────────────────────────────────────────────────────────────────

_mqtt_client = mqtt.Client()


def _on_connect(client, userdata, flags, rc):
    if rc == 0:
        topic = f"{settings.mqtt_topic_prefix.rstrip('/')}/#"
        client.subscribe(topic)
        print(f"[MQTT] Connected, subscribed to {topic}")
    else:
        print(f"[MQTT] Connection failed (rc={rc})")


def _on_message(client, userdata, msg):
    try:
        data = json.loads(msg.payload.decode("utf-8"))
    except json.JSONDecodeError as exc:
        print(f"[MQTT] Invalid payload: {exc}")
        return
    _save_to_db(data)
    _update_state(data)


_mqtt_client.on_connect = _on_connect
_mqtt_client.on_message = _on_message
_mqtt_client.connect(settings.mqtt_host, settings.mqtt_port)
_mqtt_client.loop_start()

AppDependencies().set_mqtt_client(_mqtt_client)


# ── InfluxDB writer ───────────────────────────────────────────────────────────


def _save_to_db(data: dict) -> None:
    if not isinstance(data, dict):
        return
    measurement = data.get("measurement")
    if not measurement:
        return

    point = Point(measurement)
    for tag in (
        "simulated",
        "runs_on",
        "name",
        "device",
        "code",
        "action",
        "key",
        "state",
    ):
        if tag in data:
            point.tag(tag, str(data[tag]))

    if "value" not in data:
        return
    point.field("value", data["value"])

    _write_api.write(
        bucket=settings.influxdb_bucket, org=settings.influxdb_org, record=point
    )


# ── Runtime state dispatcher ──────────────────────────────────────────────────


def _update_state(data: dict) -> None:
    """Dispatch an incoming MQTT payload to the appropriate state handler."""
    measurement = data.get("measurement", "")
    code = data.get("code", "").upper()

    if not code:
        return

    house = HouseState()
    logic = AlarmLogic()

    if measurement in _SENSOR_MEASUREMENTS:
        house.update_sensor(code, data)
        value = data.get("value")

        # Route to alarm logic
        if measurement == "motion":
            logic.on_motion(code, int(value) if value is not None else 0)

        elif measurement == "ultrasonic":
            logic.on_distance(code, value)

        elif measurement == "button":
            logic.on_door(code, int(value) if value is not None else 0)

        elif measurement == "membrane_attempt":
            logic.on_membrane_attempt(code, bool(int(value)) if value is not None else False)

        elif measurement == "gyroscope":
            logic.on_gyroscope(code, value)

    elif measurement in _ACTUATOR_MEASUREMENTS:
        house.update_actuator(code, data)
        # Keep RGB singleton in sync when the device reports a mode change
        # (e.g. triggered by IR remote rather than the web app).
        if measurement == "rgb_led" and code == "BRGB":
            mode = data.get("value")
            if mode:
                try:
                    house.set_rgb_mode(mode)
                except ValueError:
                    pass

    elif measurement == "alarm_event":
        # These come from device-side alarm coordinators; server is now the
        # authority but we still honour explicit events for manual triggers
        # sent from the web-app via the alarm router.
        action = data.get("action")
        if action == "activated":
            house.set_alarm(active=True, reason=data.get("reason"))
        elif action == "deactivated":
            house.set_alarm(active=False)
            house.set_armed(False)

    elif measurement == "timer_event":
        action = data.get("action")
        if action == "expired":
            house.set_timer_blink(True)
        elif action == "blink_stopped":
            house.stop_timer_blink()

    elif measurement == "rgb_mode":
        mode = data.get("action")
        if mode:
            try:
                house.set_rgb_mode(mode)
            except ValueError:
                pass


# ── FastAPI app ───────────────────────────────────────────────────────────────

app = FastAPI(title="Smart Home IoT Server")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:4200"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(api_router)


@app.get("/health", tags=["Health"])
async def health_check():
    return {"status": "ok"}
