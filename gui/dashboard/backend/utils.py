import os
import requests


KALAVAI_BRIDGE_URL = os.getenv("KALAVAI_BRIDGE_URL", "http://0.0.0.0")
KALAVAI_BRIDGE_PORT = os.getenv("KALAVAI_BRIDGE_PORT", "8001")


def request_to_kalavai_core(method, endpoint, base_url=None, params=None, json=None):
    if base_url is None:
        base_url = f"{KALAVAI_BRIDGE_URL}:{KALAVAI_BRIDGE_PORT}"
    result = requests.request(
        method,
        url=f"{base_url}/{endpoint}",
        params=params,
        json=json
    )
    return result.json()