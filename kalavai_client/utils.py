import json, base64
import sys
import os
import requests
from pathlib import Path
from urllib.parse import urljoin
from string import Template 
import shutil
import urllib.request
import subprocess

from rich.table import Table
import yaml
import platform
import psutil
import GPUtil


GITHUB_ORG = "kalavai-net"
GITHUB_REPO = "kalavai-client"
GITHUB_TEMPLATE_PATH = "templates"


def run_cmd(command):
    try:
        return_value = subprocess.check_output(command, shell=True, executable="/bin/bash")
        return return_value
    except OSError as error:
        return error # for exit code


def is_service_running(service):
    return 0 == os.system(f'systemctl is-active --quiet {service}')


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
    for file in fetch_git_files(remote_folder=GITHUB_TEMPLATE_PATH):
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


def request_to_server(method, endpoint, data, server_creds):
    service_url = load_watcher_service_url(server_creds)
    auth_key = load_server_auth_key(server_creds)

    headers = {
        "X-API-KEY": auth_key
    }
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
    [table.add_column(col) for col in columns]
    for idx, row in enumerate(rows):
        table.add_row(*row, end_section=end_sections and idx in end_sections)

    return table

def store_server_info(server_ip, auth_key, watcher_service, file, node_name, cluster_name):
    with open(file, "w") as f:
        json.dump({"server_ip": server_ip, "auth_key": auth_key, "watcher_service": watcher_service, "node_name": node_name, "cluster_name": cluster_name}, f)
    return True

def load_server_ip(file):
    try:
        with open(file, "r") as f:
            return json.load(f)["server_ip"]
    except:
        return None

def load_node_name(file):
    try:
        with open(file, "r") as f:
            return json.load(f)["node_name"]
    except:
        return None

def load_cluster_name(file):
    try:
        with open(file, "r") as f:
            return json.load(f)["cluster_name"]
    except:
        return None

def load_server_auth_key(file):
    try:
        with open(file, "r") as f:
            return json.load(f)["auth_key"]
    except:
        return None

def load_watcher_service_url(file):
    try:
        with open(file, "r") as f:
            return json.load(f)["watcher_service"]
    except:
        return None

def load_template(template_path, values_path):
    if not Path(template_path).exists():
        raise FileNotFoundError(f"{template_path} does not exist")
    with open(template_path, 'r') as f:
        yaml_template = "".join(f.readlines())
    
    template = Template(yaml_template)

    if not Path(values_path).exists():
        raise FileNotFoundError(f"{values_path} does not exist")
    
    with open(values_path, "r") as f:
        raw_values = yaml.load(f, Loader=yaml.SafeLoader)
        values = {variable["name"]: variable['value'] for variable in raw_values["template_values"]}
    return template.substitute(values)


def user_confirm(question: str, options: list) -> int:
    try:
        [print(f"{idx}) {option}") for idx, option in enumerate(options)]
        reply = str(input(f"{question}: "))
        if reply.isnumeric():
            reply = int(reply)
            if reply >= 0 and reply <= len(options):
                return reply
    except:
        return None
    return None

def generate_join_token(cluster_ip, cluster_token, cluster_name, auth_key, watcher_service):
    data = {
        "cluster_ip": cluster_ip,
        "cluster_name": cluster_name,
        "cluster_token": cluster_token,
        "auth_key": auth_key,
        "watcher_service": watcher_service
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

def safe_remove(filepath):
    if os.path.exists(filepath):
        os.remove(filepath)
