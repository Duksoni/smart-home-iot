"""
Shared FastAPI dependencies.

AppDependencies is a singleton that holds the MQTT client and InfluxDB
query API so routers never need to import from main.py.
"""

from typing import TYPE_CHECKING, Optional


class AppDependencies:
    """Process-wide singleton for injectable infrastructure objects."""

    _instance: Optional["AppDependencies"] = None

    def __new__(cls) -> "AppDependencies":
        if cls._instance is None:
            instance = super().__new__(cls)
            instance._mqtt_client = None
            instance._query_api = None
            cls._instance = instance
        return cls._instance

    # ── Setters (called once from main.py at startup) ─────────────────────────

    def set_mqtt_client(self, client) -> None:
        self._mqtt_client = client

    def set_query_api(self, api) -> None:
        self._query_api = api

    # ── Getters (used as FastAPI Depends) ─────────────────────────────────────

    def get_mqtt_client(self):
        return self._mqtt_client

    def get_query_api(self):
        return self._query_api


# ── FastAPI-compatible dependency functions ───────────────────────────────────
# Routers use:  mqtt=Depends(get_mqtt_client)
# This avoids importing AppDependencies in every router file.

def get_mqtt_client():
    return AppDependencies().get_mqtt_client()


def get_query_api():
    return AppDependencies().get_query_api()
