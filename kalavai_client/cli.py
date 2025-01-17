from collections import defaultdict
import math
import os
import json
import uuid
import time
import socket
from pathlib import Path
from getpass import getpass
import ipaddress
from sys import exit

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
    load_user_session,
    SERVER_IP_KEY,
    AUTH_KEY,
    WATCHER_SERVICE_KEY,
    READONLY_AUTH_KEY,
    WRITE_AUTH_KEY,
    PUBLIC_LOCATION_KEY,
    NODE_NAME_KEY,
    CLUSTER_NAME_KEY,
    CLUSTER_IP_KEY,
    CLUSTER_TOKEN_KEY,
    WATCHER_PORT_KEY,
    MANDATORY_TOKEN_FIELDS,
    USER_NODE_LABEL_KEY,
    ENDPOINT_PORTS_KEY,
    TEMPLATE_ID_KEY,
    ALLOW_UNREGISTERED_USER_KEY
)
from kalavai_client.cluster import (
    k3sCluster
)


KALAVAI_PLATFORM_URL = os.getenv("KALAVAI_PLATFORM_URL", "https://platform.kalavai.net")
LOCAL_TEMPLATES_DIR = os.getenv("LOCAL_TEMPLATES_DIR", None)
VERSION = 1
RESOURCE_EXCLUDE = ["ephemeral-storage", "hugepages-1Gi", "hugepages-2Mi", "pods"]
CORE_NAMESPACES = ["lws-system", "kube-system", "gpu-operator", "kalavai"]
TEMPLATE_LABEL = "kalavai.job.name"
RAY_LABEL = "kalavai.ray.name"
PVC_NAME_LABEL = "kalavai.storage.name"
POOL_CONFIG_TEMPLATE = resource_path("assets/pool_config_template.yaml")
POOL_CONFIG_DEFAULT_VALUES = resource_path("assets/pool_config_values.yaml")
USER_WORKSPACE_TEMPLATE = resource_path("assets/user_workspace.yaml")
DEFAULT_USER_WORKSPACE_VALUES = resource_path("assets/user_workspace_values.yaml")
STORAGE_CLASS_NAME = "longhorn"
STORAGE_CLASS_LABEL = "kalavai.storage.enabled"
DEFAULT_STORAGE_NAME = "pool-cache"
DEFAULT_STORAGE_SIZE = 20
USER_NODE_LABEL = "kalavai.cluster.user"
KUBE_VERSION = os.getenv("KALAVAI_KUBE_VERSION", "v1.31.1+k3s1")
DEFAULT_FLANNEL_IFACE = os.getenv("KALAVAI_FLANNEL_IFACE", "netmaker")
FORBIDEDEN_IPS = ["127.0.0.1"]
# kalavai templates
HELM_APPS_FILE = resource_path("assets/apps.yaml")
HELM_APPS_VALUES = resource_path("assets/apps_values.yaml")
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
            server_creds=USER_LOCAL_SERVER_FILE,
            user_cookie=USER_COOKIE
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
            server_creds=USER_LOCAL_SERVER_FILE,
            user_cookie=USER_COOKIE
        )
        console.log(f"{res}")
    except Exception as e:
        console.log(f"[red]Error when connecting to kalavai service: {str(e)}")


def init_user_workspace(force_namespace=None):
    #set_schedulable(schedulable=True)
    
    # load template config and populate with values
    sidecar_template_yaml = load_template(
        template_path=USER_WORKSPACE_TEMPLATE,
        values={},
        default_values_path=DEFAULT_USER_WORKSPACE_VALUES)

    try:
        data = {"config": sidecar_template_yaml}
        if force_namespace is not None:
            data["force_namespace"] = force_namespace
        result = request_to_server(
            method="post",
            endpoint="/v1/create_user_space",
            data=data,
            server_creds=USER_LOCAL_SERVER_FILE,
            user_cookie=USER_COOKIE
        )
        console.log(f"Workspace creation (ignore already created warnings): {result}" )
    except Exception as e:
        console.log(f"[red]Error when connecting to kalavai service: {str(e)}")

def pool_init(pool_config_values_path=None):
    """Deploy configured objects to initialise pool"""
    if pool_config_values_path is None:
        return
    
    # load template config and populate with values
    sidecar_template_yaml = load_template(
        template_path=POOL_CONFIG_TEMPLATE,
        values={},
        default_values_path=pool_config_values_path)

    try:
        result = request_to_server(
            method="post",
            endpoint="/v1/deploy_generic_model",
            data={"config": sidecar_template_yaml},
            server_creds=USER_LOCAL_SERVER_FILE,
            user_cookie=USER_COOKIE
        )
        if 'failed' in result and len(result['failed']) > 0:
            console.log(f"[red]Error when deploying pool config\n\n{result['failed']}")
        if len(result['successful']) > 0:
            console.log(f"[green]Deployed pool config!")
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

def fetch_gpus():
    data = request_to_server(
        method="post",
        endpoint="/v1/get_node_gpus",
        data={},
        server_creds=USER_LOCAL_SERVER_FILE,
        user_cookie=USER_COOKIE
    )
    return data.items()

def select_gpus(message):
    console.log(f"[yellow]{message}")
    gpu_models = ["Any/None"]
    gpu_models_full = ["Any/None"]
    available_gpus = fetch_gpus()
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
    choices = select_token_type()
    token = pool__token(**choices)
    
    if description is None:
        console.log("[yellow] [Markdown] In a few words (max 500 chars), describe your goals with this cluster. Remember, this is what other users will see to decide whether to share their resources with you, [blue]so inspire them!")
        description = input(f"(You can edit this later in {KALAVAI_PLATFORM_URL}\n")
    
    description = description
    
    try:
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
def pool__start(cluster_name, *others,  only_registered_users: bool=False, ip_address: str=None, location: str=None, app_values: str=HELM_APPS_VALUES, pool_config_values: str=POOL_CONFIG_DEFAULT_VALUES):
    """
    Start Kalavai pool and start/resume sharing resources.

    Args:
        *others: all the other positional arguments go here
    """

    if CLUSTER.is_cluster_init():
        console.log(f"[white] You are already connected to {load_server_info(data_key=CLUSTER_NAME_KEY, file=USER_LOCAL_SERVER_FILE)}. Enter [yellow]kalavai pool stop[white] to exit and join another one.")
        return
    
    # if only registered users are allowed, check user has logged in
    if only_registered_users or location is not None:
        user = user_login(user_cookie=USER_COOKIE)
        if user is None:
            console.log("[white]--only-registered-users [red]or [white]--location[red] can only be used if the host is authenticated. Run [yellow]kalavai login[red] to authenticate")
            exit()
    else:
        user = None

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
            node_labels[USER_NODE_LABEL] = user["username"]
            time.sleep(5)
        except Exception as e:
            console.log(f"[red]Error when joining network: {str(e)}")
            return

    if ip_address is None:
        console.log("Scanning for valid IPs...")
        ip_address = select_ip_address(subnet=subnet)
    console.log(f"Using {ip_address} address for server")

    auth_key = str(uuid.uuid4())
    write_auth_key = str(uuid.uuid4())
    readonly_auth_key = str(uuid.uuid4())
    watcher_port = 31000
    watcher_service = f"{ip_address}:{watcher_port}"
    values = {
        CLUSTER_NAME_KEY: cluster_name,
        CLUSTER_IP_KEY: ip_address,
        AUTH_KEY: auth_key,
        READONLY_AUTH_KEY: readonly_auth_key,
        WRITE_AUTH_KEY: write_auth_key,
        WATCHER_PORT_KEY: watcher_port,
        WATCHER_SERVICE_KEY: watcher_service,
        USER_NODE_LABEL_KEY: USER_NODE_LABEL,
        ALLOW_UNREGISTERED_USER_KEY: not only_registered_users
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
        readonly_auth_key=readonly_auth_key,
        write_auth_key=write_auth_key,
        file=USER_LOCAL_SERVER_FILE,
        watcher_service=watcher_service,
        node_name=socket.gethostname(),
        cluster_name=cluster_name,
        public_location=location,
        user_api_key=user["api_key"] if user is not None else None)
    
    while not CLUSTER.is_agent_running():
        console.log("Waiting for seed to start...")
        time.sleep(10)
    
    console.log("Install dependencies...")
    # set template values in helmfile
    helm_yaml = load_template(
        template_path=HELM_APPS_FILE,
        values=values,
        default_values_path=app_values,
        force_defaults=True)
    
    with open(USER_HELM_APPS_FILE, "w") as f:
        f.write(helm_yaml)
    
    try:
        CLUSTER.update_dependencies(
            dependencies_file=USER_HELM_APPS_FILE
        )
    except Exception as e:
        console.log(f"Error: {str(e)}")
        exit()
    
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
        if is_watcher_alive(server_creds=USER_LOCAL_SERVER_FILE, user_cookie=USER_COOKIE):
            break
    console.log("Initialise user workspace...")
    pool_init(pool_config_values_path=pool_config_values)
    # init default namespace
    init_user_workspace(force_namespace="default")
    if only_registered_users:
        # init user namespace
        init_user_workspace()

    #storage__create(name=DEFAULT_STORAGE_NAME, storage=default_storage_size)

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
    
    if not CLUSTER.is_seed_node():
        console.log("[red]Node is not seed. Possible reasons: this is a worker node.")
        return None
    
    if not admin and not user and not worker:
        console.log(f"[red]Select at least one mode (--admin, --user or --worker)")
        return
    
    if admin:
        auth_key = load_server_info(data_key=AUTH_KEY, file=USER_LOCAL_SERVER_FILE)
    elif user:
        auth_key = load_server_info(data_key=WRITE_AUTH_KEY, file=USER_LOCAL_SERVER_FILE)
    else:
        auth_key = load_server_info(data_key=READONLY_AUTH_KEY, file=USER_LOCAL_SERVER_FILE)
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
    user = None
    if public_location is not None:
        console.log("Joining private network")
        try:
            vpn = join_vpn(
                location=public_location,
                user_cookie=USER_COOKIE)
            subnet = vpn["subnet"]
            user = user_login(user_cookie=USER_COOKIE)
            node_labels[USER_NODE_LABEL] = user["username"]
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
        public_location=public_location,
        user_api_key=user["api_key"] if user is not None else None)
    fetch_remote_templates()
    
    # set status to schedulable
    time.sleep(10)
    init_user_workspace()
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
            console.log("Unregistering pool...")
            unregister_cluster(
                name=load_server_info(data_key=CLUSTER_NAME_KEY, file=USER_LOCAL_SERVER_FILE),
                user_cookie=USER_COOKIE)
    except Exception as e:
        console.log(f"[red][WARNING]: (ignore if not a public pool) Error when unpublishing cluster. {str(e)}")
    # remove local node agent
    console.log("Removing agent and local cache")
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
        data = fetch_gpus()
        columns, rows = [], []
        for node, gpus in data:
            row_gpus = []
            for gpu in gpus["gpus"]:
                status = gpu["ready"] if "ready" in gpu else True
                if available and not status:
                    continue
                row_gpus.append( (f"{gpu['model']} ({math.floor(int(gpu['memory'])/1000)} GBs)", str(status)))
            if len(row_gpus) > 0:
                models, statuses = zip(*row_gpus)
                rows.append([node, "\n".join(statuses), "\n".join(models), str(gpus["available"]), str(gpus["capacity"])])

            columns = ["Ready", "GPU(s)", "Available", "Total"]
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
            server_creds=USER_LOCAL_SERVER_FILE,
            user_cookie=USER_COOKIE
        )
        available = request_to_server(
            method="get",
            endpoint="/v1/get_cluster_available_resources",
            data={},
            server_creds=USER_LOCAL_SERVER_FILE,
            user_cookie=USER_COOKIE
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
        "access_modes": ["ReadWriteMany"],
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
        data = request_to_server(
            method="get",
            endpoint="/v1/get_nodes",
            data={},
            server_creds=USER_LOCAL_SERVER_FILE,
            user_cookie=USER_COOKIE
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
            server_creds=USER_LOCAL_SERVER_FILE,
            user_cookie=USER_COOKIE
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
    default_values_path = os.path.join(path, template_name, "values.yaml")

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

    try:
        template_yaml = load_template(
            template_path=template_path,
            values=values_dict,
            default_values_path=default_values_path)
    except Exception as e:
        console.log(f"[red]Error: {str(e)}")
        exit()

    # deploy template with kube-watcher
    data = {
        "object": {
            "group": "batch.volcano.sh",
            "api_version": "v1alpha1",
            "plural": "jobs"
            # "group": "leaderworkerset.x-k8s.io",
            # "api_version": "v1",
            # "plural": "leaderworkersets"
        },
        "body": template_yaml
    }
    if force_namespace is not None:
        data["force_namespace"] = force_namespace

    try:
        result = request_to_server(
            method="post",
            endpoint="/v1/deploy_custom_object",
            data=data,
            server_creds=USER_LOCAL_SERVER_FILE,
            user_cookie=USER_COOKIE
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
    if ENDPOINT_PORTS_KEY in values_dict:
        deployment_name = values_dict[TEMPLATE_ID_KEY]
        ports = [int(port) for port in values_dict[ENDPOINT_PORTS_KEY].split(",")]
        data = {
            "name": f"{deployment_name}-serve",
            "labels": {TEMPLATE_LABEL: deployment_name},
            "selector_labels": {
                TEMPLATE_LABEL: deployment_name,
                "role": "leader"
            },
            "service_type": "NodePort",
            "ports": [
                {"name": f"http-{port}", "port": port, "protocol": "TCP", "target_port": port} for port in ports
            ]
        }
        if force_namespace is not None:
            data["force_namespace"] = force_namespace
        try:
            result = request_to_server(
                method="post",
                endpoint="/v1/deploy_service",
                data=data,
                server_creds=USER_LOCAL_SERVER_FILE,
                user_cookie=USER_COOKIE
            )
            console.log("Service deployed")
        except Exception as e:
            console.log(f"[red]Error when connecting to kalavai service: {str(e)}")


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
    data = {
        "label": TEMPLATE_LABEL, # this ensures that both lws template and services are deleted
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
def job__estimate(billion_parameters, *others, precision=32):
    """Guesstimate of resources needed based on required memory and current resources"""
    try:
        CLUSTER.validate_cluster()
    except Exception as e:
        console.log(f"[red]Problems with your pool: {str(e)}")
        return
    
    average_vram = 8
    required_memory = float(billion_parameters) * (precision / 8) / 1.2
    available_gpus = fetch_gpus()
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
def job__list(*others, detailed=False):
    """
    List jobs in the cluster
    """
    try:
        CLUSTER.validate_cluster()
    except Exception as e:
        console.log(f"[red]Problems with your pool: {str(e)}")
        return

    data = {
        "group": "batch.volcano.sh",
        "api_version": "v1alpha1",
        "plural": "jobs"
        # "group": "leaderworkerset.x-k8s.io",
        # "api_version": "v1",
        # "plural": "leaderworkersets",
    }
    try:
        result = request_to_server(
            method="post",
            endpoint="/v1/get_objects_of_type",
            data=data,
            server_creds=USER_LOCAL_SERVER_FILE,
            user_cookie=USER_COOKIE
        )
        all_deployments = defaultdict(list)
        for ns, ds in result.items():
            all_deployments[ns].extend([d["metadata"]["labels"][TEMPLATE_LABEL] for d in ds["items"]])
        #deployments = {ns: d["metadata"]["labels"][TEMPLATE_LABEL] for ns, ds in result.items() for d in ds["items"]}
    except Exception as e:
        console.log(f"[red]Error when connecting to kalavai service: {str(e)}")
        return
    if len(all_deployments.keys()) == 0:
        console.log("[green]No deployments found.")
        return
    
    columns = ["Owner", "Deployment", "Workers", "Endpoint"]
    if detailed:
        columns.append("Status")
    rows = []
    for namespace, deployments in all_deployments.items():
        for deployment in deployments:
            try:
                # get status for deployment
                if detailed:
                    data = {
                        "group": "batch.volcano.sh",
                        "api_version": "v1alpha1",
                        "plural": "jobs",
                        # "group": "leaderworkerset.x-k8s.io",
                        # "api_version": "v1",
                        # "plural": "leaderworkersets",
                        "name": deployment
                    }
                    result = request_to_server(
                        method="post",
                        endpoint="/v1/get_status_for_object",
                        data=data,
                        server_creds=USER_LOCAL_SERVER_FILE,
                        user_cookie=USER_COOKIE
                    )
                    ss = [] # flatten results ({namespace: statuses})
                    [ss.extend(values) for values in result.values()]
                    if len(ss) > 0:
                        last = ss[-1]
                        statuses = f"[{last['lastTransitionTime']}] {last['status']}"
                    else:
                        statuses = "Unknown"
                # get pod statuses
                data = {
                    "label": TEMPLATE_LABEL,
                    "value": deployment
                }
                result = request_to_server(
                    method="post",
                    endpoint="/v1/get_pods_status_for_label",
                    data=data,
                    server_creds=USER_LOCAL_SERVER_FILE,
                    user_cookie=USER_COOKIE
                )
                workers_status = defaultdict(int)
                for ns, ss in result.items():
                    if ns != namespace: # same job name, different namespace
                        continue
                    for _, values in ss.items():
                        workers_status[values["status"]] += 1
                workers = "\n".join([f"{k}: {v}" for k, v in workers_status.items()])
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
                    server_creds=USER_LOCAL_SERVER_FILE,
                    user_cookie=USER_COOKIE
                )
                node_ports = [f"{p['node_port']} (mapped to {p['port']})" for s in result.values() for p in s["ports"]]

                urls = [f"http://{load_server_info(data_key=SERVER_IP_KEY, file=USER_LOCAL_SERVER_FILE)}:{node_port}" for node_port in node_ports]
                row = [namespace, deployment, workers, "\n".join(urls)]
                if detailed:
                    row.append(statuses)
                rows.append(row)

            except Exception as e:
                console.log(f"[red]Error when connecting to kalavai service: {str(e)}")
                return
        
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
    
    data = {
        "label": TEMPLATE_LABEL,
        "value": name,
        "tail": tail
    }
    if force_namespace is not None:
        data["force_namespace"] = force_namespace
    while True:
        try:
            # send tail as parameter (fetch only last _tail_ lines)
            result = request_to_server(
                method="post",
                endpoint="/v1/get_logs_for_label",
                data=data,
                server_creds=USER_LOCAL_SERVER_FILE,
                user_cookie=USER_COOKIE
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
            "plural": "rayclusters"
        },
        "body": template_yaml
    }
    try:
        result = request_to_server(
            method="post",
            endpoint="/v1/deploy_custom_object",
            data=data,
            server_creds=USER_LOCAL_SERVER_FILE,
            user_cookie=USER_COOKIE
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
        "label": RAY_LABEL, # this ensures that both raycluster and services are deleted
        "value": name
    }
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
        "label": "ray.io/cluster",
        "value": name
    }
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

if __name__ == "__main__":
    user_path("", create_path=True)
    
    arguably.run()