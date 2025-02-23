from collections import defaultdict
import math
import os
import json
import uuid
import time
import socket
from pathlib import Path
from getpass import getpass
from sys import exit

import yaml

import arguably
from rich.console import Console

from kalavai_client.cluster import CLUSTER
from kalavai_client.bridge_api import run_api
from kalavai_client.env import (
    USER_COOKIE,
    USER_LOCAL_SERVER_FILE,
    TEMPLATE_LABEL,
    KALAVAI_PLATFORM_URL,
    DEFAULT_VPN_CONTAINER_NAME,
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
    fetch_resources,
    fetch_job_names,
    fetch_job_details,
    fetch_devices,
    fetch_job_logs,
    fetch_gpus,
    load_gpu_models,
    fetch_job_templates,
    fetch_job_defaults,
    deploy_job,
    delete_job,
    check_token,
    attach_to_pool,
    join_pool,
    create_pool,
    get_ip_addresses,
    pause_agent,
    resume_agent,
    get_pool_token,
    delete_nodes,
    TokenType
)
from kalavai_client.utils import (
    check_gpu_drivers,
    load_template,
    run_cmd,
    user_confirm,
    generate_table,
    request_to_server,
    safe_remove,
    leave_vpn,
    load_server_info,
    user_login,
    user_logout,
    get_public_vpns,
    register_cluster,
    unregister_cluster,
    get_public_seeds,
    load_user_session,
    SERVER_IP_KEY,
    NODE_NAME_KEY,
    CLUSTER_NAME_KEY
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
    safe_remove(USER_GUI_COMPOSE_FILE)

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
    
def set_schedulable(schedulable, node_name=load_server_info(data_key=NODE_NAME_KEY, file=USER_LOCAL_SERVER_FILE)):
    """
    Delete job in the cluster
    """
    # deploy template with kube-watcher
    data = {
        "schedulable": str(schedulable),
        "node_names": [node_name]
    }
    try:
        res = request_to_server(
            method="post",
            endpoint="/v1/set_node_schedulable",
            data=data,
            server_creds=USER_LOCAL_SERVER_FILE,
            user_cookie=USER_COOKIE
        )
        console.log(f"{res}")
    except Exception as e:
        console.log(f"[red]Error when connecting to kalavai service: {str(e)}")

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

def input_gpus():
    num_gpus = 0
    try:
        has_gpus = check_gpu_drivers()
        if has_gpus:
            max_gpus = int(run_cmd("nvidia-smi -L | wc -l").decode())
            num_gpus = user_confirm(
                question=f"{max_gpus} NVIDIA GPU(s) detected. How many GPUs would you like to include?",
                options=range(max_gpus+1)
            ) 
    except:
        console.log(f"[red]WARNING: error when fetching NVIDIA GPU info. GPUs will not be used on this local machine")
    return num_gpus

##################
## CLI COMMANDS ##
##################

@arguably.command
def gui__start(*others, backend_only=False, gui_frontend_port=3000, gui_backend_port=8000, bridge_port=8001):
    """Run GUI (docker) and kalavai core backend (api)"""

    if not backend_only:
        values = {
            "gui_frontend_port": gui_frontend_port,
            "gui_backend_port": gui_backend_port,
            "path": user_path("")
        }
        compose_yaml = load_template(
            template_path=DOCKER_COMPOSE_GUI,
            values=values)
        with open(USER_GUI_COMPOSE_FILE, "w") as f:
            f.write(compose_yaml)
        
        run_cmd(f"docker compose --file {USER_GUI_COMPOSE_FILE} up -d")

        console.log(f"[green]Loading GUI, may take a few minutes. It will be available at http://localhost:{gui_frontend_port}")
    run_api(port=bridge_port)
    
    if not backend_only:
        run_cmd(f"docker compose --file {USER_GUI_COMPOSE_FILE} down")
    console.log("[green]Kalavai GUI has been stopped")

@arguably.command
def login(*others,  username: str=None):
    """
    [AUTH] (For public clusters only) Log in to Kalavai server.

    Args:
        *others: all the other positional arguments go here
    """
    console.log(f"Kalavai account details. If you don't have an account, create one at [yellow]{KALAVAI_PLATFORM_URL}")
    if username is None:
        username = input("User email: ")
    password = getpass()
    user = user_login(
        user_cookie=USER_COOKIE,
        username=username,
        password=password
    )
    
    if user is not None:
        console.log(f"[green]{username} logged in successfully")
    else:
        console.log(f"[red]Invalid credentials for {username}")
    
    return user is not None

@arguably.command
def logout(*others):
    """
    [AUTH] (For public clusters only) Log out of Kalavai server.

    Args:
        *others: all the other positional arguments go here
    """
    user_logout(
        user_cookie=USER_COOKIE
    )
    console.log("[green]Log out successfull")

@arguably.command
def location__list(*others):
    """
    [AUTH] List public locations on Kalavai
    """
    try:
        seeds = get_public_vpns(user_cookie=USER_COOKIE)
    except Exception as e:
        console.log(f"[red]Error: {str(e)}")
        console.log("Are you authenticated? Try [yellow]kalavai login")
        return
    columns, rows = [], []
    for idx, seed in enumerate(seeds):
        columns = seed.keys()
        rows.append([str(idx)] + list(seed.values()))
    columns = ["VPN"] + list(columns)
    table = generate_table(columns=columns, rows=rows)
    console.log(table)

@arguably.command
def pool__publish(*others, description=None):
    """
    [AUTH] Publish pool to Kalavai platform, where other users may be able to join
    """
    # Check for:
    # - cluster is up and running
    # - cluster is connected to vpn (has net token)
    # - user is authenticated
    try:
        CLUSTER.is_seed_node()
    except Exception as e:
        console.log(f"[red]Problems with your pool: {str(e)}")
        return
    choices = select_token_type()
    token = pool__token(**choices)
    
    if description is None:
        console.log("[yellow] [Markdown] In a few words (max 500 chars), describe your goals with this cluster. Remember, this is what other users will see to decide whether to share their resources with you, [blue]so inspire them!")
        description = input(f"(You can edit this later in {KALAVAI_PLATFORM_URL}\n")
    
    description = description
    
    try:
        valid = check_token(token=token, public=True)
        if "error" in valid:
            raise ValueError(f"[red]Cluster must be started with a valid vpn_location to publish: {valid}")
        cluster_name = load_server_info(data_key=CLUSTER_NAME_KEY, file=USER_LOCAL_SERVER_FILE)
        
        register_cluster(
            name=cluster_name,
            token=token,
            description=description,
            user_cookie=USER_COOKIE)
        console.log(f"[green]Your cluster is now public on {KALAVAI_PLATFORM_URL}")
    except Exception as e:
        console.log(f"[red]Error when publishing cluster. {str(e)}")

@arguably.command
def pool__unpublish(cluster_name=None, *others):
    """
    [AUTH] Unpublish pool to Kalavai platform. Cluster and all its workers will still work
    """
    # Check for:
    # - cluster is up and running
    # - user is authenticated
    try:
        CLUSTER.is_seed_node()
    except Exception as e:
        console.log(f"[red]Problems with your pool: {str(e)}")
        return
    
    try:
        if cluster_name is None:
            cluster_name = load_server_info(data_key=CLUSTER_NAME_KEY, file=USER_LOCAL_SERVER_FILE)
        unregister_cluster(
            name=cluster_name,
            user_cookie=USER_COOKIE)
        console.log(f"[green]Your cluster has been removed from {KALAVAI_PLATFORM_URL}")
    except Exception as e:
        console.log(f"[red]Error when unpublishing cluster. {str(e)}")

@arguably.command
def pool__list(*others, user_only=False):
    """
    [AUTH] List public pools in to Kalavai platform.
    """
    try:
        seeds = get_public_seeds(
            user_only=user_only,
            user_cookie=USER_COOKIE)
    except Exception as e:
        console.log(f"[red]Error when loading pools. {str(e)}")
        return
    
    for seed in seeds:
        console.log("[yellow]************************************")
        for key, value in seed.items():
            if key == "join_key":
                continue
            console.log(f"[yellow]{key}: [green]{value}")
        print(f"Join key: {seed['join_key']}")
        console.log("[yellow]************************************")
    console.log("[white]Use [yellow]kalavai pool join <join key> [white]to join a public pool")


@arguably.command
def pool__start(cluster_name, *others,  only_registered_users: bool=False, ip_address: str=None, location: str=None, app_values: str=None, pool_config_values: str=None):
    """
    Start Kalavai pool and start/resume sharing resources.

    Args:
        *others: all the other positional arguments go here
    """

    if CLUSTER.is_cluster_init():
        console.log(f"[white] You are already connected to {load_server_info(data_key=CLUSTER_NAME_KEY, file=USER_LOCAL_SERVER_FILE)}. Enter [yellow]kalavai pool stop[white] to exit and join another one.")
        return
    
    # User acknowledgement
    option = user_confirm(
        question="Kalavai will now create a pool and a local worker using docker. This won't modify your system. Are you happy to proceed?",
        options=["no", "yes"]
    )
    if option == 0:
        console.log("Installation was cancelled and did not complete.")
        return
    
    # select IP address (for external discovery)
    if ip_address is None and location is None:
        # local IP
        console.log(f"Scanning for valid IPs")
        ip_address = select_ip_address()
    
    console.log(f"Using {ip_address} address for server")

    console.log(f"[green]Creating {cluster_name} pool, this may take a few minutes...")

    create_pool(
        cluster_name=cluster_name,
        ip_address=ip_address,
        app_values=app_values,
        pool_config_values=pool_config_values,
        num_gpus=input_gpus(),
        only_registered_users=only_registered_users,
        location=location
    )

    return None

@arguably.command
def pool__token(*others, admin=False, user=False, worker=False):
    """
    Generate a join token for others to connect to your pool
    """
    try:
        CLUSTER.validate_cluster()
    except Exception as e:
        console.log(f"[red]Problems with your pool: {str(e)}")
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

    join_token = get_pool_token(mode=mode)

    if "error" in join_token:
        console.log(f"[red]{join_token}")
    else:
        console.log("[green]Join token:")
        print(join_token)
    return join_token

@arguably.command
def pool__check_token(token, *others, public=False):
    """
    Utility to check the validity of a join token
    """
    result = check_token(token=token, public=public)
    if "error" in result:
        console.log(f"[red]Error in token: {result}")
        return False
    
    console.log("[green]Token format is correct")
    return True

@arguably.command
def pool__join(token, *others, node_name=None):
    """
    Join Kalavai pool and start/resume sharing resources.

    Args:
        *others: all the other positional arguments go here
    """
    
    # check that k3s is not running already in the host
    # k3s service running or preinstalled
    if CLUSTER.is_agent_running():
        console.log(f"[white] You are already connected to {load_server_info(data_key=CLUSTER_NAME_KEY, file=USER_LOCAL_SERVER_FILE)}. Enter [yellow]kalavai pool stop[white] to exit and join another one.")
        return
    
    # check that is not attached to another instance
    if os.path.exists(USER_LOCAL_SERVER_FILE):
        option = user_confirm(
            question="You seem to be connected to an instance already. Are you sure you want to join a new one?",
            options=["no", "yes"]
        )
        if option == 0:
            console.log("[green]Nothing happened.")
            return
    
    num_gpus = input_gpus()

    option = user_confirm(
        question="Docker compose ready. Would you like Kalavai to deploy it?",
        options=["no", "yes"]
    )
    if option == 0:
        console.log("[red]Installation aborted")
        return
    
    console.log("Connecting worker to the pool...")
    result = join_pool(
        token=token,
        node_name=node_name,
        num_gpus=num_gpus
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
    console.log("[white] Stopping kalavai app...")
    # delete local node from server
    if not skip_node_deletion:
        node__delete(load_server_info(data_key=NODE_NAME_KEY, file=USER_LOCAL_SERVER_FILE))
    # unpublish event (only if seed node)
    # TODO: no, this should be done via the platform!!!
    # try:
    #     if CLUSTER.is_seed_node():
    #         console.log("Unregistering pool...")
    #         unregister_cluster(
    #             name=load_server_info(data_key=CLUSTER_NAME_KEY, file=USER_LOCAL_SERVER_FILE),
    #             user_cookie=USER_COOKIE)
    # except Exception as e:
    #     console.log(f"[red][WARNING]: (ignore if not a public pool) Error when unpublishing cluster. {str(e)}")
    # remove local node agent
    console.log("Removing agent and local cache")
    
    # disconnect from VPN first, then remove agent, then remove local files
    console.log("Disconnecting from VPN...")
    try:
        vpns = leave_vpn(container_name=DEFAULT_VPN_CONTAINER_NAME)
        if vpns is not None:
            for vpn in vpns:
                console.log(f"You have left {vpn} VPN")
    except:
        # no vpn
        pass

    CLUSTER.remove_agent()

    # clean local files
    cleanup_local()
    console.log("[white] Kalavai has stopped sharing your resources. Use [yellow]kalavai pool start[white] or [yellow]kalavai pool join[white] to start again!")

@arguably.command
def pool__pause(*others):
    """
    Pause sharing your device and make your device unavailable for kalavai scheduling.

    Args:
        *others: all the other positional arguments go here
    """
    # k3s stop locally
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
    # k3s stop locally
    if not CLUSTER.is_cluster_init():
        console.log("[red] Kalavai app was not started before, please run [yellow]kalavai pool start[red] to start a pool or [yellow]kalavai pool join[red] to join one first")
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
    try:
        CLUSTER.validate_cluster()
    except Exception as e:
        console.log(f"[red]Problems with your pool: {str(e)}")
        return

    gpus = fetch_gpus(available=available)
    if "error" in gpus:
        console.log(f"[red]Error when fetching gpus: {gpus}")
        return
    
    columns = ["Node", "Ready", "GPU(s)", "Available", "Total"]
    rows = []
    for gpu in gpus:
        rows.append([
            gpu.node,
            str(gpu.ready),
            gpu.model,
            str(gpu.available),
            str(gpu.total)
        ])
    console.print(
        generate_table(columns=columns, rows=rows,end_sections=[n for n in range(len(rows))])
    )

@arguably.command
def pool__resources(*others):
    """
    Display information about resources on the pool
    """
    try:
        CLUSTER.validate_cluster()
    except Exception as e:
        console.log(f"[red]Problems with your pool: {str(e)}")
        return

    data = fetch_resources()
    if "error" in data:
        console.log(f"[red]Error when connecting to kalavai service: {str(e)}")
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
    try:
        CLUSTER.validate_cluster()
    except Exception as e:
        console.log(f"[red]Problems with your pool: {str(e)}")
        return
    
    if not CLUSTER.is_seed_node():
        console.log("You can only update a pool from the seed node.")
        return
    
    # update dependencies
    try:
        CLUSTER.update_dependencies(debug=True)
        console.log("Pool updating. Expect some downtime on core services")
    except Exception as e:
        console.log(f"[red]Error when updating pool: {str(e)}")
        return


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
        user = load_user_session(user_cookie=USER_COOKIE)
        username = user["username"] if user is not None else None
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
                if namespace == username:
                    namespace = f"**{namespace}**"
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
    try:
        CLUSTER.validate_cluster()
    except Exception as e:
        console.log(f"[red]Problems with your pool: {str(e)}")
        return

    try:
        devices = fetch_devices()
        rows = []
        columns = ["Node name", "Memory Pressure", "Disk pressure", "PID pressure", "Ready", "Unschedulable"]
        for device in devices:
            rows.append([
                device.name,
                str(device.memory_pressure),
                str(device.disk_pressure),
                str(device.pid_pressure),
                str(device.ready),
                str(device.unschedulable)
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
def node__delete(name, *others):
    """
    Delete a node from the cluster
    """
    try:
        CLUSTER.validate_cluster()
    except Exception as e:
        console.log(f"[red]Problems with your pool: {str(e)}")
        return
    
    result = delete_nodes(nodes=[name])
    
    if "error" in result:
        console.log(f"[red]{result}")
    else:
        console.log(f"[green]{result}")

@arguably.command
def node__cordon(node_name, *others):
    """
    Cordon a particular node so no more work will be scheduled on it
    """
    try:
        CLUSTER.validate_cluster()
    except Exception as e:
        console.log(f"[red]Problems with your pool: {str(e)}")
        return
    set_schedulable(schedulable=False, node_name=node_name)


@arguably.command
def node__uncordon(node_name, *others):
    """
    Uncordon a particular node to allow more work to be scheduled on it
    """
    try:
        CLUSTER.validate_cluster()
    except Exception as e:
        console.log(f"[red]Problems with your pool: {str(e)}")
        return
    set_schedulable(schedulable=True, node_name=node_name)


@arguably.command
def job__templates(*others):
    """
    Job templates integrated with kalavai. Use env var LOCAL_TEMPLATES_DIR to test local templates
    """
    try:
        CLUSTER.validate_cluster()
    except Exception as e:
        console.log(f"[red]Problems with your pool: {str(e)}")
        return
    
    templates = fetch_job_templates()
    if "error" in templates:
        console.log(f"[red]Error when fetching templates: {str(e)}")
        return
    
    console.log("Templates available in the pool")
    console.log(templates)


@arguably.command
def job__run(template_name, *others, values: str=None, force_namespace: str=None):
    """
    Deploy and run a template job.

    Args:
        *others: all the other positional arguments go here
    """
    try:
        CLUSTER.validate_cluster()
    except Exception as e:
        console.log(f"[red]Problems with your pool: {str(e)}")
        return
    
    if force_namespace is not None:
        console.log("[WARNING][yellow]--force-namespace [white]requires an admin key. Request will fail if you are not an admin.")

    if values is None:
        values_dict = {}
    else:
        if not Path(values).is_file():
            console.log(f"[red]Values file {values} was not found")

        with open(values, "r") as f:
            raw_values = yaml.load(f, Loader=yaml.SafeLoader)
            values_dict = {variable["name"]: variable['value'] for variable in raw_values}
    
    # Inject hardware information if not present in the template
    def generate_gpu_annotation(input_message, values, value_key, annotation_key):
        if value_key not in values:
            selection = select_gpus(message=input_message)
        else:
            selection = values[value_key]
        if selection is not None:
            values[value_key] = f"{annotation_key}: {selection}"
        else:
            values[value_key] = ""
    GPU_TYPES_KEY = "use_gputype"
    GPU_NOTYPES_KEY = "nouse_gputype"
    console.log("Checking current GPU stock...")
    generate_gpu_annotation(
        input_message="SELECT Target GPUs for the job (loading models)",
        values=values_dict,
        value_key=GPU_TYPES_KEY,
        annotation_key="nvidia.com/use-gputype"
    )
    generate_gpu_annotation(
        input_message="AVOID Target GPUs for the job (loading models)",
        values=values_dict,
        value_key=GPU_NOTYPES_KEY,
        annotation_key="nvidia.com/nouse-gputype"
    )

    result = deploy_job(
        template_name=template_name,
        values_dict=values_dict,
        force_namespace=force_namespace
    )

    if "error" in result:
        console.log(f"[red]Error when deploying job: {str(e)}")
    else:
        console.log(f"[green]{template_name} job deployed")

@arguably.command
def job__test(local_template_dir, *others, values, defaults, force_namespace: str=None):
    """
    Helper to test local templates, useful for development
    """
    try:
        CLUSTER.validate_cluster()
    except Exception as e:
        console.log(f"[red]Problems with your pool: {str(e)}")
        return
    
    if not os.path.isdir(local_template_dir):
        console.log(f"[red]--local_template_dir ({local_template_dir}) is not a directory")
        return
    
    # load template
    with open(os.path.join(local_template_dir, "template.yaml"), "r") as f:
        template_str = f.read()
    
    # load values
    if not os.path.isfile(values):
        console.log(f"[red]--values ({values}) is not a valid local file")
        return
    with open(values, "r") as f:
        raw_values = yaml.load(f, Loader=yaml.SafeLoader)
        values_dict = {variable["name"]: variable['value'] for variable in raw_values}

    # load defaults
    if not os.path.isfile(defaults):
        console.log(f"[red]--defaults ({defaults}) is not a valid local file")
        return
    with open(defaults, "r") as f:
        defaults = f.read()
    
    # submit custom deployment
    data = {
        "template": template_str,
        "template_values": values_dict,
        "default_values": defaults
    }
    if force_namespace is not None:
        data["force_namespace"] = force_namespace

    try:
        result = request_to_server(
            method="post",
            endpoint="/v1/deploy_custom_job",
            data=data,
            server_creds=USER_LOCAL_SERVER_FILE,
            user_cookie=USER_COOKIE
        )
        console.log("Deployment result:")
        print(
            json.dumps(result,indent=3)
        )
    except Exception as e:
        console.log(f"[red]Error when connecting to kalavai service: {str(e)}")


@arguably.command
def job__defaults(template_name, *others):
    """
    Fetch default values.yaml for a template job
    """
    try:
        CLUSTER.validate_cluster()
    except Exception as e:
        console.log(f"[red]Problems with your pool: {str(e)}")
        return
    
    # deploy template with kube-watcher
    defaults = fetch_job_defaults(name=template_name)
    if "error" in defaults:
        console.log(f"[red]Error when fetching job defaults: {defaults}")
    print(
        json.dumps(defaults, indent=3)
    )


@arguably.command
def job__delete(name, *others, force_namespace: str=None):
    """
    Delete job in the cluster
    """
    try:
        CLUSTER.validate_cluster()
    except Exception as e:
        console.log(f"[red]Problems with your pool: {str(e)}")
        return
    
    if force_namespace is not None:
        console.log("[WARNING][yellow]--force-namespace [white]requires an admin key. Request will fail if you are not an admin.")
    
    # deploy template with kube-watcher
    result = delete_job(name=name, force_namespace=force_namespace)
    if "error" in result:
        console.log(f"[red]Error when deleting job: {str(e)}")
    else:
        console.log(f"{result}")


@arguably.command
def job__estimate(billion_parameters, *others, precision=32):
    """Guesstimate of resources needed based on required memory and current resources"""
    try:
        CLUSTER.validate_cluster()
    except Exception as e:
        console.log(f"[red]Problems with your pool: {str(e)}")
        return
    
    average_vram = 8
    required_memory = float(billion_parameters) * (precision / 8) / 1.2
    available_gpus = load_gpu_models()
    vrams = []
    for _, gpus in available_gpus:
        for model in gpus["gpus"]:
            vrams.extend([int(model["memory"])/1000] * int(gpus["capacity"]) )
    vrams = sorted(vrams, reverse=False)

    console.log(f"There are {len(vrams)} GPUs available ({sum(vrams)}GBs)")
    console.log(f"A [yellow]{billion_parameters}B[white] model requires [yellow]~{required_memory:.2f}GB vRAM[white] at {precision}bits precision")

    if sum(vrams) < required_memory:
        console.log("Current capacity is insufficient to host the model, but it can be scheduled for when it is!")
        console.log(f"Average devices have {average_vram}GB vRAM, use {math.ceil(required_memory/(average_vram))} GPU workers")
    else:
        current_vram = 0
        n_devices = 0
        for mem in vrams:
            current_vram += mem
            n_devices += 1
            if current_vram > required_memory:
                break
        console.log(f"Looking at current capacity, use [green]{n_devices} GPU workers[white] for a total [green]{current_vram:.2f} GB vRAM")  

@arguably.command
def job__status(name, *others):

    try:
        # get pod statuses
        data = {
            "label": TEMPLATE_LABEL,
            "value": name
        }
        result = request_to_server(
            method="post",
            endpoint="/v1/get_pods_status_for_label",
            data=data,
            server_creds=USER_LOCAL_SERVER_FILE,
            user_cookie=USER_COOKIE
        )
        workers_status = defaultdict(int)
        workers_conditions = {}
        for _, ss in result.items():
            for pod_name, values in ss.items():
                workers_status[values["status"]] += 1
                workers_conditions[pod_name] = values["conditions"]
        workers = "\n".join([f"{k}: {v}" for k, v in workers_status.items()])
        
        console.log("Workers conditions")
        for worker, conditions in workers_conditions.items():
            console.log(f"[yellow]{worker}")
            console.log(conditions)
        console.log(f"[yellow]{workers}\nTotal: {len(workers_status)}")
    except Exception as e:
        console.log(f"[red]Error when connecting to kalavai service: {str(e)}")
        return

@arguably.command
def job__list(*others):
    """
    List jobs in the cluster
    """
    try:
        CLUSTER.validate_cluster()
    except Exception as e:
        console.log(f"[red]Problems with your pool: {str(e)}")
        return

    all_deployments = fetch_job_names()
    if "error" in all_deployments:
        console.log(f"[red]Error when connecting to kalavai service: {all_deployments}")
        return 
    
    if len(all_deployments) == 0:
        console.log("[green]No deployments found.")
        return
    
    details = fetch_job_details(jobs=all_deployments)
    if "error" in details:
        console.log(f"[red]{details}")
        return
    columns = ["Owner", "Deployment", "Workers", "Endpoint"]
    rows = [[job.owner, job.name, job.workers, job.endpoint] for job in details]
    
    console.print(
        generate_table(columns=columns, rows=rows, end_sections=range(len(rows)))
    )
        
    console.log("Check detailed status with [yellow]kalavai job status <name of deployment>")
    console.log("Get logs with [yellow]kalavai job logs <name of deployment> [white](note it only works when the deployment is complete)")


@arguably.command
def job__logs(name, *others, pod_name=None, stream=False, tail=100, force_namespace: str=None):
    """
    Get logs for a specific job
    """
    try:
        CLUSTER.validate_cluster()
    except Exception as e:
        console.log(f"[red]Problems with your pool: {str(e)}")
        return
    
    if force_namespace is not None:
        console.log("[WARNING][yellow]--force-namespace [white]requires an admin key. Request will fail if you are not an admin.")

    all_logs = fetch_job_logs(
        job_name=name,
        pod_name=pod_name,
        force_namespace=force_namespace,
        tail=tail)
    if "error" in all_logs:
        console.log(f"[red]{all_logs}")
        return
    while True:
        try:
            if not stream:
                for pod, logs in all_logs.items():
                    if pod_name is not None and pod_name != pod:
                        continue
                    console.log(f"[yellow]Pod {pod}")
                    console.log(f"[green]{logs}")
                break
            else:
                os.system("clear")
                for pod, logs in all_logs.items():
                    if pod_name is not None and pod_name != pod:
                        continue
                    print(f"Pod {pod}")
                    print(f"{logs}")
                time.sleep(1)
        except KeyboardInterrupt:
            break


@arguably.command
def job__manifest(*others, name, force_namespace: str=None):
    """
    Get job manifest description
    """
    try:
        CLUSTER.validate_cluster()
    except Exception as e:
        console.log(f"[red]Problems with your pool: {str(e)}")
        return
    
    if force_namespace is not None:
        console.log("[WARNING][yellow]--force-namespace [white]requires an admin key. Request will fail if you are not an admin.")
    
    data = {
        "label": TEMPLATE_LABEL,
        "value": name,
    }
    if force_namespace is not None:
        data["force_namespace"] = force_namespace
    try:
        result = request_to_server(
            method="post",
            endpoint="/v1/describe_pods_for_label",
            data=data,
            server_creds=USER_LOCAL_SERVER_FILE,
            user_cookie=USER_COOKIE
        )
        for pod, manifest in result.items():
            manifest = json.dumps(manifest, indent=3)
            console.log(f"[yellow]Pod {pod}")
            console.log(f"{manifest}")
    except Exception as e:
        console.log(f"[red]Error when connecting to kalavai service: {str(e)}")
        return 


@arguably.command
def ray__create(name, template_path, *others, force_namespace: str=None):
    """
    Create a cluster using KubeRay operator
    """

    try:
        CLUSTER.validate_cluster()
    except Exception as e:
        console.log(f"[red]Problems with your pool: {str(e)}")
        return
    
    with open(template_path, "r") as f:
        template_yaml = f.read()
        
    data = {
        "name": name,
        "manifest": template_yaml
    }
    if force_namespace is not None:
        data["force_namespace"] = force_namespace
    try:
        result = request_to_server(
            method="post",
            endpoint="/v1/deploy_ray",
            data=data,
            server_creds=USER_LOCAL_SERVER_FILE,
            user_cookie=USER_COOKIE
        )
        if len(result['failed']) > 0:
            console.log(f"[red]Error when deploying ray manifest\n\n{result['failed']}")
            return
        if len(result['successful']) > 0:
            console.log(f"[green]Ray cluster {name} successfully deployed!")
    except Exception as e:
        console.log(f"[red]Error when connecting to kalavai service: {str(e)}")
        return


@arguably.command
def ray__list(*status):
    """
    List all available ray clusters
    """
    try:
        CLUSTER.validate_cluster()
    except Exception as e:
        console.log(f"[red]Problems with your pool: {str(e)}")
        return

    data = {
        "group": "ray.io",
        "api_version": "v1",
        "plural": "rayclusters"
    }
    try:
        result = request_to_server(
            method="post",
            endpoint="/v1/get_objects_of_type",
            data=data,
            server_creds=USER_LOCAL_SERVER_FILE,
            user_cookie=USER_COOKIE
        )
        clusters = {ns: ds["items"] for ns, ds in result.items()}
        #clusters = result['items']

    except Exception as e:
        console.log(f"[red]Error when connecting to kalavai service: {str(e)}")
        return

    if len(clusters) == 0:
        console.log("No clusters available")
        return
    
    # pretty print
    columns = ["Owner", "Name", "Status", "CPUs", "GPUs", "Memory", "Endpoints"]
    rows = []
    server_ip = load_server_info(data_key=SERVER_IP_KEY, file=USER_LOCAL_SERVER_FILE)
    for namespace, clusters in clusters.items():
        for cluster in clusters:
            cluster_name = cluster['metadata']['name']
            cpus = cluster["status"]["desiredCPU"]
            gpus = cluster["status"]["desiredGPU"]
            memory = cluster["status"]["desiredMemory"]
            min_workers = cluster["status"]["minWorkerReplicas"] if "minWorkerReplicas" in cluster["status"] else 0
            max_workers = cluster["status"]["maxWorkerReplicas"] if "maxWorkerReplicas" in cluster["status"] else 0
            ready_workers = cluster["status"]["readyWorkerReplicas"] if "readyWorkerReplicas" in cluster["status"] else 0
            head_status = cluster["status"]["state"] if "state" in cluster["status"] else "creating"
            status = f"Head {head_status}\nWorkers: {ready_workers} ready ({min_workers}/{max_workers})"
            endpoints = [f"{k}: http://{server_ip}:{v}" for k, v in cluster['status']["endpoints"].items()]
            rows.append(
                (namespace, cluster_name, status, cpus, gpus, memory, "\n".join(endpoints))
            )
    table = generate_table(columns=columns, rows=rows)
    console.log(table)

@arguably.command
def ray__delete(*others, name, force_namespace=None):
    """
    Delete a ray cluster
    """
    try:
        CLUSTER.validate_cluster()
    except Exception as e:
        console.log(f"[red]Problems with your pool: {str(e)}")
        return

    # deploy template with kube-watcher
    data = {
        "label": RAY_LABEL, # this ensures that both raycluster and services are deleted
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
def ray__manifest(*others, name, force_namespace=None):
    """
    Get ray cluster manifest description
    """
    try:
        CLUSTER.validate_cluster()
    except Exception as e:
        console.log(f"[red]Problems with your pool: {str(e)}")
        return
    
    data = {
        "label": "ray.io/cluster",
        "value": name
    }
    if force_namespace is not None:
        data["force_namespace"] = force_namespace
    try:
        result = request_to_server(
            method="post",
            endpoint="/v1/describe_pods_for_label",
            data=data,
            server_creds=USER_LOCAL_SERVER_FILE,
            user_cookie=USER_COOKIE
        )
        for pod, manifest in result.items():
            manifest = json.dumps(manifest, indent=3)
            console.log(f"[yellow]Pod {pod}")
            console.log(f"{manifest}")
    except Exception as e:
        console.log(f"[red]Error when connecting to kalavai service: {str(e)}")
        return


def app():
    user_path("", create_path=True)
    arguably.run()

if __name__ == "__main__":
    app()