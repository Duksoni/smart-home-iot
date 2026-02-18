"""
RGB bulb (BRGB) control endpoints.

The BRGB hardware supports a fixed set of named modes only – no free RGB values.

  GET  /rgb           – current mode, its CSS colour, and the list of all modes
  POST /rgb/mode      – activate a named mode
"""

import json

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel

from app.config import get_settings
from app.dependencies import get_mqtt_client
from app.state import HouseState, RGB_MODES

router = APIRouter(prefix="/rgb", tags=["RGB Bulb"])


# ── Schemas ───────────────────────────────────────────────────────────────────

class SetModeRequest(BaseModel):
    mode: str


# ── Routes ────────────────────────────────────────────────────────────────────

@router.get("")
async def get_rgb():
    """Return current mode, its CSS colour preview, and all available modes."""
    return HouseState().get_rgb()


@router.post("/mode")
async def set_mode(
    body: SetModeRequest,
    mqtt=Depends(get_mqtt_client),
    settings=Depends(get_settings),
):
    """
    Switch the BRGB bulb to one of the predefined modes.
    The mode string is published directly as the MQTT action so the PI3
    device receives exactly what its rgb_light_coordinator expects.
    """
    if body.mode not in RGB_MODES:
        raise HTTPException(
            status_code=422,
            detail=f"Unknown mode '{body.mode}'. Valid modes: {RGB_MODES}",
        )
    HouseState().set_rgb_mode(body.mode)
    topic = f"{settings.mqtt_topic_prefix}/commands/BRGB"
    mqtt.publish(topic, json.dumps({"action": body.mode}))
    return HouseState().get_rgb()
