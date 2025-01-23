import json, base64
import sys
import os
import requests
from pathlib import Path
from urllib.parse import urljoin
import shutil
import urllib.request
import subprocess
import re

from jinja2 import Template, meta, Environment

from rich.table import Table
import yaml
import platform
import psutil

import GPUtil

from kalavai_client.auth import KalavaiAuthClient


GITHUB_ORG = "kalavai-net"
GITHUB_REPO = "kalavai-client"
GITHUB_TEMPLATE_PATH = "templates"
USER_NODE_LABEL_KEY = "user_node_label"
CLUSTER_IP_KEY = "cluster_ip"
CLUSTER_TOKEN_KEY = "cluster_token"
SERVER_IP_KEY = "server_ip"
NODE_NAME_KEY = "node_name"
PUBLIC_LOCATION_KEY = "public_location"
CLUSTER_NAME_KEY = "cluster_name"
AUTH_KEY = "watcher_admin_key"
WRITE_AUTH_KEY = "watcher_write_key"
ALLOW_UNREGISTERED_USER_KEY = "watcher_allow_unregistered_user"
USER_API_KEY = "user_api_key"
READONLY_AUTH_KEY = "watcher_readonly_key"
WATCHER_SERVICE_KEY = "watcher_service"
WATCHER_PORT_KEY = "watcher_port"
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


####### Methods to check OS compatibility ########
def check_gpu_drivers():
    value = run_cmd("command -v nvidia-smi")
    if len(value.decode("utf-8")) == 0:
        # no nvidia installed, no need to check nvidia any further
        return False
    else:
        # check drivers are set correctly
        try:
            value = run_cmd("nvidia-smi")
            return True
        except:
            raise ("Nvidia not configured properly. Please check your drivers are installed and configured")

def is_storage_compatible():
    """
    Raw method to determine if running node is compatible with PVC (longhorn)

    Exclude: WSL
    """
    try:
        flagged = any([
            "microsoft" in run_cmd("cat /proc/version").decode().lower()
        ])
        return not flagged
    except:
        return False
################

def is_watcher_alive(server_creds, user_cookie):
    try:
        request_to_server(
            method="get",
            endpoint="/v1/health",
            data=None,
            server_creds=server_creds,
            user_cookie=user_cookie
        )
    except Exception as e:
        print(str(e))
        return False
    return True



def load_server_info(data_key, file):
    try:
        with open(file, "r") as f:
            return json.load(f)[data_key]
    except:
        return None
    
def user_login(user_cookie, username=None, password=None):
    auth = KalavaiAuthClient(
        user_cookie_file=user_cookie
    )
    user = auth.load_user_session()
    if user is None:
        user = auth.login(username=username, password=password)
    return user

def user_logout(user_cookie):
    auth = KalavaiAuthClient(
        user_cookie_file=user_cookie
    )
    auth.logout()

def load_user_session(user_cookie):
    auth = KalavaiAuthClient(
        user_cookie_file=user_cookie
    )
    if not auth.is_logged_in():
        return None
    return auth.load_user_session()

def get_public_vpns(user_cookie):
    auth = KalavaiAuthClient(
        user_cookie_file=user_cookie
    )
    if not auth.is_logged_in():
        raise ValueError("Cannot access vpns, user is not authenticated")
    seeds = auth.call_function(
        "get_public_vpns"
    )
    return seeds

def get_public_seeds(user_only, user_cookie):
    auth = KalavaiAuthClient(
        user_cookie_file=user_cookie
    )
    if not auth.is_logged_in():
        raise ValueError("Cannot access vpns, user is not authenticated")
    user = auth.load_user_session() if user_only else None
    seeds = auth.call_function(
        "get_available_seeds",
        user
    )
    return seeds

def get_vpn_details(location, user_cookie):
    auth = KalavaiAuthClient(
        user_cookie_file=user_cookie
    )
    if not auth.is_logged_in():
        raise ValueError("Cannot access vpns, user is not authenticated")
    vpn = auth.call_function(
        "get_vpn_details",
        location
    )
    return vpn

def register_cluster(name, token, description, user_cookie):
    auth = KalavaiAuthClient(
        user_cookie_file=user_cookie
    )
    if not auth.is_logged_in():
        raise ValueError("Cannot register cluster, user is not authenticated")
    user = auth.load_user_session()
    seed = auth.call_function(
        "register_seed",
        name,
        user,
        description,
        token
    )
    return seed

def unregister_cluster(name, user_cookie):
    auth = KalavaiAuthClient(
        user_cookie_file=user_cookie
    )
    if not auth.is_logged_in():
        raise ValueError("Cannot unregister cluster, user is not authenticated")
    user = auth.load_user_session()
    seed = auth.call_function(
        "unregister_seed",
        name,
        user,
    )
    return seed

def validate_join_public_seed(cluster_name, join_key, user_cookie):
    auth = KalavaiAuthClient(
        user_cookie_file=user_cookie
    )
    if not auth.is_logged_in():
        raise ValueError("Cannot notify join cluster, user is not authenticated")
    user = auth.load_user_session()
    seed = auth.call_function(
        "validate_join_public_seed",
        cluster_name,
        join_key,
        user,
    )
    return seed

def validate_poolconfig(poolconfig_file):
    if not Path(poolconfig_file).is_file():
        return False
    with open(poolconfig_file, "r") as f:
        data = json.load(f)
    for field in MANDATORY_POOLCONFIG_FIELDS:
        if field not in data:
            return False
    return True

def run_cmd(command):
    try:
        return_value = subprocess.check_output(command, shell=True, executable="/bin/bash")
        return return_value
    except OSError as error:
        return error # for exit code

def join_vpn(location, user_cookie):
    vpn = get_vpn_details(location=location, user_cookie=user_cookie)
    token = vpn["key"]
    if token is None:
        raise ValueError(f"VPN location {location} not found or is private")
    try:
        data = decode_dict(token)
        for field in ["server", "value"]:
            assert field in data
    except:
        raise ValueError("Invalid net token")
    
    run_cmd(f"sudo netclient join -t {token} >/dev/null 2>&1")
    return vpn

def leave_vpn():
    try:
        vpns = json.loads(run_cmd("sudo netclient list").decode())
        left_vpns = [vpn['network'] for vpn in vpns]
        for vpn in left_vpns:
            run_cmd(f"sudo netclient leave {vpn}")
        return left_vpns
    except:
        return None

def is_service_running(service):
    return 0 == os.system(f'sudo systemctl is-active --quiet {service}')


def fetch_git_files(remote_folder):
    response = requests.get(
        f"https://api.github.com/repos/{GITHUB_ORG}/{GITHUB_REPO}/contents/{remote_folder}",
        headers={
            "X-GitHub-Api-Version": "2022-11-28",
            "Accept": "application/vnd.github+json"
        }
    )
    return response.json()


def fetch_templates(local_path):
    # get all templates
    templates = [] 
    data = fetch_git_files(remote_folder=GITHUB_TEMPLATE_PATH)
    
    for file in data:
        if file['type'] == 'dir':
            templates.append((file['name'], file["path"]))

    # fetch files for each template
    for template_name, template_path in templates:
        user_path(template_path, create_path=True)
        files = fetch_git_files(remote_folder=template_path)
        for file in files:
            if file["type"] == "file":
                urllib.request.urlretrieve(
                    file["download_url"],
                    os.path.join(local_path, template_name, file["name"]))


def get_all_templates(local_path, templates_path=None, remote_load=False):

    if templates_path is not None:
        # use provided local path
        local_path = templates_path
    elif remote_load:
        # load remote templates
        if os.path.isdir(local_path):
            shutil.rmtree(local_path)
        fetch_templates(local_path=local_path)
    
    # list available templates
    return [ (local_path, item) for item in os.listdir(local_path) if os.path.isdir(os.path.join(local_path, item)) ]


def request_to_server(
        method,
        endpoint,
        data,
        server_creds,
        force_url=None,
        force_key=None,
        user_cookie=None
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

    user = load_user_session(user_cookie=user_cookie)
    headers["USER-KEY"] = load_server_info(data_key=USER_API_KEY, file=server_creds)
    headers["USER"] = user["username"] if user is not None else None

    response = requests.request(
        method=method,
        url=f"http://{service_url}{endpoint}",
        json=data,
        headers=headers
    )
    result = response.json()
    return result


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
        [print(f"{idx}) {option}") for idx, option in enumerate(options)]
        reply = str(input(f"--> {question}: "))
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

def get_gpus():
    GPUs = GPUtil.getGPUs()
    gpus = []
    for gpu in GPUs:
        name = "nvidia" if "nvidia" in gpu.name.lower() else None
        if name is None:
            continue
        mem = int(gpu.memoryTotal / 1000) # in GBs
        gpus.append(f"{name}-{mem}GB")
    return ",".join(gpus)

def system_uptick_request(username, node_name, backend_endpoint, backend_api_key, local_version=0):
    gpus = get_gpus()
    data = {
        "username": username,
        "system_info": {
            "os": platform.system(),
            "cpu_count": os.cpu_count(),
            "cpu": platform.processor(),
            "platform": platform.platform(),
            "ram": round(psutil.virtual_memory().total / (1024.0 **3)),
            "hostname": node_name,
            "gpus": gpus
        },
        "version": local_version
    }

    response = requests.post(
        url=urljoin(backend_endpoint, "/uptick"),
        json=data,
        headers={'X-API-KEY': backend_api_key}
    )
    response.raise_for_status()
    return response.json()


def resource_path(relative_path):
    """ Get absolute path to resource, works for dev and for PyInstaller """
    try:
        # PyInstaller creates a temp folder and stores path in _MEIPASS
        base_path = sys._MEIPASS
    except Exception:
        base_path = os.path.abspath(".")

    return os.path.join(base_path, relative_path)

def user_path(relative_path, create_path=False):
    """Transform a relative path into the user's cache folder path"""
    base = os.path.expanduser("~")
    kalavai_user_path = os.path.join(base, ".cache/kalavai")
    full_path = os.path.join(kalavai_user_path, relative_path)
    if create_path:
        Path(full_path).mkdir(parents=True, exist_ok=True)
    
    return full_path

def safe_remove(filepath, force=True):
    if not os.path.exists(filepath):
        return
    try:
        if os.path.isfile(filepath):
            os.remove(filepath)
        if os.path.isdir(filepath):
            shutil.rmtree(filepath)
    except:
        if force:
            run_cmd(f"sudo rm -rf {filepath}")
