import os
import requests


KALAVAI_BRIDGE_URL = os.getenv("KALAVAI_BRIDGE_URL", "http://0.0.0.0")
KALAVAI_BRIDGE_PORT = os.getenv("KALAVAI_BRIDGE_PORT", "8001")
ACCESS_KEY = os.getenv("ACCESS_KEY", None)


def request_to_kalavai_core(method, endpoint, base_url=None, **kwargs):
    if base_url is None:
        base_url = f"{KALAVAI_BRIDGE_URL}:{KALAVAI_BRIDGE_PORT}"
    headers = None
    if ACCESS_KEY is not None:
        headers = {
            "X-API-KEY": ACCESS_KEY
        }
    result = requests.request(
        method,
        url=f"{base_url}/{endpoint}",
        headers=headers,
        **kwargs
    )
    result.raise_for_status()
    return result.json()