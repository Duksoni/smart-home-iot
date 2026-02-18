"""
Sensor & occupancy endpoints.

  GET  /sensors                  – latest reading for every known sensor
  GET  /sensors/occupancy        – current people-inside count
  POST /sensors/occupancy        – manual override (admin/debug)
  GET  /sensors/{code}           – latest reading for a specific sensor
  GET  /sensors/{code}/history   – historical readings from InfluxDB
"""

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel

from app.config import get_settings
from app.dependencies import get_query_api
from app.state import HouseState

router = APIRouter(prefix="/sensors", tags=["Sensors"])


# ── Schemas ───────────────────────────────────────────────────────────────────

class OccupancyOverride(BaseModel):
    count: int


# ── Routes ────────────────────────────────────────────────────────────────────

@router.get("")
async def list_sensors():
    return {"sensors": HouseState().get_all_sensors()}


@router.get("/occupancy")
async def get_occupancy():
    return {"people_inside": HouseState().get_people_count()}


@router.post("/occupancy")
async def set_occupancy(body: OccupancyOverride):
    HouseState().set_people_count(body.count)
    return {"people_inside": HouseState().get_people_count()}


@router.get("/{code}")
async def get_sensor(code: str):
    reading = HouseState().get_sensor(code.upper())
    if reading is None:
        raise HTTPException(status_code=404, detail=f"No data for sensor '{code}'")
    return reading


@router.get("/{code}/history")
async def get_sensor_history(
    code: str,
    start: str = Query("-1h", description="Flux duration or RFC3339 timestamp"),
    limit: int = Query(200, ge=1, le=2000),
    query_api=Depends(get_query_api),
    settings=Depends(get_settings),
):
    flux = f"""
from(bucket: "{settings.influxdb_bucket}")
  |> range(start: {start})
  |> filter(fn: (r) => r.code == "{code.upper()}")
  |> sort(columns: ["_time"], desc: true)
  |> limit(n: {limit})
"""
    tables = query_api.query(flux, org=settings.influxdb_org)
    rows = [
        {
            "time": record.get_time().isoformat(),
            "measurement": record.get_measurement(),
            "value": record.get_value(),
            "simulated": record.values.get("simulated"),
            "runs_on": record.values.get("runs_on"),
        }
        for table in tables
        for record in table.records
    ]
    return {"code": code.upper(), "history": rows}
