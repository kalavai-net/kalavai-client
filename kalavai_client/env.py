import os
from pathlib import Path


def user_path(relative_path, create_path=False):
    """Transform a relative path into the user's cache folder path"""
    base = os.path.expanduser("~")
    kalavai_user_path = os.path.join(base, ".cache/kalavai")
    full_path = os.path.join(kalavai_user_path, relative_path)
    if create_path:
        Path(full_path).mkdir(parents=True, exist_ok=True)
    
    return full_path


USER_LOCAL_SERVER_FILE = user_path(".server")
USER_COOKIE = user_path(".user_cookie.pkl")
TEMPLATE_LABEL = "kalavai.job.name"
SERVER_IP_KEY = "server_ip"
KALAVAI_PLATFORM_URL = "https://platform.kalavai.net"
KALAVAI_PLATFORM_ENDPOINT = "https://platform.kalavai.net/_/api"