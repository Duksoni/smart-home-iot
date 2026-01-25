import json

import paho.mqtt.client as mqtt
from fastapi import FastAPI
from influxdb_client import InfluxDBClient, Point
from influxdb_client.client.write_api import SYNCHRONOUS

from .config import get_settings

settings = get_settings()

# InfluxDB configuration
influxdb_client = InfluxDBClient(
    url=settings.influxdb_url,
    token=settings.influxdb_admin_token,
    org=settings.influxdb_org,
)
write_api = influxdb_client.write_api(write_options=SYNCHRONOUS)

# MQTT Configuration
mqtt_client = mqtt.Client()


def on_connect(client, userdata, flags, rc):
    if rc == 0:
        topic = f"{settings.mqtt_topic_prefix.rstrip('/')}/#"
        client.subscribe(topic)
        print(f"Connected to MQTT broker, subscribed to {topic}")
    else:
        print(f"Failed to connect to MQTT broker (rc={rc})")


def on_message(client, userdata, msg):
    try:
        data = json.loads(msg.payload.decode("utf-8"))
    except json.JSONDecodeError as exc:
        print(f"Invalid MQTT payload: {exc}")
        return
    save_to_db(data)

mqtt_client.on_connect = on_connect
mqtt_client.on_message = on_message

mqtt_client.connect(settings.mqtt_host, settings.mqtt_port)
mqtt_client.loop_start()

def save_to_db(data):
    if not isinstance(data, dict):
        return

    measurement = data.get("measurement")
    if not measurement:
        return

    point = Point(measurement)
    if "simulated" in data:
        point.tag("simulated", str(data["simulated"]).lower())
    if "runs_on" in data:
        point.tag("runs_on", str(data["runs_on"]))
    if "name" in data:
        point.tag("name", str(data["name"]))
    if "device" in data:
        point.tag("device", str(data["device"]))
    if "code" in data:
        point.tag("code", str(data["code"]))
    if "action" in data:
        point.tag("action", str(data["action"]))
    if "key" in data:
        point.tag("key", str(data["key"]))
    if "state" in data:
        point.tag("state", str(data["state"]))

    if "value" not in data:
        return
    point.field("value", data["value"])

    write_api.write(
        bucket=settings.influxdb_bucket,
        org=settings.influxdb_org,
        record=point,
    )


app = FastAPI(title="Smart Home IoT Server")


@app.get("/health", tags=["Health"])
async def health_check():
    return {"message": "Server is running. Great!"}
