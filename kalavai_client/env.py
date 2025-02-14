import os
from pathlib import Path
import importlib.resources


def user_path(relative_path, create_path=False):
    """Transform a relative path into the user's cache folder path"""
    base = os.path.expanduser("~")
    kalavai_user_path = os.path.join(base, ".cache/kalavai")
    full_path = os.path.join(kalavai_user_path, relative_path)
    if create_path:
        Path(full_path).mkdir(parents=True, exist_ok=True)
    
    return full_path

def resource_path(relative_path: str):
    """ Get absolute path to resource """
    try:
        last_slash = relative_path.rfind("/") 
        path = relative_path[:last_slash].replace("/", ".")
        filename = relative_path[last_slash+1:]
        resource = str(importlib.resources.files(path).joinpath(filename))
    except Exception as e:
        return None
    return resource


TEMPLATE_LABEL = "kalavai.job.name"
SERVER_IP_KEY = "server_ip"
KALAVAI_PLATFORM_URL = "https://platform.kalavai.net"
KALAVAI_PLATFORM_ENDPOINT = "https://platform.kalavai.net/_/api"
DEFAULT_CONTAINER_NAME = "kalavai"
DEFAULT_VPN_CONTAINER_NAME = "kalavai-vpn"
CONTAINER_HOST_PATH = user_path("pool/", create_path=True)
DEFAULT_FLANNEL_IFACE = os.getenv("KALAVAI_FLANNEL_IFACE", "netmaker-1")
DOCKER_COMPOSE_TEMPLATE = resource_path("kalavai_client/assets/docker-compose-template.yaml")
KUBE_VERSION = os.getenv("KALAVAI_KUBE_VERSION", "v1.31.1+k3s1")
# user specific config files
USER_TEMPLATES_FOLDER = user_path("templates", create_path=True)
USER_LOCAL_SERVER_FILE = user_path(".server")
USER_COOKIE = user_path(".user_cookie.pkl")
USER_COMPOSE_FILE = user_path("docker-compose-worker.yaml")
USER_HELM_APPS_FILE = user_path("apps.yaml")
USER_KUBECONFIG_FILE = user_path("kubeconfig")
USER_VPN_COMPOSE_FILE = user_path("docker-compose-vpn.yaml")
