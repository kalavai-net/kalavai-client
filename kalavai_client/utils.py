import json, base64
import os
import uuid
import requests
from pathlib import Path
import shutil
import subprocess
import re

from jinja2 import Template

from rich.table import Table
import yaml

from kalavai_client.auth import KalavaiAuth
from kalavai_client.env import (
    SERVER_IP_KEY,
    DOCKER_COMPOSE_TEMPLATE,
    DEFAULT_CONTAINER_NAME,
    DEFAULT_FLANNEL_IFACE,
    DEFAULT_VPN_CONTAINER_NAME,
    CONTAINER_HOST_PATH,
    USER_COMPOSE_FILE,
    USER_COOKIE,
    KALAVAI_USER_ID,
    user_path
)

GITHUB_ORG = "kalavai-net"
GITHUB_REPO = "kalavai-client"
GITHUB_TEMPLATE_PATH = "templates"
USER_NODE_LABEL_KEY = "user_node_label"
CLUSTER_IP_KEY = "cluster_ip"
CLUSTER_TOKEN_KEY = "cluster_token"
NODE_NAME_KEY = "node_name"
PUBLIC_LOCATION_KEY = "public_location"
CLUSTER_NAME_KEY = "cluster_name"
AUTH_KEY = "watcher_admin_key"
USER_ID_KEY = "kalavai_user_id"
WRITE_AUTH_KEY = "watcher_write_key"
ALLOW_UNREGISTERED_USER_KEY = "watcher_allow_unregistered_user"
NODE_ROLE_LABEL = "kalavai/role"
USER_API_KEY = "user_api_key"
READONLY_AUTH_KEY = "watcher_readonly_key"
WATCHER_SERVICE_KEY = "watcher_service"
WATCHER_PORT_KEY = "watcher_port"
WATCHER_IMAGE_TAG_KEY = "watcher_image_tag"
ENDPOINT_PORTS_KEY = "endpoint_ports"
TEMPLATE_ID_FIELD = "id_field"
TEMPLATE_ID_KEY = "deployment_id"
MANDATORY_TOKEN_FIELDS = [
    CLUSTER_IP_KEY,
    CLUSTER_TOKEN_KEY,
    CLUSTER_NAME_KEY,
    AUTH_KEY,
    WATCHER_SERVICE_KEY,
    PUBLIC_LOCATION_KEY
]
MANDATORY_POOLCONFIG_FIELDS = [
    SERVER_IP_KEY,
    AUTH_KEY,
    WATCHER_SERVICE_KEY,
    NODE_NAME_KEY,
    CLUSTER_NAME_KEY,
    PUBLIC_LOCATION_KEY
]

KALAVAI_AUTH = KalavaiAuth(
    auth_service_url="dummy_url",
    auth_service_key="dummy_key",
    user_cookie_file=USER_COOKIE
)


####### Methods to check OS compatibility ########
def check_gpu_drivers():
    value = run_cmd("nvidia-smi", hide_output=True)
    return len(value.decode("utf-8")) == 0

def get_max_gpus():
    try:
        has_gpus = check_gpu_drivers()
        if has_gpus:
            return len(
                [r for r in run_cmd("nvidia-smi -L").decode().split("\n") if len(r.strip())>0]
            )
        else:
            return 0
    except:
        return 0

def is_storage_compatible():
    """
    Raw method to determine if running node is compatible with PVC (longhorn)

    Exclude: WSL
    """
    try:
        import platform
        if "windows" in platform.system().lower():
            return True
        flagged = any([
            "microsoft" in run_cmd("cat /proc/version").decode().lower()
        ])
        return not flagged
    except:
        return False
################

def parse_key_value_pairs(input_str: str) -> dict:
    """Parse key=value pairs from a string into a dictionary.
    
    Args:
        input_str: String containing key=value pairs separated by commas
        
    Returns:
        Dictionary with parsed key-value pairs
        
    Raises:
        ValueError: If any pair is not in key=value format
    """
    if not input_str.strip():
        return {}
    
    result = {}
    for pair in input_str.split(','):
        pair = pair.strip()
        if not pair:
            continue
        if '=' not in pair:
            raise ValueError(f"Invalid key=value pair: '{pair}'. Expected format: key=value")
        key, value = pair.split('=', 1)
        result[key.strip()] = value.strip()
    return result

def extract_auth_token(headers):
    """
    Extract auth token. Valid headers:
        X-API-KEY: token
        X-API-Key: token
        Authorization: Bearer token
        authorization: Bearer token
    """
    #return headers.get("X-API-Key")
    bearer = None
    try:
        for header in ["Authorization", "authorization", "X-API-KEY", "X-API-Key"]:
            bearer = headers.get(header, None)
            if bearer is not None:
                break
        if bearer is not None and " " in bearer:
            return bearer.split()[-1]
        else:
            return bearer
    except Exception as e:
        return {"error": str(e)}


def generate_compose_config(
    role,
    node_name,
    mtu="",
    target_platform="amd64",
    write_to_file=True,
    node_ip_address="0.0.0.0",
    lb_ip_address=None,
    num_gpus=0,
    node_labels=None,
    pool_ip=None,
    vpn_token=None,
    pool_token=None,
    host_root_path=None,
):
    if node_labels is not None:
        node_labels = " ".join([f"--node-label {key}={value}" for key, value in node_labels.items()])
    rand_suffix = uuid.uuid4().hex[:8]
    compose_values = {
        "target_platform": target_platform,
        "user_path": user_path(""),
        "service_name": DEFAULT_CONTAINER_NAME,
        "vpn": vpn_token is not None,
        "vpn_name": DEFAULT_VPN_CONTAINER_NAME,
        "mtu": mtu,
        "node_ip_address": node_ip_address,
        "load_balancer_ip_address": lb_ip_address if lb_ip_address is not None else "",
        "pool_ip": pool_ip,
        "pool_token": pool_token,
        "vpn_token": vpn_token,
        "node_name": node_name,
        "command": role,
        "storage_enabled": "True",
        "num_gpus": num_gpus,
        "k3s_path": f"{CONTAINER_HOST_PATH}/{rand_suffix}/k3s",
        "etc_path": f"{CONTAINER_HOST_PATH}/{rand_suffix}/etc",
        "random_suffix": rand_suffix,
        "node_labels": node_labels,
        "flannel_iface": DEFAULT_FLANNEL_IFACE if vpn_token is not None else "",
        "user_id": load_user_id(),
        "host_root_path": host_root_path
    }
    # generate local config files
    compose_yaml = load_template(
        template_path=DOCKER_COMPOSE_TEMPLATE,
        values=compose_values)
    if write_to_file:
        with open(USER_COMPOSE_FILE, "w") as f:
            f.write(compose_yaml)
    return compose_yaml

def is_watcher_alive(server_creds, user_cookie, timeout=30):
    try:
        request_to_server(
            method="get",
            endpoint="/v1/health",
            data=None,
            server_creds=server_creds,
            user_cookie=user_cookie,
            timeout=timeout
        )
    except Exception as e:
        return False
    return True


def load_server_info(data_key, file):
    try:
        with open(file, "r") as f:
            return json.load(f)[data_key]
    except:
        return None

def load_user_session():
    if KALAVAI_USER_ID is None:
        user_id = KALAVAI_AUTH.load_user_session()
    else:
        user_id = KALAVAI_USER_ID
    return user_id

def load_user_id():
    if KALAVAI_USER_ID is None:
        user_id = KALAVAI_AUTH.get_user_id()
    else:
        user_id = KALAVAI_USER_ID
    return user_id

def get_public_seeds(user_only, user_cookie):
    return []
    # if not auth_obj.is_logged_in():
    #     raise ValueError("Cannot access vpns, user is not authenticated")
    # user = auth_obj.load_user_session() if user_only else None
    # seeds = auth_obj.call_function(
    #     "get_available_seeds",
    #     user
    # )
    # return seeds

def register_cluster(name, token, description, user_cookie, is_private=True):
    return None
    # if not auth_obj.is_logged_in():
    #     raise ValueError("Cannot register cluster, user is not authenticated")
    # user = auth_obj.load_user_session()
    # seed = auth_obj.call_function(
    #     "register_seed",
    #     name,
    #     user,
    #     description,
    #     token,
    #     is_private
    # )
    # return seed

def unregister_cluster(name, user_cookie):
    return None
    # if not auth_obj.is_logged_in():
    #     raise ValueError("Cannot unregister cluster, user is not authenticated")
    # user = auth_obj.load_user_session()
    # seed = auth_obj.call_function(
    #     "unregister_seed",
    #     name,
    #     user,
    # )
    # return seed

def send_pool_invite(cluster_name, invitee_addresses, user_cookie):
    return None
    # if not auth_obj.is_logged_in():
    #     raise ValueError("Cannot notify join cluster, user is not authenticated")
    # user = auth_obj.load_user_session()
    # result = auth_obj.call_function(
    #     "send_pool_invite",
    #     user,
    #     cluster_name,
    #     invitee_addresses
    # )
    # return result

def validate_poolconfig(poolconfig_file):
    if not Path(poolconfig_file).is_file():
        return False
    with open(poolconfig_file, "r") as f:
        data = json.load(f)
    for field in MANDATORY_POOLCONFIG_FIELDS:
        if field not in data:
            return False
    return True

def run_cmd(command, hide_output=False):
    try:
        import platform
        if "windows" in platform.system().lower():
            if hide_output:
                command = command + " > $nul 2>&1"
            return_value = subprocess.check_output(command, shell=True)
        else:
            if hide_output:
                command = command + " >/dev/null 2>&1"
            return_value = subprocess.check_output(command, shell=True, executable="/bin/bash")
        return return_value
    except OSError as error:
        return error # for exit code

def leave_vpn(container_name):
    try:
        vpns = json.loads(run_cmd(f"docker exec {container_name} netclient list").decode())
        left_vpns = [vpn['network'] for vpn in vpns]
        for vpn in left_vpns:
            run_cmd(f"docker exec {container_name} netclient leave {vpn}")
        return left_vpns
    except:
        return None

def request_to_server(
        method,
        endpoint,
        server_creds,
        data=None,
        params=None,
        force_url=None,
        force_key=None,
        user_cookie=None,
        timeout=60
):
    if force_url is None:
        service_url = load_server_info(data_key=WATCHER_SERVICE_KEY, file=server_creds)
    else:
        service_url = force_url
    
    if force_key is None:
        auth_key = load_server_info(data_key=AUTH_KEY, file=server_creds)
    else:
        auth_key = force_key

    headers = {
        "X-API-KEY": auth_key
    }

    headers["USER-KEY"] = load_server_info(data_key=USER_API_KEY, file=server_creds)
    user_id = load_user_id()
    if user_id is not None:
        headers["USER"] = user_id

    response = requests.request(
        method=method,
        url=f"http://{service_url}{endpoint}",
        json=data,
        params=params,
        headers=headers,
        timeout=timeout
    )
    try:
        result = response.json()
        return result
    except Exception as e:
        raise ValueError(f"Error with HTTP request: {response.text}\n{str(e)}")


def generate_table(columns, rows, end_sections=None):

    table = Table(show_header=True, header_style="bold white")
    [table.add_column(col, overflow="fold") for col in columns]
    for idx, row in enumerate(rows):
        table.add_row(*row, end_section=end_sections and idx in end_sections)

    return table

def store_server_info(server_ip, auth_key, watcher_service, file, node_name, cluster_name, readonly_auth_key=None, write_auth_key=None, public_location=None, user_api_key=None):
    with open(file, "w") as f:
        json.dump({
            SERVER_IP_KEY: server_ip,
            AUTH_KEY: auth_key,
            READONLY_AUTH_KEY: readonly_auth_key,
            WRITE_AUTH_KEY: write_auth_key,
            WATCHER_SERVICE_KEY: watcher_service,
            NODE_NAME_KEY: node_name,
            CLUSTER_NAME_KEY: cluster_name,
            PUBLIC_LOCATION_KEY: public_location,
            USER_API_KEY: user_api_key
        }, f)
    return True

def populate_template(template_str, values_dict):
    return Template(template_str).render(values_dict)

def escape_field(text):
    return re.sub('[^0-9a-z]+', '-', text.lower())

def load_template(template_path, values, default_values_path=None, force_defaults=False):

    if not Path(template_path).exists():
        raise FileNotFoundError(f"{template_path} does not exist")
    with open(template_path, 'r') as f:
        yaml_template = "".join(f.readlines())
    
    # substitute missing values with defaults
    if default_values_path is not None:
        with open(default_values_path, 'r') as f:
            default_values = yaml.safe_load(f)
        for default in default_values:
            if default["name"] == TEMPLATE_ID_FIELD:
                if default["default"] not in values:
                    raise ValueError(f"Key value '{default['default']}' missing from values")
                values[TEMPLATE_ID_KEY] = escape_field(values[default["default"]])
                continue
            if force_defaults or default["name"] not in values:
                values[default['name']] = default['default']
        
    return populate_template(template_str=yaml_template, values_dict=values)


def user_confirm(question: str, options: list, multiple: bool=False) -> int:
    try:
        print(question)
        [print(f"{idx}) {option}") for idx, option in enumerate(options)]
        reply = str(input())
        if multiple:
            if "," in reply:
                selection = reply.split(",")
                cast_selection = [int(s) for s in selection]
                if all([s >= 0 and s < len(options) for s in cast_selection]):
                    return cast_selection
            else:
                reply = int(reply)
                if reply >= 0 and reply <= len(options):
                    return [reply]
        else:
            reply = int(reply)
            if reply >= 0 and reply <= len(options):
                return reply

    except:
        return None
    return None

def generate_join_token(cluster_ip, cluster_token, cluster_name, auth_key, watcher_service, public_location):
    data = {
        CLUSTER_IP_KEY: cluster_ip,
        CLUSTER_NAME_KEY: cluster_name,
        CLUSTER_TOKEN_KEY: cluster_token,
        AUTH_KEY: auth_key,
        WATCHER_SERVICE_KEY: watcher_service,
        PUBLIC_LOCATION_KEY: public_location
    }
    return encode_dict(data=data)

def encode_dict(data: dict):
    base64_str = base64.b64encode(json.dumps(data).encode())
    return base64_str.decode()

def decode_dict(str_data: str):
    return json.loads(base64.b64decode(str_data.encode()))

def safe_remove(filepath, force=True):
    if not os.path.exists(filepath):
        return
    try:
        if os.path.isfile(filepath):
            os.remove(filepath)
        if os.path.isdir(filepath):
            shutil.rmtree(filepath)
        return
    except:
        pass

    if force:
        try:
            run_cmd(f"rm -rf {filepath}")
        except:
            pass
