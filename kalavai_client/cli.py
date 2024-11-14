from collections import defaultdict
import math
import os
import json
import uuid
from string import Template
import time
import socket
from pathlib import Path
from getpass import getpass
import ipaddress

import yaml
import netifaces as ni
import arguably
from rich.console import Console

from kalavai_client.utils import (
    user_path,
    decode_dict,
    generate_join_token,
    user_confirm,
    load_template,
    store_server_info,
    generate_table,
    request_to_server,
    get_all_templates,
    is_service_running,
    resource_path,
    user_path,
    safe_remove,
    join_vpn,
    leave_vpn,
    load_server_info,
    user_login,
    user_logout,
    get_public_vpns,
    register_cluster,
    unregister_cluster,
    get_public_seeds,
    validate_join_public_seed,
    is_storage_compatible,
    is_watcher_alive,
    SERVER_IP_KEY,
    AUTH_KEY,
    WATCHER_SERVICE_KEY,
    READONLY_KEY,
    PUBLIC_LOCATION_KEY,
    NODE_NAME_KEY,
    CLUSTER_NAME_KEY,
    CLUSTER_IP_KEY,
    CLUSTER_TOKEN_KEY,
    WATCHER_PORT_KEY,
    MANDATORY_TOKEN_FIELDS,
    USER_NODE_LABEL_KEY,
    DEPLOY_HELIOS_KEY,
    LONGHORN_UI_PORT_KEY
)
from kalavai_client.cluster import (
    k3sCluster
)


KALAVAI_PLATFORM_URL = os.getenv("KALAVAI_PLATFORM_URL", "https://platform.kalavai.net")
LOCAL_TEMPLATES_DIR = os.getenv("LOCAL_TEMPLATES_DIR", None)
VERSION = 1
RESOURCE_EXCLUDE = ["ephemeral-storage", "hugepages-1Gi", "hugepages-2Mi", "pods"]
CORE_NAMESPACES = ["lws-system", "kube-system", "gpu-operator", "kalavai"]
TEMPLATE_LABEL = "kalavai.lws.name"
RAY_LABEL = "kalavai.ray.name"
PVC_NAME_LABEL = "kalavai.storage.name"
STORAGE_CLASS_NAME = "longhorn-rwx"
STORAGE_CLASS_LABEL = "kalavai.storage.enabled"
DEFAULT_STORAGE_NAME = "pool-cache"
DEFAULT_STORAGE_SIZE = 5
DEFAULT_STORAGE_REPLICAS = 1
USER_NODE_LABEL = "kalavai.cluster.user"
KUBE_VERSION = os.getenv("KALAVAI_KUBE_VERSION", "v1.31.1+k3s1")
DEFAULT_FLANNEL_IFACE = os.getenv("KALAVAI_FLANNEL_IFACE", "netmaker")
FORBIDEDEN_IPS = ["127.0.0.1"]
# kalavai templates
HELM_APPS_FILE = resource_path("assets/apps.yaml")
SERVICE_TEMPLATE_FILE = resource_path("assets/service_template.yaml")
STORAGE_TEMPLATE_FILE = resource_path("assets/pvc_template.yaml")
STORAGE_CLASS_TEMPLATE_FILE = resource_path("assets/storage_class_template.yaml")
# user specific config files
USER_HELM_APPS_FILE = user_path("apps.yaml")
USER_KUBECONFIG_FILE = user_path("kubeconfig")
USER_LOCAL_SERVER_FILE = user_path(".server")
USER_TEMPLATES_FOLDER = user_path("templates", create_path=True)
USER_COOKIE = user_path(".user_cookie.pkl")


console = Console()
CLUSTER = k3sCluster(
    kube_version=KUBE_VERSION,
    flannel_iface=DEFAULT_FLANNEL_IFACE,
    kubeconfig_file=USER_KUBECONFIG_FILE,
    poolconfig_file=USER_LOCAL_SERVER_FILE,
    dependencies_file=USER_HELM_APPS_FILE
)


######################
## HELPER FUNCTIONS ##
######################

def cleanup_local():
    # disconnect from private network
    try:
        vpns = leave_vpn()
        if vpns is not None:
            for vpn in vpns:
                console.log(f"You have left {vpn} VPN")
    except:
        # no vpn
        pass
    safe_remove(USER_KUBECONFIG_FILE)
    safe_remove(USER_LOCAL_SERVER_FILE)

def fetch_remote_templates():
    templates = get_all_templates(
        local_path=USER_TEMPLATES_FOLDER,
        templates_path=LOCAL_TEMPLATES_DIR,
        remote_load=True)
    return templates

def pre_join_check(node_name, server_url, server_key):
    # check with the server that we can connect
    try:
        nodes = request_to_server(
            force_url=server_url,
            force_key=server_key,
            method="get",
            endpoint="/v1/get_nodes",
            data={"node_names": [node_name]},
            server_creds=USER_LOCAL_SERVER_FILE
        )
        return node_name not in nodes.keys()
    except Exception as e:
        console.log(f"[red]Error when connecting to kalavai service: {str(e)}")
        return False

def restart():
    console.log("[white] Restarting sharing (may take a few minutes)...")
    success = CLUSTER.restart_agent()
    if success:
        console.log("[white] Kalava sharing resumed")
        fetch_remote_templates()
    else:
        console.log("[red] Error when restarting. Please run [yellow]kalavai pool resume[white] again.")

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
            server_creds=USER_LOCAL_SERVER_FILE
        )
        console.log(f"{res}")
    except Exception as e:
        console.log(f"[red]Error when connecting to kalavai service: {str(e)}")

def select_ip_address(subnet=None):
    ips = []
    for iface in ni.interfaces():
        try:
            ip = ni.ifaddresses(iface)[ni.AF_INET][0]['addr']
            if ip in FORBIDEDEN_IPS:
                continue
            if subnet is None or ipaddress.ip_address(ip) in ipaddress.ip_network(subnet):
                ips.append(ip)
        except:
            pass
    if len(ips) == 1:
        return ips[0]
    if len(ips) == 0:
        raise ValueError("No IPs available")
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

def deploy_templated_yaml(template_file, template_values):
    sidecar_template_yaml = load_template(
        template_path=template_file,
        values=template_values
    )
    try:
        result = request_to_server(
            method="post",
            endpoint="/v1/deploy_generic_model",
            data={"config": sidecar_template_yaml},
            server_creds=USER_LOCAL_SERVER_FILE
        )
        if len(result['failed']) > 0:
            console.log(f"[red]Error when creating {template_file}\n\n{result['failed']}")
        if len(result['successful']) > 0:
            console.log(f"[green]Created {template_file}")
    except Exception as e:
        console.log(f"[red]Error when connecting to kalavai service: {str(e)}")


##################
## CLI COMMANDS ##
##################

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
        CLUSTER.validate_cluster()
    except Exception as e:
        console.log(f"[red]Problems with your pool: {str(e)}")
        return
    
    if description is None:
        console.log("[yellow] [Markdown] In a few words (max 500 chars), describe your goals with this cluster. Remember, this is what other users will see to decide whether to share their resources with you, [blue]so inspire them!")
        description = input(f"(You can edit this later in {KALAVAI_PLATFORM_URL}\n")
    
    description = description
    
    try:
        token = pool__token()
        if not pool__check_token(token=token, public=True):
            raise ValueError("[red]Cluster must be started with a valid vpn_location to publish")
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
        CLUSTER.validate_cluster()
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
def pool__start(cluster_name, *others,  ip_address: str=None, location: str=None, default_storage_name: str=DEFAULT_STORAGE_NAME, default_storage_size: int=DEFAULT_STORAGE_SIZE):
    """
    Start Kalavai pool and start/resume sharing resources.

    Args:
        *others: all the other positional arguments go here
    """

    if CLUSTER.is_cluster_init():
        console.log(f"[white] You are already connected to {load_server_info(data_key=CLUSTER_NAME_KEY, file=USER_LOCAL_SERVER_FILE)}. Enter [yellow]kalavai pool stop[white] to exit and join another one.")
        return

    # join private network if provided
    subnet = None
    node_labels = {
        STORAGE_CLASS_LABEL: is_storage_compatible()
    }
    if location is not None:
        console.log("Joining private network")
        try:
            vpn = join_vpn(
                location=location,
                user_cookie=USER_COOKIE)
            subnet = vpn["subnet"]
            user = user_login(user_cookie=USER_COOKIE)
            node_labels = {USER_NODE_LABEL: user["username"]}
            time.sleep(5)
        except Exception as e:
            console.log(f"[red]Error when joining network: {str(e)}")
            return

    if ip_address is None:
        console.log("Scanning for valid IPs...")
        ip_address = select_ip_address(subnet=subnet)
    console.log(f"Using {ip_address} address for server")

    auth_key = str(uuid.uuid4())
    readonly_key = str(uuid.uuid4())
    watcher_port = 31000
    longhorn_port = 30000
    watcher_service = f"{ip_address}:{watcher_port}"
    values = {
        CLUSTER_NAME_KEY: cluster_name,
        CLUSTER_IP_KEY: ip_address,
        AUTH_KEY: auth_key,
        READONLY_KEY: readonly_key,
        WATCHER_PORT_KEY: watcher_port,
        LONGHORN_UI_PORT_KEY: longhorn_port,
        WATCHER_SERVICE_KEY: watcher_service,
        USER_NODE_LABEL_KEY: USER_NODE_LABEL,
        DEPLOY_HELIOS_KEY: location is not None
    }
    
    # 1. start k3s server
    console.log("Installing cluster seed")
    CLUSTER.start_seed_node(
        ip_address=ip_address,
        labels=node_labels,
        is_public=location is not None)
    
    store_server_info(
        server_ip=ip_address,
        auth_key=auth_key,
        readonly_key=readonly_key,
        file=USER_LOCAL_SERVER_FILE,
        watcher_service=watcher_service,
        node_name=socket.gethostname(),
        cluster_name=cluster_name,
        public_location=location)
    
    while not CLUSTER.is_agent_running():
        console.log("Waiting for seed to start...")
        time.sleep(10)
    
    console.log("Install dependencies...")
    # set template values in helmfile
    with open(HELM_APPS_FILE, "r") as f:
        config = Template(f.read())
        config = config.substitute(values)
    
    with open(USER_HELM_APPS_FILE, "w") as f:
        f.write(config)
    CLUSTER.update_dependencies(
        dependencies_file=USER_HELM_APPS_FILE
    )
    
    fetch_remote_templates()
    console.log("[green]Your cluster is ready! Grow your cluster by sharing your joining token with others. Run [yellow]kalavai pool token[green] to generate one.")

    if location is not None:
        # register with kalavai if it's a public cluster
        console.log("Registering public cluster with Kalavai...")
        pool__publish()
    
    # create default local storage
    while True:
        # wait until the server is ready to create objects
        console.log("Waiting for core services to be ready, may take a few minutes...")
        time.sleep(30)
        if is_watcher_alive(server_creds=USER_LOCAL_SERVER_FILE):
            break
    console.log(f"Initialising storage: {DEFAULT_STORAGE_NAME} ({DEFAULT_STORAGE_SIZE}Gi)...")  
    storage__init()
    storage__create()

    return None

@arguably.command
def pool__token(*others, admin_workers=False):
    """
    Generate a join token for others to connect to your pool
    """
    try:
        CLUSTER.validate_cluster()
    except Exception as e:
        console.log(f"[red]Problems with your pool: {str(e)}")
        return
    
    if not CLUSTER.is_seed_node():
        console.log("[red]Node is not seed. Possible reasons: this is a worker node.")
        return None
    
    if admin_workers:
        auth_key = load_server_info(data_key=AUTH_KEY, file=USER_LOCAL_SERVER_FILE)
    else:
        auth_key = load_server_info(data_key=READONLY_KEY, file=USER_LOCAL_SERVER_FILE)
    watcher_service = load_server_info(data_key=WATCHER_SERVICE_KEY, file=USER_LOCAL_SERVER_FILE)
    public_location = load_server_info(data_key=PUBLIC_LOCATION_KEY, file=USER_LOCAL_SERVER_FILE)

    cluster_token = CLUSTER.get_cluster_token()

    ip_address = load_server_info(SERVER_IP_KEY, file=USER_LOCAL_SERVER_FILE)
    cluster_name = load_server_info(data_key=CLUSTER_NAME_KEY, file=USER_LOCAL_SERVER_FILE)

    join_token = generate_join_token(
        cluster_ip=ip_address,
        cluster_name=cluster_name,
        cluster_token=cluster_token,
        auth_key=auth_key,
        watcher_service=watcher_service,
        public_location=public_location
    )

    console.log("[green]Join token:")
    print(join_token)

    return join_token

@arguably.command
def pool__check_token(token, *others, public=False):
    """
    Utility to check the validity of a join token
    """
    try:
        data = decode_dict(token)
        for field in MANDATORY_TOKEN_FIELDS:
            assert field in data
        if public:
            if data[PUBLIC_LOCATION_KEY] is None:
                raise ValueError("Token is not valid for public pools. Did you start the cluster with a public_location?")
        console.log("[green]Token format is correct")
        return True
    except Exception as e:
        console.log(f"[white]{str(e)}")
        console.log("[red]Token is invalid.")
        return False


@arguably.command
def pool__join(token, *others, node_name=None, ip_address: str=None):
    """
    Join Kalavai pool and start/resume sharing resources.

    Args:
        *others: all the other positional arguments go here
    """
    if node_name is None:
        node_name = socket.gethostname()
    
    # check token
    if not pool__check_token(token):
        return
    
    # check that k3s is not running already in the host
    # k3s service running or preinstalled
    if CLUSTER.is_agent_running():
        console.log(f"[white] You are already connected to {load_server_info(data_key=CLUSTER_NAME_KEY, file=USER_LOCAL_SERVER_FILE)}. Enter [yellow]kalavai pool stop[white] to exit and join another one.")
        return

    try:
        data = decode_dict(token)
        kalavai_seed_ip = data[CLUSTER_IP_KEY]
        kalavai_token = data[CLUSTER_TOKEN_KEY]
        cluster_name = data[CLUSTER_NAME_KEY]
        auth_key = data[AUTH_KEY]
        watcher_service = data[WATCHER_SERVICE_KEY]
        public_location = data[PUBLIC_LOCATION_KEY]
        subnet = None
    except Exception as e:
        console.log(str(e))
        console.log("[red] Invalid token")
        return
    
    # join private network if provided
    node_labels = {
        STORAGE_CLASS_LABEL: is_storage_compatible()
    }
    if public_location is not None:
        console.log("Joining private network")
        try:
            vpn = join_vpn(
                location=public_location,
                user_cookie=USER_COOKIE)
            subnet = vpn["subnet"]
            user = user_login(user_cookie=USER_COOKIE)
            node_labels = {USER_NODE_LABEL: user["username"]}
            time.sleep(5)
        except Exception as e:
            console.log(f"[red]Error when joining network: {str(e)}")
            console.log("Are you authenticated? Try [yellow]kalavai login")
            return
        # validate public seed
        try:
            validate_join_public_seed(
                cluster_name=cluster_name,
                join_key=token,
                user_cookie=USER_COOKIE
            )
        except Exception as e:
            console.log(f"[red]Error when joining network: {str(e)}")
            leave_vpn()
            return

    # send note to server to let them know the node is coming online
    if not pre_join_check(node_name=node_name, server_url=watcher_service, server_key=auth_key):
        console.log(f"[red] Failed pre join checks. Server offline or node '{node_name}' may already exist. Please specify a different one with '--node-name'")
        leave_vpn()
        return

    if ip_address is None:
        console.log("Scanning for valid IPs...")
        ip_address = select_ip_address(subnet=subnet)
    console.log(f"Using {ip_address} address for worker")
    
    # local k3s agent join
    console.log(f"[white] Connecting to {cluster_name} @ {kalavai_seed_ip} (this may take a few minutes)...")
    try:
        CLUSTER.start_worker_node(
            url=kalavai_seed_ip,
            token=kalavai_token,
            node_name=node_name,
            ip_address=ip_address,
            labels=node_labels,
            is_public=public_location is not None)
    except Exception as e:
        console.log(f"[red] Error connecting to {cluster_name} @ {kalavai_seed_ip}. Check with the admin if the token is still valid.")
        leave_vpn()
        exit()

    while not CLUSTER.is_agent_running():
        console.log("Waiting for worker to start...")
        time.sleep(10)
    store_server_info(
        server_ip=kalavai_seed_ip,
        auth_key=auth_key,
        file=USER_LOCAL_SERVER_FILE,
        watcher_service=watcher_service,
        node_name=node_name,
        cluster_name=cluster_name,
        public_location=public_location)
    fetch_remote_templates()
    
    # set status to schedulable
    time.sleep(10)
    set_schedulable(schedulable=True)
    console.log(f"[green] You are connected to {cluster_name}")

@arguably.command
def pool__stop(*others):
    """
    Stop sharing your device and clean up. DO THIS ONLY IF YOU WANT TO REMOVE KALAVAI-CLIENT from your device.

    Args:
        *others: all the other positional arguments go here
    """
    console.log("[white] Stopping kalavai app...")
    # delete local node from server
    node__delete(load_server_info(data_key=NODE_NAME_KEY, file=USER_LOCAL_SERVER_FILE))
    # unpublish event (only if seed node)
    try:
        if CLUSTER.is_seed_node():
            unregister_cluster(
                name=load_server_info(data_key=CLUSTER_NAME_KEY, file=USER_LOCAL_SERVER_FILE),
                user_cookie=USER_COOKIE)
    except Exception as e:
        console.log(f"[red][WARNING]: (ignore if not a public pool) Error when unpublishing cluster. {str(e)}")
    # remove local node agent
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
    success = CLUSTER.pause_agent()
    if success:
        console.log("[white] Kalava sharing paused. Resume with [yellow]kalavai pool resume")
    else:
        console.log("[red] Error when stopping. Please run [yellow]kalavai pool pause[red] again.")

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
    console.log("[white] Resuming kalavai app...")
    restart()

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

    try:
        data = request_to_server(
            method="post",
            endpoint="/v1/get_node_gpus",
            data={},
            server_creds=USER_LOCAL_SERVER_FILE
        )
        columns, rows = [], []
        for node, gpus in data.items():
            row_gpus = []
            for gpu in gpus:
                status = gpu["ready"] if "ready" in gpu else True
                if available and not status:
                    continue
                row_gpus.append( (f"{gpu['model']} ({math.floor(int(gpu['memory'])/1000)} GBs)", str(status)))
            if len(row_gpus) > 0:
                models, statuses = zip(*row_gpus)
                rows.append([node, str(len(row_gpus)), "\n".join(models), "\n".join(statuses)])

            columns = ["Quantity", "GPU(s)", "Ready"]
        columns = ["Node"] + columns
        console.print(
            generate_table(columns=columns, rows=rows,end_sections=[n for n in range(len(rows))])
        )
        
    except Exception as e:
        console.log(f"[red]Error when connecting to kalavai service: {str(e)}")


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

    try:
        total = request_to_server(
            method="get",
            endpoint="/v1/get_cluster_total_resources",
            data={},
            server_creds=USER_LOCAL_SERVER_FILE
        )
        available = request_to_server(
            method="get",
            endpoint="/v1/get_cluster_available_resources",
            data={},
            server_creds=USER_LOCAL_SERVER_FILE
        )
        columns = []
        total_values = []
        available_values = []
        for col in total.keys():
            if col in RESOURCE_EXCLUDE:
                continue
            columns.append(col)
            total_values.append(str(total[col]))
            available_values.append(str(available[col]))
        
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
        
    except Exception as e:
        console.log(f"[red]Error when connecting to kalavai service: {str(e)}")

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
def pool__status(*others):
    """
    Check the status of the kalavai pool
    """
    try:
        CLUSTER.validate_cluster()
    except Exception as e:
        console.log(f"[red]Problems with your pool: {str(e)}")
        return

    try:
        response = request_to_server(
            method="POST",
            endpoint="/v1/get_deployments",
            data={"namespaces": CORE_NAMESPACES},
            server_creds=USER_LOCAL_SERVER_FILE
        )
        global_status = True
        for _, deployments in response.items():
            for key, values in deployments.items():
                state = values["available_replicas"] == values["ready_replicas"]
                console.log(f"{key} status: {state}")
                global_status &= state
        console.log("---------------------------------")
        console.log(f"--> Pool status: {global_status}")
    except Exception as e:
        console.log(f"[red]Error when connecting to kalavai service: {str(e)}")


@arguably.command
def pool__diagnostics(*others, log_file=None):
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
    logs.append(f"App installed: {CLUSTER.is_cluster_init()}")

    logs.append(f"Agent running: {CLUSTER.is_agent_running()}")

    logs.append(f"Containerd running: {is_service_running(service='containerd.service')}")
    
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
def storage__init(replicas=DEFAULT_STORAGE_REPLICAS, *others):
    """
    Create storage for the cluster
    """
    try:
        CLUSTER.validate_cluster()
    except Exception as e:
        console.log(f"[red]Problems with your pool: {str(e)}")
        return

    # Ensure storage class exists
    deploy_templated_yaml(
        template_file=STORAGE_CLASS_TEMPLATE_FILE,
        template_values={
            "sc_name": STORAGE_CLASS_NAME,
            "sc_label_selector": f"{STORAGE_CLASS_LABEL}:True",
            "sc_replicas": replicas
        }
    )

@arguably.command
def storage__create(name=DEFAULT_STORAGE_NAME, storage=DEFAULT_STORAGE_SIZE, *others):
    """
    Create storage for the cluster
    """
    try:
        CLUSTER.validate_cluster()
    except Exception as e:
        console.log(f"[red]Problems with your pool: {str(e)}")
        return

    # Deploy PVC
    deploy_templated_yaml(
        template_file=STORAGE_TEMPLATE_FILE,
        template_values={
            "pvc_name": name,
            "storage": f"{storage}Gi",
            "storage_class_name": STORAGE_CLASS_NAME,
            "pvc_name_label": PVC_NAME_LABEL
        }
    )

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
    
    data = {
        "label": "kalavai.resource",
        "value": "storage",
        "namespace": "default"
    }
    try:
        result = request_to_server(
            method="post",
            endpoint="/v1/get_resources_with_label",
            data=data,
            server_creds=USER_LOCAL_SERVER_FILE
        )
        for resource, items in result.items():
            console.log(f"[yellow]{resource}s available in the pool")
            for name, values in items.items():
                console.log(f"\t{name} ({values['creation_timestamp']})")
    except Exception as e:
        console.log(f"[red]Error when connecting to kalavai service: {str(e)}")
    
@arguably.command
def storage__delete(name, *others):
    """
    Delete storage by name
    """
    # deploy template with kube-watcher
    data = {
        "namespace": "default",
        "label": PVC_NAME_LABEL,
        "value": name
    }
    try:
        result = request_to_server(
            method="post",
            endpoint="/v1/delete_labeled_resources",
            data=data,
            server_creds=USER_LOCAL_SERVER_FILE
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
        data = request_to_server(
            method="get",
            endpoint="/v1/get_nodes",
            data={},
            server_creds=USER_LOCAL_SERVER_FILE
        )
        rows = []
        columns = ["Node name"]
        for node, status in data.items():
            row = [node]
            for key, value in status.items():
                if key not in columns:
                    columns.append(key)
                row.append(str(value))
            rows.append(tuple(row))
        
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
    
    data = {
        "node_names": [name]
    }
    try:
        result = request_to_server(
            method="post",
            endpoint="/v1/delete_nodes",
            data=data,
            server_creds=USER_LOCAL_SERVER_FILE
        )
        if result is None or result is True:
            console.log(f"Node {name} deleted successfully")
        else:
            console.log(f"{result}")
    except Exception as e:
        console.log(f"[yellow](ignore if stopping worker from dead server). Error when removing node {name}: {str(e)}")


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
    templates = get_all_templates(
        local_path=USER_TEMPLATES_FOLDER,
        templates_path=LOCAL_TEMPLATES_DIR)
    
    console.log("[green]Available templates:")
    for _, template in templates:
        console.log(f"[green]{template}")


@arguably.command
def job__reload(*others):
    """
    Refreshes template collection from remote repository. Run when you want to update your local collection.
    """
    templates = fetch_remote_templates()
    
    console.log(f"[green] {len(templates)} templates loaded remotely")
    job__templates()



@arguably.command
def job__run(template_name, *others, values=None):
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

    expose = True

    paths, available_templates = zip(*get_all_templates(
        local_path=USER_TEMPLATES_FOLDER,
        templates_path=LOCAL_TEMPLATES_DIR)
    )
    
    if template_name not in available_templates:
        console.log(f"[red]{template_name} not found")
        job__templates()
        return
    
    path = paths[available_templates.index(template_name)]
    template_path = os.path.join(path, template_name, "template.yaml")

    if values is None or not Path(values).is_file():
        console.log(f"[red]Values file {values} was not found")

    with open(values, "r") as f:
        raw_values = yaml.load(f, Loader=yaml.SafeLoader)
        values_dict = {variable["name"]: variable['value'] for variable in raw_values["template_values"]}
    
    template_yaml = load_template(
        template_path=template_path,
        values=values_dict)

    # deploy template with kube-watcher
    data = {
        "object": {
            "group": "leaderworkerset.x-k8s.io",
            "api_version": "v1",
            "namespace": "default",
            "plural": "leaderworkersets"
        },
        "body": template_yaml
    }
    try:
        result = request_to_server(
            method="post",
            endpoint="/v1/deploy_custom_object",
            data=data,
            server_creds=USER_LOCAL_SERVER_FILE
        )
        if len(result['failed']) > 0:
            console.log(f"[red]Error when deploying template\n\n{result['failed']}")
            return
        if len(result['successful']) > 0:
            console.log(f"[green]Template {template_path} successfully deployed!")
    except Exception as e:
        console.log(f"[red]Error when connecting to kalavai service: {str(e)}")
        return
    
    # expose lws with nodeport template if required
    if expose:
        deploy_templated_yaml(
            template_file=SERVICE_TEMPLATE_FILE,
            template_values=values_dict
        )

@arguably.command
def job__defaults(template_name, *others):
    """
    Fetch default values.yaml for a template job
    """
    paths, available_templates = zip(*get_all_templates(
        local_path=USER_TEMPLATES_FOLDER,
        templates_path=LOCAL_TEMPLATES_DIR)
    )
    
    if template_name not in available_templates:
        console.log(f"[red]{template_name} not found")
        job__templates()
        return
    
    path = paths[available_templates.index(template_name)]
    values_path = os.path.join(path, template_name, "values.yaml")

    with open(values_path, "r") as f:
        print("".join(f.readlines()))


@arguably.command
def job__describe(template_name, *others):
    """
    Fetch documentation for a template job
    """
    paths, available_templates = zip(*get_all_templates(
        local_path=USER_TEMPLATES_FOLDER,
        templates_path=LOCAL_TEMPLATES_DIR)
    )
    
    if template_name not in available_templates:
        console.log(f"[red]{template_name} not found")
        job__templates()
        return
    
    path = paths[available_templates.index(template_name)]
    values_path = os.path.join(path, template_name, "README.md")

    with open(values_path, "r") as f:
        print("".join(f.readlines()))


@arguably.command
def job__delete(name, *others):
    """
    Delete job in the cluster
    """
    try:
        CLUSTER.validate_cluster()
    except Exception as e:
        console.log(f"[red]Problems with your pool: {str(e)}")
        return

    # deploy template with kube-watcher
    data = {
        "namespace": "default",
        "label": TEMPLATE_LABEL, # this ensures that both lws template and services are deleted
        "value": name
    }
    try:
        result = request_to_server(
            method="post",
            endpoint="/v1/delete_labeled_resources",
            data=data,
            server_creds=USER_LOCAL_SERVER_FILE
        )
        console.log(f"{result}")
    except Exception as e:
        console.log(f"[red]Error when connecting to kalavai service: {str(e)}")


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

    data = {
        "group": "leaderworkerset.x-k8s.io",
        "api_version": "v1",
        "plural": "leaderworkersets",
        "namespace": ""
    }
    try:
        result = request_to_server(
            method="post",
            endpoint="/v1/get_objects_of_type",
            data=data,
            server_creds=USER_LOCAL_SERVER_FILE
        )
        deployment_names = [d["metadata"]["name"] for d in result["items"]]

    except Exception as e:
        console.log(f"[red]Error when connecting to kalavai service: {str(e)}")
        return
    
    if len(deployment_names) == 0:
        console.log("[green]No deployments found.")
        return
    
    columns = ["Deployment", "Status", "Workers", "Endpoint"]
    rows = []
    for deployment in deployment_names:
        try:
            # get status for deployment
            data = {
                "group": "leaderworkerset.x-k8s.io",
                "api_version": "v1",
                "plural": "leaderworkersets",
                "namespace": "default",
                "name": deployment
            }
            result = request_to_server(
                method="post",
                endpoint="/v1/get_status_for_object",
                data=data,
                server_creds=USER_LOCAL_SERVER_FILE
            )
            if len(result) > 0:
                last = result[-1]
                statuses = f"{last['type']}: {last['message']}"
            else:
                statuses = "Unknown"
            # get pod statuses
            data = {
                "namespace": "default",
                "label": "leaderworkerset.sigs.k8s.io/name",
                "value": deployment
            }
            result = request_to_server(
                method="post",
                endpoint="/v1/get_pods_status_for_label",
                data=data,
                server_creds=USER_LOCAL_SERVER_FILE
            )
            workers = defaultdict(int)
            for _, status in result.items():
                workers[status] += 1
            workers = "\n".join([f"{k}: {v}" for k, v in workers.items()])
            # get URL details
            data = {
                "label": TEMPLATE_LABEL,
                "value": deployment,
                "types": ["NodePort"]
            }
            result = request_to_server(
                method="post",
                endpoint="/v1/get_ports_for_services",
                data=data,
                server_creds=USER_LOCAL_SERVER_FILE
            )
            node_ports = [p["node_port"] for s in result.values() for p in s["ports"]]

            urls = [f"http://{load_server_info(data_key=SERVER_IP_KEY, file=USER_LOCAL_SERVER_FILE)}:{node_port}" for node_port in node_ports]
            rows.append((deployment, statuses, workers, "\n".join(urls)))

        except Exception as e:
            console.log(f"[red]Error when connecting to kalavai service: {str(e)}")
            return
        
    console.print(
        generate_table(columns=columns, rows=rows)
    )
        
    console.log("Get logs with [yellow]kalavai job logs <name of deployment> [white](note it only works when the deployment is complete)")
    console.log("Get full job manifest with [yellow]kalavai job manifest <name of deployment> [white](note it only works when the deployment is complete)")


@arguably.command
def job__logs(name, *others, pod_name=None, stream=False):
    """
    Get logs for a specific job
    """
    try:
        CLUSTER.validate_cluster()
    except Exception as e:
        console.log(f"[red]Problems with your pool: {str(e)}")
        return
    
    data = {
        "namespace": "default",
        "label": "leaderworkerset.sigs.k8s.io/name",
        "value": name
    }
    while True:
        try:
            result = request_to_server(
                method="post",
                endpoint="/v1/get_logs_for_label",
                data=data,
                server_creds=USER_LOCAL_SERVER_FILE
            )
            if not stream:
                for pod, logs in result.items():
                    if pod_name is not None and pod_name != pod:
                        continue
                    console.log(f"[yellow]Pod {pod}")
                    console.log(f"[green]{logs}")
                break
            else:
                os.system("clear")
                for pod, logs in result.items():
                    if pod_name is not None and pod_name != pod:
                        continue
                    print(f"Pod {pod}")
                    print(f"{logs}")
                time.sleep(1)
        except KeyboardInterrupt:
            break
        except Exception as e:
            console.log(f"[red]Error when connecting to kalavai service: {str(e)}")
            console.log(f"Check if {name} is running with [yellow]kalavai job list")
            return

@arguably.command
def job__manifest(*others, name):
    """
    Get job manifest description
    """
    try:
        CLUSTER.validate_cluster()
    except Exception as e:
        console.log(f"[red]Problems with your pool: {str(e)}")
        return
    
    data = {
        "namespace": "default",
        "label": "leaderworkerset.sigs.k8s.io/name",
        "value": name
    }
    try:
        result = request_to_server(
            method="post",
            endpoint="/v1/describe_pods_for_label",
            data=data,
            server_creds=USER_LOCAL_SERVER_FILE
        )
        for pod, manifest in result.items():
            manifest = json.dumps(manifest, indent=3)
            console.log(f"[yellow]Pod {pod}")
            console.log(f"{manifest}")
    except Exception as e:
        console.log(f"[red]Error when connecting to kalavai service: {str(e)}")
        return 


@arguably.command
def ray__create(template_path, *others):
    """
    Create a cluster using KubeRay operator
    """
    try:
        CLUSTER.validate_cluster()
    except Exception as e:
        console.log(f"[red]Problems with your pool: {str(e)}")
        return
    
    with open(template_path, "r") as f:
        template_yaml = yaml.safe_load(f)
        # ensure deployment is labelled (for tracking and deletion)
        if "metadata" not in template_yaml or "name" not in template_yaml["metadata"]:
            console.log("[red]Cluster must contain a metadata field and include a name entry.")
            return
        name = template_yaml["metadata"]["name"]
        if "labels" in template_yaml["metadata"]:
            template_yaml["metadata"]["labels"][RAY_LABEL] = name
        else:
            template_yaml["metadata"]["labels"] = {
                RAY_LABEL: name
            }
        template_yaml = json.dumps(template_yaml)

    data = {
        "object": {
            "group": "ray.io",
            "api_version": "v1",
            "namespace": "default",
            "plural": "rayclusters"
        },
        "body": template_yaml
    }
    try:
        result = request_to_server(
            method="post",
            endpoint="/v1/deploy_custom_object",
            data=data,
            server_creds=USER_LOCAL_SERVER_FILE
        )
        if len(result['failed']) > 0:
            console.log(f"[red]Error when deploying template\n\n{result['failed']}")
            return
        if len(result['successful']) > 0:
            console.log(f"[green]Template {template_path} successfully deployed!")
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
        "namespace": "default",
        "plural": "rayclusters"
    }
    try:
        result = request_to_server(
            method="post",
            endpoint="/v1/get_objects_of_type",
            data=data,
            server_creds=USER_LOCAL_SERVER_FILE
        )
        clusters = result['items']

    except Exception as e:
        console.log(f"[red]Error when connecting to kalavai service: {str(e)}")
        return

    if len(clusters) == 0:
        console.log("No clusters available")
        return
    
    # pretty print
    columns = ["Name", "Status", "CPUs", "GPUs", "Memory", "Endpoints"]
    rows = []
    server_ip = load_server_info(data_key=SERVER_IP_KEY, file=USER_LOCAL_SERVER_FILE)
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
            (cluster_name, status, cpus, gpus, memory, "\n".join(endpoints))
        )
    table = generate_table(columns=columns, rows=rows)
    console.log(table)

@arguably.command
def ray__delete(*others, name):
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
        "namespace": "default",
        "label": RAY_LABEL, # this ensures that both raycluster and services are deleted
        "value": name
    }
    try:
        result = request_to_server(
            method="post",
            endpoint="/v1/delete_labeled_resources",
            data=data,
            server_creds=USER_LOCAL_SERVER_FILE
        )
        console.log(f"{result}")
    except Exception as e:
        console.log(f"[red]Error when connecting to kalavai service: {str(e)}")

@arguably.command
def ray__manifest(*others, name):
    """
    Get ray cluster manifest description
    """
    try:
        CLUSTER.validate_cluster()
    except Exception as e:
        console.log(f"[red]Problems with your pool: {str(e)}")
        return
    
    data = {
        "namespace": "default",
        "label": "ray.io/cluster",
        "value": name
    }
    try:
        result = request_to_server(
            method="post",
            endpoint="/v1/describe_pods_for_label",
            data=data,
            server_creds=USER_LOCAL_SERVER_FILE
        )
        for pod, manifest in result.items():
            manifest = json.dumps(manifest, indent=3)
            console.log(f"[yellow]Pod {pod}")
            console.log(f"{manifest}")
    except Exception as e:
        console.log(f"[red]Error when connecting to kalavai service: {str(e)}")
        return

if __name__ == "__main__":
    user_path("", create_path=True)
    
    arguably.run()