from collections import defaultdict
import math
import os
import json
import uuid
import time
import socket
from pathlib import Path
from typing import Annotated
import re

import yaml

import arguably
from rich.console import Console

from kalavai_client.cluster import CLUSTER
from kalavai_client.env import (
    USER_COOKIE,
    USER_LOCAL_SERVER_FILE,
    CONTAINER_HOST_PATH,
    USER_COMPOSE_FILE,
    USER_HELM_APPS_FILE,
    USER_KUBECONFIG_FILE,
    USER_VPN_COMPOSE_FILE,
    USER_TEMPLATES_FOLDER,
    DOCKER_COMPOSE_GUI,
    USER_GUI_COMPOSE_FILE,
    user_path,
    resource_path,
)
from kalavai_client.core import (
    generate_worker_package,
    load_gpu_models,
    check_token,
    attach_to_pool,
    join_pool,
    create_pool,
    get_ip_addresses,
    pause_agent,
    resume_agent,
    stop_pool,
    TokenType,
    update_pool,
    fetch_pool_services
)
from kalavai_client.utils import (
    check_gpu_drivers,
    get_max_gpus,
    load_template,
    run_cmd,
    user_confirm,
    generate_table,
    request_to_server,
    safe_remove,
    load_server_info,
    load_user_id,
    parse_key_value_pairs,
    request_to_api,
    store_server_info,
    has_api_details,
    CLUSTER_NAME_KEY,
    KALAVAI_AUTH,
    KALAVAI_API_URL_KEY,
    KALAVAI_API_KEY_KEY
)


LOCAL_TEMPLATES_DIR = os.getenv("LOCAL_TEMPLATES_DIR", None)
VERSION = 1
RESOURCE_EXCLUDE = ["ephemeral-storage", "hugepages-1Gi", "hugepages-2Mi", "pods"]
CORE_NAMESPACES = ["lws-system", "kube-system", "gpu-operator", "kalavai"]
RAY_LABEL = "kalavai.ray.name"
PVC_NAME_LABEL = "kalavai.storage.name"
VPN_COMPOSE_TEMPLATE = resource_path("kalavai_client/assets/vpn-template.yaml")
STORAGE_CLASS_NAME = "local-path"
STORAGE_ACCESS_MODE = ["ReadWriteOnce"]
DEFAULT_STORAGE_NAME = "pool-cache"
DEFAULT_STORAGE_SIZE = 20

    
console = Console()


######################
## HELPER FUNCTIONS ##
######################


def cleanup_local():
    console.log("Removing local cache files...")
    safe_remove(CONTAINER_HOST_PATH)
    safe_remove(USER_COMPOSE_FILE)
    safe_remove(USER_VPN_COMPOSE_FILE)
    safe_remove(USER_HELM_APPS_FILE)
    safe_remove(USER_KUBECONFIG_FILE)
    safe_remove(USER_LOCAL_SERVER_FILE)
    safe_remove(USER_TEMPLATES_FOLDER)
    #safe_remove(USER_GUI_COMPOSE_FILE)

def pre_join_check(node_name, server_url, server_key):
    # check with the server that we can connect
    try:
        nodes = request_to_server(
            force_url=server_url,
            force_key=server_key,
            method="get",
            endpoint="/v1/get_nodes",
            data={"node_names": [node_name]},
            server_creds=USER_LOCAL_SERVER_FILE,
            user_cookie=USER_COOKIE
        )
        return node_name not in nodes.keys()
    except Exception as e:
        console.log(f"[red]Error when connecting to kalavai service: {str(e)}")
        return False

def select_ip_address(subnet=None):
    ips = get_ip_addresses(subnet=subnet)
    if len(ips) == 1:
        return ips[0]

    while True:
        option = user_confirm(
            question="Select IP to advertise the node (needs to be visible to other nodes)",
            options=ips
        )
        if option is not None:
            break
        else:
            console.log("[red] Input error")
    return ips[option]

def select_gpus(message):
    console.log(f"[yellow]{message}")
    gpu_models = ["Any/None"]
    gpu_models_full = ["Any/None"]
    available_gpus = load_gpu_models()
    for _, gpus in available_gpus:
        for gpu in gpus["gpus"]:
            #status = "free" if "ready" in gpu else "busy"
            memory = math.floor(int(gpu['memory'])/1000)
            gpu_models.append(gpu['model'])
            gpu_models_full.append(f"{gpu['model']} ({memory}GB) (in use: {gpus['available'] == 0})" )
    
    while True:
        options = user_confirm(
            question=" ",
            options=gpu_models_full,
            multiple=True
        )
        if options is not None:
            if 0 in options:
                ids = None
            else:
                ids = ",".join([gpu_models[i] for i in options])
            break
    return ids

def select_token_type():
    options = ["Admin", "User (deploy jobs)", "Worker (read only)"]
    
    while True:
        choice = user_confirm(
            question="What type of access are you granting?",
            options=options,
            multiple=False
        )
        if choice is not None:
            break
    return {"admin": choice == 0, "user": choice == 1, "worker": choice == 2}

def input_gpus(non_interactive=False):
    num_gpus = 0
    try:
        has_gpus = check_gpu_drivers()
        if has_gpus:
            max_gpus = get_max_gpus()
            if non_interactive:
                num_gpus = max_gpus
            else:
                num_gpus = user_confirm(
                    question=f"{max_gpus} NVIDIA GPU(s) detected. How many GPUs would you like to include?",
                    options=range(max_gpus+1)
                ) 
    except:
        console.log(f"[red]WARNING: error when fetching NVIDIA GPU info. GPUs will not be used on this local machine")
    return num_gpus

def show_connection_suggestion():
    console.log("[red]Not connected to a local or remote pool")
    console.log("Suggestions:")
    console.log("- Create a pool: [yellow]kalavai pool start")
    console.log("- Join a pool: [yellow]kalavai pool join")
    console.log("- Connect to a remote pool: [yellow]kalavai pool connect")

##################
## CLI COMMANDS ##
##################

@arguably.command
def check__gpus(*others):
    """Check if gpus are detected in the local machine"""
    has_gpus = check_gpu_drivers()
    if has_gpus:
        max_gpus = get_max_gpus()
        console.log(f"Has GPUs: {has_gpus}")
        console.log(f"Max GPUs: {max_gpus}")
    else:
        console.log("[red]No local GPUs detected")
    

@arguably.command
def pool__spaces(*others):
    """List available user spaces in the pool"""
    spaces = request_to_api(
        method="GET",
        endpoint="/get_available_user_spaces"
    )
    console.log("Available user spaces")

    if "error" in spaces:
        console.log(f"[red]Error: {spaces}")
    for space in spaces:
        console.log(f"-> {space}")

@arguably.command
def gui__start(
    *others,
    version="latest"
):
    """Run GUI (docker) and kalavai core backend (api)"""
    ports_needed = 2
    # find 2 available ports
    ip = socket.gethostbyname (socket.gethostname())
    ports = []
    for port in range(49153,65535):
        try:
            serv = socket.socket(socket.AF_INET,socket.SOCK_STREAM) # create a new socket
            serv.bind((ip, port)) # bind socket with address
            serv.close()
            ports.append(port)
        except:
            #port closed
            pass
        if len(ports) >= ports_needed:
            break
    
    if len(ports) < ports_needed:
        # if not found, error
        console.log(f"[red]Cannot initialise GUI: Could not find {ports_needed} free ports in your machine")    
        return
    console.log(f"Using ports: {ports}")
    kalavai_api_url = load_server_info(data_key=KALAVAI_API_URL_KEY, file=USER_LOCAL_SERVER_FILE)
    if kalavai_api_url is None:
        show_connection_suggestion()
        return

    user_key = load_server_info(data_key=KALAVAI_API_KEY_KEY, file=USER_LOCAL_SERVER_FILE)
    if user_key is not None:
        console.log(f"[green]Using user key: {user_key}")
    
    values = {
        "gui_frontend_port": ports[0],
        "gui_backend_port": ports[1],
        "kalavai_api_url": kalavai_api_url,
        "path": user_path("", create_path=True),
        "protected_access": user_key,
        "gui_version": version
    }
    compose_yaml = load_template(
        template_path=DOCKER_COMPOSE_GUI,
        values=values)
    with open(USER_GUI_COMPOSE_FILE, "w") as f:
        f.write(compose_yaml)
    
    run_cmd(f"docker compose --file {USER_GUI_COMPOSE_FILE} up -d")

    console.log(f"[green]Loading GUI, may take a few minutes. It will be available at http://localhost:{ports[0]}")
    console.log("Run [yellow]kalavai gui stop[white] to stop running the GUI")

@arguably.command
def gui__stop():
    try:
        run_cmd(f"docker compose --file {USER_GUI_COMPOSE_FILE} down")
    except Exception as e:
        console.log(f"Error when stopping GUI: {str(e)}. IGNORE if GUI was not running before")
    
@arguably.command
def auth(user_key, *others):
    """
    [AUTH] (For public clusters only) Log in to Kalavai server.
    """
    KALAVAI_AUTH.save_auth(user_key)
    if KALAVAI_AUTH.is_authenticated():
        console.log(f"[green]User key stored")
    else:
        console.log(f"[red]Invalid user key")

@arguably.command
def logout(*others):
    """
    Log out of Kalavai server.
    """
    KALAVAI_AUTH.clear_auth()
    console.log(f"[green]User key removed")

@arguably.command
def pool__package_worker(output_file, *others, platform="amd64", num_gpus=0, ip_address="0.0.0.0", node_name=None, storage_compatible=True):
    """
    [AUTH]Package a worker for distribution (docker compose only)
    """

    if not CLUSTER.is_seed_node():
        console.log(f"[red]You can only create workers from a seed node")
        return
    
    compose = generate_worker_package(
        target_platform=platform,
        num_gpus=num_gpus,
        ip_address=ip_address,
        node_name=node_name,
        storage_compatible=storage_compatible
    )

    if "error" in compose:
        console.log(f"[red]{compose['error']}")
    else:
        console.log(f"[green]Worker package created: {output_file}")
        with open(output_file, "w") as f:
            f.write(compose)

@arguably.command
def pool__credentials(*others):
    """
    Show credentials details for a remote machine to connect to local pool
    """
    if not has_api_details():
        show_connection_suggestion()
        return
    
    data = request_to_api(
        method="GET",
        endpoint="/get_pool_credentials"
    )
    try:
        url = data[KALAVAI_API_URL_KEY]
        key = data[KALAVAI_API_KEY_KEY]

        console.log(f"[green]Kalavai API URL: {url}")
        console.log(f"[green]Kalavai API Key: {key}")
        console.log("\n")
        console.log(f"Run the following from a remote machine to connect to this pool")
        console.log(f"[yellow]kalavai pool connect {url} {key}")
    except Exception as e:
        console.log(f"[red]Error: {e}")

@arguably.command
def pool__connect(url: str, key: str, *others):
    """
    Connect local instance to a remote kalavai pool.

    This does not join the physical machine to the pool, just connects to 
    the pool API.
    """
    url_with_port_regex = re.compile(
        r'^https?:\/\/'         # Start with 'http://' or 'https://'
        r'(([a-zA-Z0-9.-]+)|(localhost))' # **CAPTURE GROUP 1: The address/domain/localhost**
        r':\d{1,5}$'            # Colon and port
    )

    match = url_with_port_regex.match(url)
    if not match:
        console.log("[red]Unexpected url format, expected http://<address>:<port>")
        return
    ip_address = match.group(1)
    
    # - check if user connected already --> reject if so
    if has_api_details():
        option = user_confirm(
            question="You seem to be connected to an instance already. Are you sure you want to join a new one? You will lose access to the current pool and this cannot be reversed",
            options=["no", "yes"]
        )
        if option == 0:
            console.log("[green]Nothing happened.")
            return
        else:
            console.log("[yellow]Overwriting old config...")

    # test connection
    import requests
    response = requests.get(f"{url}/health")
    
    if response.status_code != 200:
        console.log(f"[red]Connection error. Cannot find external API at {url}")
        return
    
    # store new details for remote API
    store_server_info(
        file=USER_LOCAL_SERVER_FILE,
        kalavai_api_url=url,
        kalavai_api_key=key,
        server_ip=ip_address,
        auth_key=None,
        watcher_service=None,
        node_name=None,
        cluster_name=None
    )
    
    console.log(f"[green]Local instance connected to {url}")
    

@arguably.command
def pool__start(
    *others, 
    pool_config_file=None,
    apps: list=None,
    mtu: str="",
    watcher_image_tag: str=None,
    platform="amd64",
    ip_address: str=None,
    lb_address: str=None,
    location: str=None,
    non_interactive: bool=False,
    kalavai_api_version: str=None,
    node_labels: Annotated[dict, arguably.arg.handler(parse_key_value_pairs)] = {}
):

    """
    Start Kalavai pool and start/resume sharing resources.

    Args:
        *others: all the other positional arguments go here
    """

    if CLUSTER.is_cluster_init():
        console.log(f"[white] You are already connected to {load_server_info(data_key=CLUSTER_NAME_KEY, file=USER_LOCAL_SERVER_FILE)}. Enter [yellow]kalavai pool stop[white] to exit and join another one.")
        return
    
    if non_interactive and ip_address is None:
        import public_ip
        ip_address = public_ip.get()
        console.log(f"[blue]Warning: 'non-interactive' mode without a set 'ip-address' requires a public IP on the node ({ip_address} was discovered). If the machine is not accessible via the internet, the process will stall.")

    if node_labels:
        console.log(f"[blue]Configuration received: {node_labels}")
    
    # User acknowledgement
    if not non_interactive:
        option = user_confirm(
            question="Kalavai will now create a pool and a local worker using docker. This won't modify your system. Are you happy to proceed?",
            options=["no", "yes"]
        )
        if option == 0:
            console.log("Installation was cancelled and did not complete.")
            return
    
    # select IP address (for external discovery)
    if ip_address is None and location is None:
        if non_interactive:
            ip_address = "0.0.0.0"
            console.log("[yellow]Using [green]0.0.0.0 [yellow]for server address")
        else:
            # local IP
            console.log(f"Scanning for valid IPs")
            ip_address = select_ip_address()
    
    console.log(f"Using {ip_address} address for server")

    console.log(f"[green]Creating pool, this may take a few minutes...")

    result = create_pool(
        ip_address=ip_address,
        lb_ip_address=lb_address,
        location=location,
        target_platform=platform,
        watcher_image_tag=watcher_image_tag,
        pool_config_file=pool_config_file,
        apps=apps,
        num_gpus=input_gpus(non_interactive=non_interactive),
        mtu=mtu,
        node_labels=node_labels,
        kalavai_api_version=kalavai_api_version
    )

    if "warning" in result:
        console.log(f"[yellow]Warning: {result['warning']}")
    if "error" in result:
        console.log(f"[red]{result}")
    else:
        console.log("[green]Pool is ready to use and running in the background. Access it via:")
        console.log("[green]- GUI: [yellow]kalavai gui start")
        console.log("[green]- CLI: [yellow]kalavai --help")


@arguably.command
def pool__token(*others, admin=False, user=False, worker=False):
    """
    Generate a join token for others to connect to your pool
    """
    # try:
    #     CLUSTER.validate_cluster()
    # except Exception as e:
    #     console.log(f"[red]Problems with your pool: {str(e)}")
    #     return
    if not has_api_details():
        show_connection_suggestion()
        return
    
    if not admin and not user and not worker:
        console.log(f"[red]Select at least one mode (--admin, --user or --worker)")
        return
    
    if admin:
        mode = TokenType.ADMIN
    elif user:
        mode = TokenType.USER
    else:
        mode = TokenType.WORKER

    #join_token = get_pool_token(mode=mode)
    join_token = request_to_api(
        method="GET",
        endpoint="/get_pool_token",
        params={"mode": mode.value}
    )

    if "error" in join_token:
        console.log(f"[red]{join_token}")
    else:
        console.log("[green]Join token:")
        print(join_token["token"])
    return join_token

@arguably.command
def pool__check_token(token, *others, public=False, verbose=False):
    """
    Utility to check the validity of a join token
    """
    
    result = check_token(token=token, public=public)
    if "error" in result:
        console.log(f"[red]Error in token: {result}")
        return False
    if verbose:
        console.log(json.dumps(result["data"], indent=2))
    
    console.log("[green]Token format is correct")
    return True

@arguably.command
def pool__join(
    token,
    *others,
    mtu="",
    platform="amd64",
    node_name=None,
    non_interactive=False,
    node_labels: Annotated[dict, arguably.arg.handler(parse_key_value_pairs)] = {},
    seed: bool=False,
    kalavai_api_version: str=None
):
    """
    Join Kalavai pool and start/resume sharing resources.

    Args:
        token: Pool join token
        *others: all the other positional arguments go here
        mtu: Maximum transmission unit
        platform: Target platform (default: amd64)
        node_name: Name for this node
        non_interactive: Run in non-interactive mode
        node_labels: Node labels as key=value pairs (e.g., "key1=value1,key2=value2")
        seed: if the node should join as an extra seed (for HA deployments)
    """
    
    # Process node labels if provided
    if node_labels:
        console.log(f"[blue]Configuration received: {node_labels}")
    
    # check that k3s is not running already in the host
    # k3s service running or preinstalled
    if CLUSTER.is_agent_running():
        console.log(f"[white] You are already connected to {load_server_info(data_key=CLUSTER_NAME_KEY, file=USER_LOCAL_SERVER_FILE)}. Enter [yellow]kalavai pool stop[white] to exit and join another one.")
        return
    
    # check that is not attached to another instance
    if not non_interactive:
        if os.path.exists(USER_LOCAL_SERVER_FILE):
            option = user_confirm(
                question="You seem to be connected to an instance already. Are you sure you want to join a new one?",
                options=["no", "yes"]
            )
            if option == 0:
                console.log("[green]Nothing happened.")
                return
    
    user_id = load_user_id()
    if user_id is None:
        console.log("You are not authenticated. If you want to authenticate your node, use [yellow]kalavai auth <user_key>")
    
    num_gpus = input_gpus(non_interactive=non_interactive)

    if not non_interactive:
        option = user_confirm(
            question="Docker compose ready. Would you like Kalavai to deploy it?",
            options=["no", "yes"]
        )
        if option == 0:
            console.log("[red]Installation aborted")
            return
    
    # select IP address (for external discovery)
    console.log(f"Scanning for valid IPs")
    if non_interactive:
        ip_address = "0.0.0.0"
        console.log("[yellow]Using [green]0.0.0.0 [yellow]for server address")
    else:
        ip_address = select_ip_address()
    
    console.log("Connecting worker to the pool...")
    result = join_pool(
        target_platform=platform,
        token=token,
        node_name=node_name,
        num_gpus=num_gpus,
        ip_address=ip_address,
        mtu=mtu,
        node_labels=node_labels,
        is_seed=seed,
        kalavai_api_version=kalavai_api_version
    )
    if "error" in result:
        console.log(f"[red]Error when connecting: {result}")
    else:
        console.log(f"[green] You are connected to {result}")

@arguably.command
def pool__stop(*others, skip_node_deletion=False):
    """
    Stop sharing your device and clean up. DO THIS ONLY IF YOU WANT TO REMOVE KALAVAI-CLIENT from your device.

    Args:
        *others: all the other positional arguments go here
    """
    console.log("[white] Stopping kalavai GUI...")
    gui__stop()
    console.log("[white] Stopping kalavai app...")
    result = stop_pool(skip_node_deletion=skip_node_deletion)
    if "error" in result:
        console.log(f"[red]{result['error']}")
    else:
        console.log(result)
        console.log("[white] Kalavai has stopped sharing your resources. Use [yellow]kalavai pool start[white] or [yellow]kalavai pool join[white] to start again!")

@arguably.command
def pool__pause(*others):
    """
    Pause sharing your device and make your device unavailable for kalavai scheduling.

    Args:
        *others: all the other positional arguments go here
    """
    # k3s stop locally
    if not CLUSTER.is_cluster_init():
        console.log("[red] Kalavai pool not running locally. Cannot pause, please run [yellow]kalavai pool start[red] to start a pool or [yellow]kalavai pool join[red] to join one first")
        return
    console.log("[white] Pausing kalavai app...")
    success = pause_agent()
    if "error" in success:
        console.log(f"[red] Error when stopping. {success['error']}")
    else:
        console.log("[white] Kalava sharing paused. Resume with [yellow]kalavai pool resume")
        

@arguably.command
def pool__resume(*others):
    """
    Resume sharing your device and make device available for kalavai scheduling.

    Args:
        *others: all the other positional arguments go here
    """
    if not CLUSTER.is_cluster_init():
        console.log("[red] Kalavai pool not running locally. Cannot resume, please run [yellow]kalavai pool start[red] to start a pool or [yellow]kalavai pool join[red] to join one first")
        return
    console.log("[white] Restarting sharing (may take a few minutes)...")
    success = resume_agent()
    if "error" in success:
        console.log(f"[red] Error when restarting. {success['error']}")
    else:
        console.log("[white] Kalava sharing resumed")

@arguably.command
def pool__gpus(*others, available=False):
    """
    Display GPU information from all connected nodes
    """

    if not has_api_details():
        show_connection_suggestion()
        return
    

    gpus = request_to_api(
        method="GET",
        endpoint="/fetch_gpus",
        params={"available": available}
    )
    if "error" in gpus:
        console.log(f"[red]Error when fetching gpus: {gpus}")
        return
    
    columns = ["Node", "Ready", "GPU(s)", "Available", "Total"]
    rows = []
    try:
        for gpu in gpus:
            rows.append([
                gpu["node"],
                str(gpu["ready"]),
                "\n".join(gpu["models"]),
                str(gpu["available"]),
                str(gpu["total"])
            ])
        console.print(
            generate_table(columns=columns, rows=rows,end_sections=[n for n in range(len(rows))])
        )
    except Exception as e:
        console.log(f"[red]Error: {str(e)}")

@arguably.command
def pool__resources(*others):
    """
    Display information about resources on the pool
    """
    if not has_api_details():
        show_connection_suggestion()
        return
    
    data = request_to_api(
        method="GET",
        endpoint="/fetch_resources"
    )

    if "error" in data:
        console.log(f"[red]Error when connecting to kalavai service: {data}")
        return
    
    columns = []
    total_values = []
    available_values = []
    for col in data["total"].keys():
        if col in RESOURCE_EXCLUDE:
            continue
        columns.append(col)
        total_values.append(str(data["total"][col]))
        available_values.append(str(data["available"][col]))
    
    columns = [""] + columns
    total_values = ["Total"] + total_values
    available_values = ["Available"] + available_values
    
    rows = [
        tuple(available_values),
        tuple(total_values)
    ]
    console.print(
        generate_table(columns=columns, rows=rows, end_sections=[0, 1])
    )
        

@arguably.command
def pool__update(*others):
    """
    Update kalavai pool
    """
    result = update_pool(debug=True)

    if "error" in result:
        console.log(f"[red]{result['error']}")
    else:
        console.log(f"[green]{result}")

@arguably.command
def pool__logs(*others, tail: int=100):
    """
    Get the logs for the Kalavai API
    """
    if not has_api_details():
        show_connection_suggestion()
        return
    
    logs = request_to_api(
        method="GET",
        endpoint="/fetch_service_logs",
        params={"tail": tail}
    )

    for name, log in logs.items():
        console.log(f"[yellow]LOGS for service: {name}")
        for key, value in log.items():
            console.log(f"[yellow]{key}")
            console.log(json.dumps(value, indent=2))

@arguably.command
def pool__status(*others, log_file=None):
    """
    Run diagnostics on a local installation of kalavai
    * is pool installed
    * is agent running
    * is kube-watcher running
    * is lws running
    """
    logs = []

    logs.append("Getting deployment status...")

    if CLUSTER.is_seed_node():
        # seed node
        data = CLUSTER.diagnostics()
        logs.append(data)
    else:
        # worker node
        logs.append("Could not access node info. This info is only available to seed nodes. Ignore if you are on a worker node.")
    logs.append(f"Worker installed: {CLUSTER.is_cluster_init()}")

    logs.append(f"Worker running: {CLUSTER.is_agent_running()}")

    logs.append(f"Pool credentials present: {CLUSTER.validate_cluster()}")

    logs.append(f"Is connected to Kalavai API (local/external): {has_api_details()}")
    
    if log_file is not None:
        with open(log_file, "w") as f:
            for log in logs:
                f.write(log)
                f.write("\n")
        console.log(f"[green]Logs written to {log_file}")
    else:
        for log in logs:
            console.log(f"{log}\n")

@arguably.command
def pool__attach(token, *others, node_name=None):
    """
    Set creds in token on the local instance
    """

    if node_name is None:
        node_name = f"{socket.gethostname()}-{uuid.uuid4().hex[:6]}"
    
    # check that is not attached to another instance
    if os.path.exists(USER_LOCAL_SERVER_FILE):
        option = user_confirm(
            question="You seem to be connected to an instance already. Are you sure you want to join a new one?",
            options=["no", "yes"]
        )
        if option == 0:
            console.log("[green]Nothing happened.")
            return
    
    option = user_confirm(
        question="Docker compose ready. Would you like Kalavai to deploy it?",
        options=["no", "yes"]
    )
    if option == 0:
        console.log("Manually deploy the worker with the following command:\n")
        print(f"docker compose -f {USER_COMPOSE_FILE} up -d")
        return
    
    result = attach_to_pool(token=token, node_name=node_name)
    
    if "error" in result:
        console.log(f"[red]Error when attaching to pool: {result}")
        return
    # set status to schedulable
    console.log(f"[green] You are connected to {result}")

@arguably.command
def pool__services(*others, force_namespace: str = None):
    """
    Pool Services available
    """
    if not has_api_details():
        show_connection_suggestion()
        return
    
    # services = fetch_pool_services(force_namespace=force_namespace)
    # print(services)
    # exit()
    
    services = request_to_api(
        method="GET",
        endpoint="/fetch_pool_services"
    )
    if "error" in services:
        console.log(f"[red]Error when fetching services: {services}")
        return
    
    console.log("Services available in the pool")
    for namespace, ns_service in services.items():
        console.log(f"[green]{namespace} services:")
        console.log(json.dumps(ns_service, indent=2))
        console.log("-------------")

@arguably.command
def pool__usage(*others, start_time: str="24h", end_time: str="now"):
    from kalavai_client.api import get_compute_usage

    devices = request_to_api(
        method="GET",
        endpoint="/fetch_devices"
    )
    if "error" in devices:
        console.log(f"[red]Error when fetching devices: {devices}")
        return
    devices = [device["name"] for device in devices]

    console.log(f"Getting usage for: {devices}")
    usage = get_compute_usage(
        node_names=devices,
        start_time=start_time,
        end_time=end_time
    )
    if "error" in usage:
        console.log(f"[red]Error when fetching usage: {usage}")
        return
    console.log(json.dumps(usage, indent=2))


@arguably.command
def pool__metrics(*others, start_time: str="24h", end_time: str="now"):
    from kalavai_client.api import get_nodes_metrics

    devices = request_to_api(
        method="GET",
        endpoint="/fetch_devices"
    )
    if "error" in devices:
        console.log(f"[red]Error when fetching devices: {devices}")
        return
    devices = [device["name"] for device in devices]
    console.log(f"Getting metrics for: {devices}")
    metrics = get_nodes_metrics(
        node_names=devices,
        start_time=start_time,
        end_time=end_time
    )
    if "error" in metrics:
        console.log(f"[red]Error when fetching metrics: {metrics}")
        return
    console.log(json.dumps(metrics, indent=2))

@arguably.command
def repositories__update(*others):
    """
    Update local Helm repositories
    """
    if not has_api_details():
        show_connection_suggestion()
        return
    
    result = request_to_api(
        method="POST",
        endpoint="/update_repositories"
    )

    if "error" in result:
        console.log(f"[red]{result['error']}")
    else:
        console.log(f"[green]Repositories updated successfully: {result}")

@arguably.command
def storage__create(name, storage, *others, force_namespace: str=None):
    """
    Create storage for the cluster
    """
    try:
        CLUSTER.validate_cluster()
    except Exception as e:
        console.log(f"[red]Problems with your pool: {str(e)}")
        return
    
    if force_namespace is not None:
        console.log("[WARNING][yellow]--force-namespace [white]requires an admin key. Request will fail if you are not an admin.")

    # Deploy PVC
    data = {
        "name": name,
        "labels": {
            PVC_NAME_LABEL: name,
            "kalavai.resource": "storage"
        },
        "access_modes": STORAGE_ACCESS_MODE,
        "storage_class_name": STORAGE_CLASS_NAME,
        "storage_size": storage
    }
    if force_namespace is not None:
        data["force_namespace"] = force_namespace

    try:
        result = request_to_server(
            method="post",
            endpoint="/v1/deploy_storage_claim",
            data=data,
            server_creds=USER_LOCAL_SERVER_FILE,
            user_cookie=USER_COOKIE
        )
        if "error" in result or "detail" in result:
            console.log(f"Error: {result}")
        else:
            console.log(f"Storage {name} ({storage}Gi) created")
    except Exception as e:
        console.log(f"[red]Error when connecting to kalavai service: {str(e)}")


@arguably.command
def storage__list(*other):
    """
    List existing storages deployed in the pool
    """
    try:
        CLUSTER.validate_cluster()
    except Exception as e:
        console.log(f"[red]Problems with your pool: {str(e)}")
        return

    try:
        result = request_to_server(
            method="post",
            endpoint="/v1/get_storage_usage",
            data={},
            server_creds=USER_LOCAL_SERVER_FILE,
            user_cookie=USER_COOKIE
        )

        columns = []
        rows = []
        for namespace, storages in result.items():
            for name, values in storages.items():
                columns = list(values.keys())
                rows.append([namespace, name] + [f"{v:.2f} MB" if "capacity" in k else str(v) for k, v in values.items()])
        
        if len(rows) == 0:
            console.log("[green] Storages have not been claimed yet (did you deploy any job using them?)")
            return
        columns = ["Owner", "Name"] + columns
        table = generate_table(columns=columns, rows=rows)
        console.log(table)

    except Exception as e:
        console.log(f"[red]Error when connecting to kalavai service: {str(e)}")
    
@arguably.command
def storage__delete(name, *others, force_namespace: str=None):
    """
    Delete storage by name
    """
    try:
        CLUSTER.validate_cluster()
    except Exception as e:
        console.log(f"[red]Problems with your pool: {str(e)}")
        return
    
    if force_namespace is not None:
        console.log("[WARNING][yellow]--force-namespace [white]requires an admin key. Request will fail if you are not an admin.")

    # deploy template with kube-watcher
    data = {
        "label": PVC_NAME_LABEL,
        "value": name
    }
    if force_namespace is not None:
        data["force_namespace"] = force_namespace
    try:
        result = request_to_server(
            method="post",
            endpoint="/v1/delete_labeled_resources",
            data=data,
            server_creds=USER_LOCAL_SERVER_FILE,
            user_cookie=USER_COOKIE
        )
        console.log(f"{result}")
    except Exception as e:
        console.log(f"[red]Error when connecting to kalavai service: {str(e)}")

@arguably.command
def node__list(*others):
    """
    Display information about nodes connected
    """
    if not has_api_details():
        show_connection_suggestion()
        return
    
    devices = request_to_api(
        method="GET",
        endpoint="/fetch_devices"
    )

    try:
        rows = []
        columns = ["Node name", "Memory Pressure", "Disk pressure", "PID pressure", "Ready", "Unschedulable"]
        for device in devices:
            rows.append([
                device["name"],
                str(device["memory_pressure"]),
                str(device["disk_pressure"]),
                str(device["pid_pressure"]),
                str(device["ready"]),
                str(device["unschedulable"])
            ])
        
        console.log("Nodes with 'unschedulable=True' will not receive workload")
        console.log("To make a node unschedulable (i.e. won't receive workloads) use [yellow]kalavai node cordon <node name>")
        console.log("To make a node schedulable (i.e. will receive workloads) use [yellow]kalavai node uncordon <node name>")
        console.print(
            generate_table(columns=columns, rows=rows)
        )
        
    except Exception as e:
        console.log(f"[red]Error when connecting to kalavai service: {str(e)}")


@arguably.command
def node__delete(node_name, *others):
    """
    Delete a node from the cluster
    """
    if not has_api_details():
        show_connection_suggestion()
        return
    
    result = request_to_api(
        method="POST",
        endpoint="/delete_nodes",
        json={"nodes": [node_name]}
    )
    
    #result = delete_nodes(nodes=[name])
    
    if "error" in result:
        console.log(f"[red]{result}")
    else:
        console.log(f"[green]{result}")

@arguably.command
def node__cordon(node_name, *others):
    """
    Cordon a particular node so no more work will be scheduled on it
    """
    if not has_api_details():
        show_connection_suggestion()
        return
    
    result = request_to_api(
        method="POST",
        endpoint="/cordon_nodes",
        params={"nodes": [node_name]}
    )
    if "error" in result:
        console.log(f"[red]{result['error']}")
    else:
        console.log(result)

@arguably.command
def node__uncordon(node_name, *others):
    """
    Uncordon a particular node to allow more work to be scheduled on it
    """
    if not has_api_details():
        show_connection_suggestion()
        return
    
    result = request_to_api(
        method="POST",
        endpoint="/uncordon_nodes",
        params={"nodes": [node_name]}
    )
    if "error" in result:
        console.log(f"[red]{result['error']}")
    else:
        console.log(result)

@arguably.command
def job__templates(*others):
    """
    Job templates integrated with kalavai. Use env var LOCAL_TEMPLATES_DIR to test local templates
    """
    if not has_api_details():
        show_connection_suggestion()
        return
    
    templates = request_to_api(
        method="GET",
        endpoint="/fetch_job_templates"
    )
    if "error" in templates:
        console.log(f"[red]Error when fetching templates: {templates}")
        return
    
    console.log("Templates available in the pool")
    for template in templates:
        console.log(json.dumps(template, indent=2))


@arguably.command
def job__run(job_name, template, *others, repo="kalavai-templates", values: str=None, force_namespace: str=None):
    """
    Deploy and run a template job.

    Args:
        *others: all the other positional arguments go here
    """
    if not has_api_details():
        show_connection_suggestion()
        return
    
    if force_namespace is not None:
        console.log("[WARNING][yellow]--force-namespace [white]requires an admin key. Request will fail if you are not an admin.")

    if values is None:
        values_dict = {}
    else:
        if not Path(values).is_file():
            console.log(f"[red]Values file {values} was not found")

        with open(values, "r") as f:
            values_dict = yaml.safe_load(f)

    data = {
        "name": job_name,
        "template_name": template,
        "template_repo": repo,
        "values": values_dict,
        "force_namespace": force_namespace
    }
    results = request_to_api(
        method="POST",
        endpoint="/deploy_job",
        json=data
    )

    if "error" in results:
        console.log(f"[red]Error when deploying job: {str(results['error'])}")
    else:
        try:
            success = len(results["successful"]) if "successful" in results else 0
            fail = len(results["failed"]) if "failed" in results else 0
            if success == 0 or fail > 0:
                console.log(f"[red]Unexpected results")
                console.log(f"[red]{results}")
            else:
                console.log(f"[green]Job '{job_name}' deployed ({success} OK, {fail} failed)")
        except Exception as e:
            console.log(f"[red]Error: {str(e)}")
            console.log(results)

@arguably.command
def job__test(local_template_dir, *others, values, force_namespace: str=None):
    """
    Helper to test local templates, useful for development
    """
    if not has_api_details():
        show_connection_suggestion()
        return
    
    if not os.path.isfile(os.path.join(local_template_dir, "template.yaml")):
        console.log(f"[red]template.yaml not found under {local_template_dir}")
        return
    if not os.path.isfile(os.path.join(local_template_dir, "values.yaml")):
        console.log(f"[red]values.yaml not found under {local_template_dir}")
        return
    
    # load template
    with open(os.path.join(local_template_dir, "template.yaml"), "r") as f:
        template_str = f.read()
    with open(os.path.join(local_template_dir, "values.yaml"), "r") as f:
        defaults = f.read()
    
    # load values
    if not os.path.isfile(values):
        console.log(f"[red]--values ({values}) is not a valid local file")
        return
    with open(values, "r") as f:
        raw_values = yaml.load(f, Loader=yaml.SafeLoader)
        values_dict = {variable["name"]: variable['value'] for variable in raw_values}

    data = {
        "template_str": template_str,
        "values": values_dict,
        "default_values": defaults,
        "target_labels": {}
    }
    if force_namespace is not None:
        data["force_namespace"] = force_namespace
    
    results = request_to_api(
        method="POST",
        endpoint="/deploy_custom_job",
        json=data
    )
    
    if "error" in results:
        console.log(f"[red]Error when deploying job: {str(results['error'])}")
    else:
        try:
            for job in results:
                success = len(job["result"]["successful"]) if "successful" in job["result"] else 0
                fail = len(job["result"]["failed"]) if "failed" in job["result"] else 0
                console.log(f"[green]Job ID {job['job_id']} deployed ({success} OK, {fail} failed)")
        except Exception as e:
            console.log(f"[red]{results}")
            console.log(f"[red]Error: {str(e)}")
            

@arguably.command
def job__info(template_name, *others):
    """
    Fetch all metadata for a specific template
    """
    if not has_api_details():
        show_connection_suggestion()
        return
    
    data = request_to_api(
        method="GET",
        endpoint="/fetch_template_all",
        params={"name": template_name}
    )

    if "error" in data:
        console.log(f"[red]Error when fetching template defaults: {data}")
        return
    
    for field in ["values", "metadata", "schema"]:
        if field in data:
            console.log("[blue]******************")
            console.log(f"[blue]**** {field} ****")
            console.log("[blue]******************")
            console.log(data[field])

@arguably.command
def job__defaults(template_name, *others):
    """
    Fetch default values.yaml for a template job
    """
    if not has_api_details():
        show_connection_suggestion()
        return
    
    data = request_to_api(
        method="GET",
        endpoint="/fetch_template_values",
        params={"name": template_name}
    )
    if data is None or "error" in data:
        console.log(f"[red]Error when fetching template defaults: {data}")
        return
    
    console.log(f"[blue]Default values for template {template_name}")
    console.log(f"[green]{json.dumps(data, indent=3)}")

@arguably.command
def job__delete(name, *others, force_namespace: str=None):
    """
    Delete job in the cluster
    """
    if not has_api_details():
        show_connection_suggestion()
        return
    
    if force_namespace is not None:
        console.log("[WARNING][yellow]--force-namespace [white]requires an admin key. Request will fail if you are not an admin.")
    
    data = {
        "name": name,
        "force_namespace": force_namespace
    }
    results = request_to_api(
        method="POST",
        endpoint="/delete_job",
        json=data
    )

    if "error" in results:
        console.log(f"[red]Error when deleting job: {results['error']}")
    else:
        console.log(f"[green]Successfully deleted {name}")


@arguably.command
def job__list(*others, force_namespace: str=None):
    """
    List jobs in the cluster
    """
    if not has_api_details():
        show_connection_suggestion()
        return
    
    data = {}
    if force_namespace is not None:
        data["force_namespace"] = force_namespace
    details = request_to_api(
        method="GET",
        endpoint="/fetch_job_details",
        params=data
    )

    if "error" in details:
        console.log(f"[red]{details}")
        return
    
    try:
        columns = ["ID", "Name", "Workers", "Endpoint"]
        rows = [[job["job_id"], job["name"], job["workers"], "\n".join([f"{k} -> {v['address']}:{v['port']}" for k, v in job["endpoint"].items()])] for job in details]
        
        console.print(
            generate_table(columns=columns, rows=rows, end_sections=range(len(rows)))
        )
            
        console.log("Get logs with [yellow]kalavai job logs <job id> [white](note it only works when the deployment is complete)")
    except Exception as e:
        console.log(f"[red]Error: {str(e)}")
        console.log(f"[red]Response: {details}")
        console.log("[red]Error when querying backend")

@arguably.command
def job__logs(job_id, *others, pod_name=None, tail=100, force_namespace: str=None):
    """
    Get logs for a specific job
    """
    if not has_api_details():
        show_connection_suggestion()
        return
    
    if force_namespace is not None:
        console.log("[WARNING][yellow]--force-namespace [white]requires an admin key. Request will fail if you are not an admin.")

    data = {
        "job_name": job_id,
        "pod_name": pod_name,
        "tail": tail,
    }
    if force_namespace is not None:
        data["force_namespace"] = force_namespace
    results = request_to_api(
        method="GET",
        endpoint="/fetch_job_logs",
        params=data)

    if "error" in results:
        console.log(f"[red]{results}")
        return
    for label_match, data in results.items():
        for pod, info in data.items():
            if pod_name is not None and pod_name != pod:
                continue
            if "logs" not in info:
                console.log(f"[white] Logs not ready for {pod}")
            else:
                logs = info["logs"]
                describe = info["describe"]
                console.log(f"[yellow]Logs for {pod} in {describe['spec']['node_name']}")
                console.log(f"[green]{logs}")
            console.log("---------------------------")
            console.log("---------------------------")
            if "describe" not in info:
                console.log(f"[white] Description not ready for {pod}")
            else:
                console.log(f"[yellow]Status {pod} in {describe['spec']['node_name']}")
                console.log(f"[green]{describe}")

def app():
    user_path("", create_path=True)
    arguably.run()

if __name__ == "__main__":
    app()