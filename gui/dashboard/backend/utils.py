import os
import requests
from urllib.parse import urljoin


KALAVAI_CORE_URL = os.getenv("KALAVAI_CORE_URL", "http://localhost:8001")

def request_to_kalavai_core(method, endpoint, base_url=KALAVAI_CORE_URL, params=None, json=None):
    result = requests.request(
        method,
        url=f"{base_url}/{endpoint}",
        params=params,
        json=json
    )
    return result.json()