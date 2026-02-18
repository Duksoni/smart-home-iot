from fastapi import APIRouter

from . import actuators, alarm, rgb, sensors, timer

__all__ = ["api_router"]

api_router = APIRouter()
api_router.include_router(alarm.router)
api_router.include_router(sensors.router)
api_router.include_router(actuators.router)
api_router.include_router(timer.router)
api_router.include_router(rgb.router)
