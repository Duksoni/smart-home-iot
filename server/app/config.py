from functools import lru_cache

from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    influxdb_url: str
    influxdb_org: str
    influxdb_bucket: str
    influxdb_admin_token: str

    mqtt_host: str
    mqtt_port: int

    class Config:
        env_file = ".env"


@lru_cache()
def get_settings():
    return Settings()
