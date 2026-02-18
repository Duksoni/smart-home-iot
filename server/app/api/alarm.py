"""
Alarm-related endpoints.

  GET  /alarm              – current alarm + armed state
  POST /alarm/trigger      – manually trigger the alarm
  POST /alarm/deactivate   – disarm alarm via PIN
  POST /alarm/arm          – arm the security system (10-s grace on device side)
  POST /alarm/disarm       – admin override, no PIN required
  GET  /alarm/events       – alarm events from InfluxDB
"""

import json
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel

from app.config import get_settings
from app.dependencies import get_mqtt_client, get_query_api
from app.state import HouseState

router = APIRouter(prefix="/alarm", tags=["Alarm"])


# ── Schemas ───────────────────────────────────────────────────────────────────

class TriggerAlarmRequest(BaseModel):
    reason: str = "manual"


class DeactivateAlarmRequest(BaseModel):
    pin: str


class ArmRequest(BaseModel):
    pin: str


# ── Routes ────────────────────────────────────────────────────────────────────

@router.get("")
async def get_alarm():
    """Return current alarm + armed status + occupancy."""
    return HouseState().get_alarm() | {"people_inside": HouseState().get_people_count()}


@router.post("/trigger")
async def trigger_alarm(
    body: TriggerAlarmRequest,
    mqtt=Depends(get_mqtt_client),
    settings=Depends(get_settings),
):
    """Manually activate the alarm from the web application."""
    HouseState().set_alarm(active=True, reason=body.reason)
    _publish_alarm(mqtt, settings, "activate", reason=body.reason)
    return {"ok": True, "alarm": HouseState().get_alarm()}


@router.post("/deactivate")
async def deactivate_alarm(
    body: DeactivateAlarmRequest,
    mqtt=Depends(get_mqtt_client),
    settings=Depends(get_settings),
):
    """Deactivate alarm + disarm system by supplying the correct PIN."""
    if body.pin != settings.alarm_pin:
        raise HTTPException(status_code=403, detail="Incorrect PIN")
    HouseState().set_alarm(active=False)
    HouseState().set_armed(False)
    _publish_alarm(mqtt, settings, "deactivate")
    return {"ok": True, "alarm": HouseState().get_alarm()}


@router.post("/arm")
async def arm_system(
    body: ArmRequest,
    mqtt=Depends(get_mqtt_client),
    settings=Depends(get_settings),
):
    """Arm the security system from the web application."""
    HouseState().set_armed(True)
    _publish_alarm(mqtt, settings, "arm", pin=body.pin)
    return {"ok": True, "alarm": HouseState().get_alarm()}


@router.post("/disarm")
async def disarm_system(
    mqtt=Depends(get_mqtt_client),
    settings=Depends(get_settings),
):
    """Disarm the system without PIN (admin/web override)."""
    HouseState().set_alarm(active=False)
    HouseState().set_armed(False)
    _publish_alarm(mqtt, settings, "disarm")
    return {"ok": True, "alarm": HouseState().get_alarm()}


@router.get("/events")
async def get_alarm_events(
    limit: int = Query(50, ge=1, le=500),
    query_api=Depends(get_query_api),
    settings=Depends(get_settings),
):
    """Return the last N alarm events from InfluxDB."""
    flux = f"""
from(bucket: "{settings.influxdb_bucket}")
  |> range(start: -30d)
  |> filter(fn: (r) => r._measurement == "alarm_event")
  |> sort(columns: ["_time"], desc: true)
  |> limit(n: {limit})
"""
    tables = query_api.query(flux, org=settings.influxdb_org)
    events = [
        {
            "time": record.get_time().isoformat(),
            "action": record.values.get("action"),
            "reason": record.values.get("reason"),
            "value": record.get_value(),
        }
        for table in tables
        for record in table.records
    ]
    return {"events": events}


# ── Helper ────────────────────────────────────────────────────────────────────

def _publish_alarm(mqtt_client, settings, action: str, **extra) -> None:
    topic = f"{settings.mqtt_topic_prefix}/commands/alarm"
    mqtt_client.publish(topic, json.dumps({"action": action, **extra}))
