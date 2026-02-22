"""
Kitchen timer endpoints.

  GET  /timer             – current timer state
  POST /timer/set         – set duration and start
  POST /timer/add         – add N seconds (mirrors BTN on PI2)
  POST /timer/stop        – stop blinking after expiry (mirrors BTN on PI2)
  PUT  /timer/increment   – change the N-seconds-per-button-press setting
"""

import json

from fastapi import APIRouter, Depends
from pydantic import BaseModel, Field

from app.config import get_settings
from app.dependencies import get_mqtt_client
from app.state import HouseState

router = APIRouter(prefix="/timer", tags=["Kitchen Timer"])


# ── Schemas ───────────────────────────────────────────────────────────────────

class SetTimerRequest(BaseModel):
    duration_seconds: int = Field(..., ge=1)
    add_seconds_increment: int | None = Field(None, ge=1)


class IncrementRequest(BaseModel):
    add_seconds_increment: int = Field(..., ge=1)


# ── Routes ────────────────────────────────────────────────────────────────────

@router.get("")
async def get_timer():
    if HouseState().get_timer()['remaining_seconds'] <= 0 and HouseState().get_timer()['running']:
        HouseState().set_timer_blink(True)
    return HouseState().get_timer()


@router.post("/set")
async def set_timer(
    body: SetTimerRequest,
    mqtt=Depends(get_mqtt_client),
    settings=Depends(get_settings),
):
    HouseState().set_timer(body.duration_seconds, body.add_seconds_increment)
    _publish(mqtt, settings, {"action": "set", "duration": body.duration_seconds})
    return HouseState().get_timer()


@router.post("/add")
async def add_time(
    mqtt=Depends(get_mqtt_client),
    settings=Depends(get_settings),
):
    current = HouseState().get_timer()
    n = current["add_seconds_increment"]
    HouseState().set_timer(current["remaining_seconds"] + n)
    _publish(mqtt, settings, {"action": "add", "seconds": n})
    return HouseState().get_timer()


@router.post("/stop")
async def stop_blink(
    mqtt=Depends(get_mqtt_client),
    settings=Depends(get_settings),
):
    HouseState().stop_timer_blink()
    _publish(mqtt, settings, {"action": "stop_blink"})
    return HouseState().get_timer()


@router.put("/increment")
async def set_increment(
    body: IncrementRequest,
    mqtt=Depends(get_mqtt_client),
    settings=Depends(get_settings),
):
    HouseState().set_add_seconds_increment(body.add_seconds_increment)
    _publish(mqtt, settings, {"action": "set_increment", "seconds": body.add_seconds_increment})
    return HouseState().get_timer()


# ── Helper ────────────────────────────────────────────────────────────────────

def _publish(mqtt_client, settings, payload: dict) -> None:
    topic = f"{settings.mqtt_topic_prefix}/commands/4SD"
    mqtt_client.publish(topic, json.dumps(payload))
