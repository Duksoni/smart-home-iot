import json

def load_settings(file_path="settings.json"):
    with open(file_path, "r") as f:
        return json.load(f)

def get_device_config(settings, device=None):
    device = device or settings.get("device", "PI1")
    mapping = settings.get("device_map", {})
    return mapping.get(device, {}), settings.get("hardware", {})