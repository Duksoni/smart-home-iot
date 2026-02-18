"""
Actuator control endpoints.

  GET  /actuators                  – last known state of every actuator
  GET  /actuators/{code}           – last known state of a single actuator
  POST /actuators/{code}/command   – publish a command to an actuator via MQTT
"""

import json

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel

from app.dependencies import get_mqtt_client
from app.config import get_settings
from app.state import HouseState

router = APIRouter(prefix="/actuators", tags=["Actuators"])


# ── Schemas ───────────────────────────────────────────────────────────────────

class ActuatorCommand(BaseModel):
    action: str
    payload: dict = {}


# ── Routes ────────────────────────────────────────────────────────────────────

@router.get("")
async def list_actuators():
    return {"actuators": HouseState().get_all_actuators()}


@router.get("/{code}")
async def get_actuator(code: str):
    actuator = HouseState().get_actuator(code.upper())
    if actuator is None:
        raise HTTPException(status_code=404, detail=f"No data for actuator '{code}'")
    return actuator


@router.post("/{code}/command")
async def send_actuator_command(
    code: str,
    body: ActuatorCommand,
    mqtt=Depends(get_mqtt_client),
    settings=Depends(get_settings),
):
    """Publish an arbitrary command to smarthome/commands/{CODE}."""
    topic = f"{settings.mqtt_topic_prefix}/commands/{code.upper()}"
    message = json.dumps({"action": body.action, **body.payload})
    mqtt.publish(topic, message)
    return {"ok": True, "topic": topic, "message": message}
