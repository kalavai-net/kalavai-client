import os
from pathlib import Path
import importlib.resources


DEFAULT_KALAVAI_PATH = os.getenv("KALAVAI_PATH", "")
KALAVAI_USER_ID = os.getenv("KALAVAI_USER_ID", None)

def user_path(relative_path, create_path=False):
    """Transform a relative path into the user's cache folder path"""
    if len(DEFAULT_KALAVAI_PATH.strip()) > 0:
        kalavai_user_path = DEFAULT_KALAVAI_PATH
    else:
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
KALAVAI_SERVICE_LABEL = "app"
KALAVAI_SERVICE_LABEL_VALUE = "kube-watcher-api"
STORAGE_CLASS_LABEL = "kalavai.storage.enabled"
USER_NODE_LABEL = "kalavai.cluster.user"
SERVER_IP_KEY = "server_ip"
KALAVAI_PLATFORM_URL = "https://platform.kalavai.net"
KALAVAI_PLATFORM_ENDPOINT = "https://platform.kalavai.net/_/api"
DEFAULT_CONTAINER_NAME = "kalavai"
DEFAULT_VPN_CONTAINER_NAME = "kalavai-vpn"
CONTAINER_HOST_PATH = user_path("pool/", create_path=True)
DEFAULT_FLANNEL_IFACE = os.getenv("KALAVAI_FLANNEL_IFACE", "netmaker")
DEFAULT_WATCHER_PORT = 30001
KUBE_VERSION = os.getenv("KALAVAI_KUBE_VERSION", "v1.31.1+k3s1")
FORBIDEDEN_IPS = ["127.0.0.1"]
# kalavai templates
HELM_APPS_FILE = resource_path("kalavai_client/assets/apps.yaml")
HELM_APPS_VALUES = resource_path("kalavai_client/assets/apps_values.yaml")
DOCKER_COMPOSE_TEMPLATE = resource_path("kalavai_client/assets/docker-compose-template.yaml")
DOCKER_COMPOSE_GUI = resource_path("kalavai_client/assets/docker-compose-gui.yaml")
DEFAULT_POOL_CONFIG_TEMPLATE = resource_path("kalavai_client/assets/default_pool_config.yaml")
USER_WORKSPACE_TEMPLATE = resource_path("kalavai_client/assets/user_workspace.yaml")
DEFAULT_USER_WORKSPACE_VALUES = resource_path("kalavai_client/assets/user_workspace_values.yaml")
POOL_CONFIG_TEMPLATE = resource_path("kalavai_client/assets/pool_config_template.yaml")
POOL_CONFIG_DEFAULT_VALUES = resource_path("kalavai_client/assets/pool_config_values.yaml")
MODEL_DEPLOYMENT_VALUES_MAPPING = resource_path("kalavai_client/assets/model_deployment_values.yaml")
# user specific config files
USER_TEMPLATES_FOLDER = user_path("templates", create_path=True)
USER_LOCAL_SERVER_FILE = user_path(".server")
USER_COOKIE = user_path(".user_cookie.json")
USER_COMPOSE_FILE = user_path("docker-compose-worker.yaml")
USER_GUI_COMPOSE_FILE = user_path("docker-compose-gui.yaml")
USER_HELM_APPS_FILE = user_path("apps.yaml")
USER_KUBECONFIG_FILE = user_path("kubeconfig")
USER_VPN_COMPOSE_FILE = user_path("docker-compose-vpn.yaml")
