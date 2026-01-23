import json

import paho.mqtt.client as mqtt
from fastapi import FastAPI
from influxdb_client import InfluxDBClient

from .config import get_settings

settings = get_settings()

# InfluxDB configuration
influxdb_client = InfluxDBClient(
    url=settings.influxdb_url,
    token=settings.influxdb_admin_token,
    org=settings.influxdb_org,
)

# MQTT Configuration
mqtt_client = mqtt.Client()
mqtt_client.connect(settings.mqtt_host, settings.mqtt_port)
mqtt_client.loop_start()


def on_connect(client, userdata, flags, rc):
    print("Connected to MQTT broker")


mqtt_client.on_connect = on_connect
mqtt_client.on_message = lambda client, userdata, msg: save_to_db(
    json.loads(msg.payload.decode("utf-8"))
)


def save_to_db(data):
    print(f"Saving to db:\n{data}")


app = FastAPI(title="Smart Home IoT Server")


@app.get("/health", tags=["Health"])
async def health_check():
    return {"message": "Server is running. Great!"}
