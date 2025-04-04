import os
import time
from collections import defaultdict
import math
import uuid
import socket
import ipaddress
import netifaces as ni
from typing import Optional
from pydantic import BaseModel
from enum import Enum
import re

from kalavai_client.cluster import CLUSTER
from kalavai_client.utils import (
    DEPLOY_LLM_SIDECARS_KEY,
    NODE_ROLE_LABEL,
    check_gpu_drivers,
    generate_join_token,
    load_user_id,
    register_cluster,
    request_to_server,
    load_server_info,
    decode_dict,
    send_pool_invite,
    unregister_cluster,
    generate_compose_config,
    store_server_info,
    is_watcher_alive,
    run_cmd,
    leave_vpn,
    safe_remove,
    get_public_seeds,
    load_template,
    is_storage_compatible,
    NODE_NAME_KEY,
    MANDATORY_TOKEN_FIELDS,
    PUBLIC_LOCATION_KEY,
    CLUSTER_IP_KEY,
    CLUSTER_NAME_KEY,
    AUTH_KEY,
    WATCHER_SERVICE_KEY,
    CLUSTER_TOKEN_KEY,
    READONLY_AUTH_KEY,
    WRITE_AUTH_KEY,
    WATCHER_PORT_KEY,
    WATCHER_SERVICE_KEY,
    USER_NODE_LABEL_KEY,
    ALLOW_UNREGISTERED_USER_KEY,
    KALAVAI_AUTH
)
from kalavai_client.env import (
    USER_COOKIE,
    USER_LOCAL_SERVER_FILE,
    TEMPLATE_LABEL,
    SERVER_IP_KEY,
    USER_COMPOSE_FILE,
    DEFAULT_VPN_CONTAINER_NAME,
    CONTAINER_HOST_PATH,
    USER_VPN_COMPOSE_FILE,
    USER_HELM_APPS_FILE,
    USER_KUBECONFIG_FILE,
    USER_TEMPLATES_FOLDER,
    USER_WORKSPACE_TEMPLATE,
    DEFAULT_USER_WORKSPACE_VALUES,
    STORAGE_CLASS_LABEL,
    USER_NODE_LABEL,
    DEFAULT_WATCHER_PORT,
    HELM_APPS_FILE,
    HELM_APPS_VALUES,
    POOL_CONFIG_DEFAULT_VALUES,
    POOL_CONFIG_TEMPLATE,
    FORBIDEDEN_IPS
)

class Job(BaseModel):
    owner: Optional[str] = None
    name: Optional[str] = None
    workers: Optional[str] = None
    endpoint: Optional[str] = None
    status: Optional[str] = None

class DeviceStatus(BaseModel):
    name: str
    memory_pressure: bool
    disk_pressure: bool
    pid_pressure: bool
    ready: bool
    unschedulable: bool

class GPU(BaseModel):
    node: str
    available: int
    total: int
    ready: bool
    model: str

class TokenType(Enum):
    ADMIN = 0
    USER = 1
    WORKER = 2


def set_schedulable(schedulable, node_names):
    """
    Delete job in the cluster
    """
    # deploy template with kube-watcher
    data = {
        "schedulable": str(schedulable),
        "node_names": node_names
    }
    try:
        res = request_to_server(
            method="post",
            endpoint="/v1/set_node_schedulable",
            data=data,
            server_creds=USER_LOCAL_SERVER_FILE,
            user_cookie=USER_COOKIE
        )
        if res is not None and "detail" in res:
            return {"error": res["detail"]}
        else:
            return {"result": res}
    except Exception as e:
        return {"error": f"Error when connecting to kalavai service: {str(e)}"}

def init_user_workspace(user_id=None, node_name=None, force_namespace=None):
    
    # load template config and populate with values
    sidecar_template_yaml = load_template(
        template_path=USER_WORKSPACE_TEMPLATE,
        values={},
        default_values_path=DEFAULT_USER_WORKSPACE_VALUES)

    try:
        data = {"config": sidecar_template_yaml}
        if force_namespace is not None:
            data["force_namespace"] = force_namespace
        if user_id is not None:
            data["user_id"] = user_id
        if node_name is not None:
            data["node_name"] = node_name
        result = request_to_server(
            method="post",
            endpoint="/v1/create_user_space",
            data=data,
            server_creds=USER_LOCAL_SERVER_FILE,
            user_cookie=USER_COOKIE
        )
        return {"success"}
    except Exception as e:
        return {"error": f"Error when connecting to kalavai service: {str(e)}"}

def check_seed_compatibility():
    """Check required packages to start pools"""
    logs = []
    # docker
    try:
        run_cmd("docker version >/dev/null 2>&1")
    except:
        logs.append("[red]Docker not installed. Install instructions:\n")
        logs.append("   Linux: https://docs.docker.com/engine/install/\n")
        logs.append("   Windows/MacOS: https://docs.docker.com/desktop/\n")
    
    return {"issues": logs}

def check_worker_compatibility():
    """Check required packages to join pools"""
    logs = []
    # docker
    try:
        run_cmd("docker version >/dev/null 2>&1")
    except:
        logs.append("[red]Docker not installed. Install instructions:\n")
        logs.append("   Linux: https://docs.docker.com/engine/install/\n")
        logs.append("   Windows/MacOS: https://docs.docker.com/desktop/\n")
    
    return {"issues": logs}

def get_ip_addresses(subnet=None):
    ips = []
    retry = 3
    while len(ips) == 0:
        for iface in ni.interfaces():
            try:
                ip = ni.ifaddresses(iface)[ni.AF_INET][0]['addr']
                if ip in FORBIDEDEN_IPS:
                    continue
                if subnet is None or ipaddress.ip_address(ip) in ipaddress.ip_network(subnet):
                    ips.append(ip)
            except:
                pass
        time.sleep(2)
        retry -= 1
        if retry < 0:
            raise ValueError(f"No IPs available on subnet {subnet}")
    return ips

def fetch_resources():
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
    except Exception as e:
        return {"error": str(e)}
        
    return {"total": total, "available": available}

def fetch_job_defaults(name):
    data = {
        "template": name
    }
    try:
        defaults = request_to_server(
            method="get",
            endpoint="/v1/job_defaults",
            data=data,
            server_creds=USER_LOCAL_SERVER_FILE,
            user_cookie=USER_COOKIE
        )
        return defaults
    except Exception as e:
        return {"error": str(e)}
    
def fetch_job_templates():
    try:
        templates = request_to_server(
            method="get",
            endpoint="/v1/get_job_templates",
            server_creds=USER_LOCAL_SERVER_FILE,
            data=None,
            user_cookie=USER_COOKIE
        )
        return templates
    except Exception as e:
        return {"error": str(e)}

def fetch_job_names():
    data = {
        "group": "batch.volcano.sh",
        "api_version": "v1alpha1",
        "plural": "jobs"
    }
    try:
        jobs = request_to_server(
            method="post",
            endpoint="/v1/get_objects_of_type",
            data=data,
            server_creds=USER_LOCAL_SERVER_FILE,
            user_cookie=USER_COOKIE
        )
        all_jobs = []
        for ns, ds in jobs.items():
            all_jobs.extend([Job(owner=ns, name=d["metadata"]["labels"][TEMPLATE_LABEL]) for d in ds["items"]])
    except Exception as e:
        return {"error": str(e)}
    
    return all_jobs  

def fetch_job_details(jobs: list[Job]):
    """Get job details. A job is a dict:
    {
        "namespace": ns,
        "name": name
    }
    """
    job_details = []
    for job in jobs:
        namespace = job.owner
        deployment = job.name
        try:
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
            restart_counts = 0
            for ns, ss in result.items():
                if ns != namespace: # same job name, different namespace
                    continue
                for _, values in ss.items():
                    # TODO: get nodes involved in deployment (needs kubewatcher)
                    if "conditions" in values and values["conditions"] is not None:
                        restart_counts = sum([c["restart_count"] for c in values["conditions"]])
                    workers_status[values["status"]] += 1
            workers = "\n".join([f"{k}: {v}" for k, v in workers_status.items()])
            if restart_counts > 0:
                workers += f"\n({restart_counts} restart)"
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
            if "Ready" in workers_status and len(workers_status) == 1:
                status = "running"
            elif any([st in workers_status for st in ["Failed"]]):
                status = "error"
            elif any([st in workers_status for st in ["Pending"]]) or len(workers_status) == 0:
                status = "pending"
            elif any([st in workers_status for st in ["Succeeded", "Completed"]]):
                status = "completed"
            else:
                status = "working"
            job_details.append(
                Job(owner=namespace,
                    name=deployment,
                    workers=workers,
                    endpoint="\n".join(urls),
                    status=str(status))
            )

        except Exception as e:
            return {"error": str(e)}
    
    return job_details

def deploy_job(template_name, values_dict, force_namespace=None, target_labels=None):

    # deploy template with kube-watcher
    data = {
        "template": template_name,
        "template_values": values_dict
    }
    if force_namespace is not None:
        data["force_namespace"] = force_namespace
    if target_labels is not None:
        data["target_labels"] = target_labels

    try:
        result = request_to_server(
            method="post",
            endpoint="/v1/deploy_job",
            data=data,
            server_creds=USER_LOCAL_SERVER_FILE,
            user_cookie=USER_COOKIE
        )
        return result
    except Exception as e:
        return {"error": str(e)}  
    
def deploy_test_job(template_str, values_dict, default_values, force_namespace=None):
    
    # submit custom deployment
    data = {
        "template": template_str,
        "template_values": values_dict,
        "default_values": default_values
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
        return result
    except Exception as e:
        return {"error": str(e)}
    
def delete_job(name, force_namespace=None):
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
        return result
    except Exception as e:
        return {"error": str(e)}

def fetch_devices():
    """Load devices status info for all hosts"""
    try:
        data = request_to_server(
            method="get",
            endpoint="/v1/get_nodes",
            data={},
            server_creds=USER_LOCAL_SERVER_FILE,
            user_cookie=USER_COOKIE
        )
        devices = []
        for node, status in data.items():
            devices.append(
                DeviceStatus(
                    name=node,
                    memory_pressure=status["MemoryPressure"],
                    disk_pressure=status["DiskPressure"],
                    pid_pressure=status["PIDPressure"],
                    ready=status["Ready"],
                    unschedulable=status["unschedulable"]
                )
            )
        return devices

    except Exception as e:
        return {"error": str(e)}

def fetch_job_logs(job_name, force_namespace=None, pod_name=None, tail=100):
    data = {
        "label": TEMPLATE_LABEL,
        "value": job_name,
        "tail": tail
    }
    if force_namespace is not None:
        data["force_namespace"] = force_namespace
    try:
        # send tail as parameter (fetch only last _tail_ lines)
        all_logs = request_to_server(
            method="post",
            endpoint="/v1/get_logs_for_label",
            data=data,
            server_creds=USER_LOCAL_SERVER_FILE,
            user_cookie=USER_COOKIE
        )
        return {pod: info for pod, info in all_logs.items() if pod_name is None or pod_name == pod}

    except Exception as e:
        return {"error": str(e)}
    

def load_gpu_models():
    data = request_to_server(
        method="post",
        endpoint="/v1/get_node_gpus",
        data={},
        server_creds=USER_LOCAL_SERVER_FILE,
        user_cookie=USER_COOKIE
    )
    return data.items()

def fetch_gpus(available=False):
    try:
        data = load_gpu_models()
        all_gpus = []
        for node, gpus in data:
            row_gpus = []
            for gpu in gpus["gpus"]:
                status = gpu["ready"] if "ready" in gpu else True
                if available and not status:
                    continue
                row_gpus.append( (f"{gpu['model']} ({math.floor(int(gpu['memory'])/1000)} GBs)", str(status)))
            if len(row_gpus) > 0:
                models, statuses = zip(*row_gpus)
                #rows.append([node, "\n".join(statuses), "\n".join(models), str(gpus["available"]), str(gpus["capacity"])])
                all_gpus.extend([
                    GPU(
                        node=node,
                        ready=status,
                        model=model,
                        available=gpus["available"],
                        total=gpus["capacity"]
                    ) for model, status in zip(models, statuses)
                ])
        return all_gpus

    except Exception as e:
        return {"error": str(e)}
    
def authenticate_user(user_key=None):
    if user_key is None:
        KALAVAI_AUTH.save_auth(user_key)
    
    return KALAVAI_AUTH.load_user_session()

def load_user_session():
    return KALAVAI_AUTH.load_user_session()

def user_logout():
    return KALAVAI_AUTH.clear_auth()

def check_token(token, public=False):
    try:
        data = decode_dict(token)
        for field in MANDATORY_TOKEN_FIELDS:
            assert field in data
        if public:
            if data[PUBLIC_LOCATION_KEY] is None:
                raise ValueError("Token is not valid for public pools. Did you start the cluster with a public_location?")
        return {"status": True}
    except Exception as e:
        return {"error": str(e)}
    
def delete_nodes(nodes):
    data = {
        "node_names": nodes
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
            return {"success": nodes}
        else:
            return {"error": result}
    except Exception as e:
        return {"error": f"Error when removing nodes {nodes}: {str(e)}"}

def cordon_nodes(nodes):
    return set_schedulable(schedulable=False, node_names=nodes)

def uncordon_nodes(nodes):
    return set_schedulable(schedulable=True, node_names=nodes)

def attach_to_pool(token, node_name=None):
    if node_name is None:
        node_name = f"{socket.gethostname()}-{uuid.uuid4().hex[:6]}"
    
    # check token
    valid = check_token(token=token)
    if "error" in valid:
        return {"error": f"Invalid token: {valid}"}

    try:
        data = decode_dict(token)
        kalavai_seed_ip = data[CLUSTER_IP_KEY]
        cluster_name = data[CLUSTER_NAME_KEY]
        auth_key = data[AUTH_KEY]
        watcher_service = data[WATCHER_SERVICE_KEY]
        public_location = data[PUBLIC_LOCATION_KEY]
    except Exception as e:
        return {"error": f"Invalid token. {str(e)}"} 
    
    # local agent join
    # 1. Generate local cache files
    # Generate docker compose recipe
    generate_compose_config(
        role="",
        vpn_token=public_location,
        node_name=node_name)
    
    store_server_info(
        server_ip=kalavai_seed_ip,
        auth_key=auth_key,
        file=USER_LOCAL_SERVER_FILE,
        watcher_service=watcher_service,
        node_name=node_name,
        cluster_name=cluster_name,
        public_location=public_location,
        user_api_key=None)
    
    run_cmd(f"docker compose -f {USER_COMPOSE_FILE} up -d")
    # ensure we are connected
    while True:
        time.sleep(30)
        if is_watcher_alive(server_creds=USER_LOCAL_SERVER_FILE, user_cookie=USER_COOKIE):
            break

    return cluster_name

def get_max_gpus():
    try:
        has_gpus = check_gpu_drivers()
        if has_gpus:
            return int(run_cmd("nvidia-smi -L | wc -l").decode())
        else:
            return 0
    except:
        return 0

def generate_worker_package(num_gpus=0, node_name=None, ip_address="0.0.0.0", storage_compatible=True):
    # get pool data from token  
    token = get_pool_token(mode=TokenType.WORKER)
    if "error" in token:
        return {"error": f"[red]Error when getting pool token: {token['error']}"}
    
    if node_name is None:
        node_name = f"worker-{uuid.uuid4().hex[:6]}"
    
    # parse pool data
    try:
        data = decode_dict(token["token"])
        kalavai_seed_ip = data[CLUSTER_IP_KEY]
        kalavai_token = data[CLUSTER_TOKEN_KEY]
        public_location = data[PUBLIC_LOCATION_KEY]
    except Exception as e:
        return {"error": f"Invalid token. {str(e)}"} 
    
    # join private network if provided
    node_labels = {
        STORAGE_CLASS_LABEL: storage_compatible,
        NODE_ROLE_LABEL: "worker"
    }
    # Generate docker compose recipe
    compose = generate_compose_config(
        write_to_file=False,
        role="agent",
        node_ip_address=ip_address,
        pool_ip=f"https://{kalavai_seed_ip}:6443",
        pool_token=kalavai_token,
        num_gpus=num_gpus,
        vpn_token=public_location,
        node_name=node_name,
        node_labels=node_labels)
    
    return compose


def join_pool(token, num_gpus=None, node_name=None, ip_address=None):
    compatibility = check_worker_compatibility()
    if len(compatibility["issues"]) > 0:
        return {"error": compatibility["issues"]}

    if num_gpus is None:
        num_gpus = get_max_gpus()

    if node_name is None:
        node_name = f"{socket.gethostname()}-{uuid.uuid4().hex[:6]}"
    
    # check token
    valid = check_token(token=token)
    if "error" in valid:
        return {"error": f"Invalid token: {valid}"}

    try:
        data = decode_dict(token)
        kalavai_seed_ip = data[CLUSTER_IP_KEY]
        kalavai_token = data[CLUSTER_TOKEN_KEY]
        cluster_name = data[CLUSTER_NAME_KEY]
        auth_key = data[AUTH_KEY]
        watcher_service = data[WATCHER_SERVICE_KEY]
        public_location = data[PUBLIC_LOCATION_KEY]
    except Exception as e:
        return {"error": f"Invalid token. {str(e)}"} 
    
    # join private network if provided
    node_labels = {
        STORAGE_CLASS_LABEL: is_storage_compatible(),
        NODE_ROLE_LABEL: "worker"
    }  
    # local agent join
    # Generate docker compose recipe
    generate_compose_config(
        role="agent",
        node_ip_address=ip_address,
        pool_ip=f"https://{kalavai_seed_ip}:6443",
        pool_token=kalavai_token,
        num_gpus=num_gpus,
        vpn_token=public_location,
        node_name=node_name,
        node_labels=node_labels)
    
    store_server_info(
        server_ip=kalavai_seed_ip,
        auth_key=auth_key,
        file=USER_LOCAL_SERVER_FILE,
        watcher_service=watcher_service,
        node_name=node_name,
        cluster_name=cluster_name,
        public_location=public_location,
        user_api_key=None)
    
    try:
        CLUSTER.start_worker_node()
    except Exception as e:
        return {"error": f"Error connecting to {cluster_name} @ {kalavai_seed_ip}. Check with the admin if the token is still valid."}

    # ensure we are connected
    while True:
        time.sleep(30)
        if is_watcher_alive(server_creds=USER_LOCAL_SERVER_FILE, user_cookie=USER_COOKIE):
            break
    
    # check the node has connected successfully
    try:
        while not CLUSTER.is_agent_running():
            time.sleep(30)
    except KeyboardInterrupt:
        return {"error": "Installation aborted. Leaving pool."}
    
    result = init_user_workspace(
        user_id=load_user_id(),
        node_name=node_name)
    if "error" in result:
        return {"error": f"Error when creating user workspace: {result}"}
    
    return cluster_name

def create_pool(
        cluster_name: str,
        ip_address: str,
        description: str="",
        token_mode: TokenType=TokenType.USER,
        app_values: str=None,
        pool_config_values: str=None,
        num_gpus: int=0,
        node_name: str=None,
        location: str=None
    ):

    if not check_seed_compatibility():
        return {"error": "Requirements failed"}
    
    if app_values is None:
        app_values = HELM_APPS_VALUES
    
    if pool_config_values is None:
        pool_config_values = POOL_CONFIG_DEFAULT_VALUES

    node_name = f"{socket.gethostname()}-{uuid.uuid4().hex[:6]}"
    user_id = load_user_id()
    
    node_labels = {
        STORAGE_CLASS_LABEL: is_storage_compatible(),
        NODE_ROLE_LABEL: "server"
    }

    # if location is not None:
    #     try:
    #         vpn = get_vpn_details(
    #             location=location,
    #             user_cookie=USER_COOKIE)
    #         node_labels[USER_NODE_LABEL] = user["username"]
    #     except Exception as e:
    #         return {"error": f"[red]Error when joining network: {str(e)}"}
        
    if num_gpus is None:
        num_gpus = get_max_gpus()
    
    # Generate docker compose recipe
    generate_compose_config(
        role="server",
        vpn_token=location,
        node_ip_address=ip_address,
        num_gpus=num_gpus,
        node_name=node_name,
        node_labels=node_labels
    )
    
    # start server
    CLUSTER.start_seed_node()
    
    while not CLUSTER.is_agent_running():
        time.sleep(10)
    
    # select IP address (for external discovery)
    if ip_address is None or location is not None:
        # load VPN ip
        ip_address = CLUSTER.get_vpn_ip()

    # populate local cred files
    
    auth_key = user_id if user_id is not None else str(uuid.uuid4())
    write_auth_key = str(uuid.uuid4())
    readonly_auth_key = str(uuid.uuid4())
    watcher_service = f"{ip_address}:{DEFAULT_WATCHER_PORT}"
    values = {
        CLUSTER_NAME_KEY: cluster_name,
        CLUSTER_IP_KEY: ip_address,
        AUTH_KEY: auth_key,
        READONLY_AUTH_KEY: readonly_auth_key,
        WRITE_AUTH_KEY: write_auth_key,
        WATCHER_PORT_KEY: DEFAULT_WATCHER_PORT,
        WATCHER_SERVICE_KEY: watcher_service,
        USER_NODE_LABEL_KEY: USER_NODE_LABEL,
        ALLOW_UNREGISTERED_USER_KEY: True, # Change this if only registered users are allowed,
        DEPLOY_LLM_SIDECARS_KEY: location is not None
    }

    store_server_info(
        server_ip=ip_address,
        auth_key=auth_key,
        readonly_auth_key=readonly_auth_key,
        write_auth_key=write_auth_key,
        file=USER_LOCAL_SERVER_FILE,
        watcher_service=watcher_service,
        node_name=node_name,
        cluster_name=cluster_name,
        public_location=location,
        user_api_key=None)
    
    # Generate helmfile recipe
    helm_yaml = load_template(
        template_path=HELM_APPS_FILE,
        values=values,
        default_values_path=app_values,
        force_defaults=True)
    with open(USER_HELM_APPS_FILE, "w") as f:
        f.write(helm_yaml)
    
    # set template values in helmfile
    try:
        CLUSTER.update_dependencies(
            dependencies_file=USER_HELM_APPS_FILE
        )
    except Exception as e:
        return {"error": f"Error when updating dependencies: {str(e)}"}

    if location is not None:
        # TODO: register with kalavai if it's a public cluster
        pass
        #pool__publish()
    
    # wait until the server is ready to create objects
    while True:
        time.sleep(30)
        if is_watcher_alive(server_creds=USER_LOCAL_SERVER_FILE, user_cookie=USER_COOKIE):
            break

    result = pool_init(pool_config_values_path=pool_config_values)
    if "error" in result or ("failed" in result and len(result['failed']) > 0):
        return {"error": f"Error when initialising pool: {result}"}
    # init default namespace
    init_user_workspace(
        user_id=user_id,
        node_name=node_name,
        force_namespace="default")
    # if only_registered_users:
    #     # init user namespace
    #     init_user_workspace(
    #         user_id=user_id)
    # register cluster (if user is logged in)
    result = register_pool(
        cluster_name=cluster_name,
        description=description,
        is_private=True,
        token_mode=token_mode)

    if "error" in result:
        return {"warning": result["error"]}
    if "warning" in result:
        return {"warning": result["warning"]}
    
    return {"success"}


def get_pool_token(mode: TokenType):

    try:
        match mode:
            case TokenType.ADMIN:
                auth_key = load_server_info(data_key=AUTH_KEY, file=USER_LOCAL_SERVER_FILE)
            case TokenType.USER:
                auth_key = load_server_info(data_key=WRITE_AUTH_KEY, file=USER_LOCAL_SERVER_FILE)
            case _:
                auth_key = load_server_info(data_key=READONLY_AUTH_KEY, file=USER_LOCAL_SERVER_FILE)
        if auth_key is None:
            return {"error": "Cannot generate selected token mode. Are you the seed node?"}

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

        return {"token": join_token}
    except Exception as e:
        return {"error": f"Error when generating token: {str(e)}"}

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
        return result
    except Exception as e:
        return {"error": f"[red]Error when connecting to kalavai service: {str(e)}"}
    
def register_pool(cluster_name, description, is_private=True, token_mode=TokenType.USER):
    token = get_pool_token(mode=token_mode)["token"]
    valid = check_token(token=token, public=not is_private)
    if "error" in valid:
        return {"error": valid}
    try:
        result = register_cluster(
            name=cluster_name,
            token=token,
            description=description,
            user_cookie=USER_COOKIE,
            is_private=is_private)

        return {"success": result}
    except Exception as e:
        return {"warning": str(e)}
    
def unregister_pool():
    cluster_name = load_server_info(data_key=CLUSTER_NAME_KEY, file=USER_LOCAL_SERVER_FILE)
    try:
        unregister_cluster(
            name=cluster_name,
            user_cookie=USER_COOKIE)
    except Exception as e:
        return {"warning": str(e)}
    return {"success"}

def is_connected():
    if not os.path.isfile(USER_LOCAL_SERVER_FILE):
        return False
    return is_watcher_alive(server_creds=USER_LOCAL_SERVER_FILE, user_cookie=USER_COOKIE, timeout=10)

def is_agent_running():
    return CLUSTER.is_agent_running()

def is_server():
    return CLUSTER.is_seed_node()

def pause_agent(retries=3):
    try:
        while retries > 0:
            state = CLUSTER.pause_agent()
            if state:
                return {"success"}
            time.sleep(5)
            retries -= 1
    except:
        return {"error": "Could not pause agent"}

def resume_agent(retries=3):
    try:
        while retries > 0:
            state = CLUSTER.restart_agent()
            if state:
                return {"success"}
            time.sleep(5)
            retries -= 1
    except:
        return {"error": "Could not resume agent"}

def cleanup_local():
    safe_remove(CONTAINER_HOST_PATH)
    safe_remove(USER_COMPOSE_FILE)
    safe_remove(USER_VPN_COMPOSE_FILE)
    safe_remove(USER_HELM_APPS_FILE)
    safe_remove(USER_KUBECONFIG_FILE)
    safe_remove(USER_LOCAL_SERVER_FILE)
    safe_remove(USER_TEMPLATES_FOLDER)

def delete_node(name):
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
            return {f"Node {name} deleted successfully"}
        else:
            return {"error": result}
    except Exception as e:
        return {"error": str(e)}

def stop_pool(skip_node_deletion=False):
    # delete local node from server
    logs = []
    if not skip_node_deletion:
        logs.append(
            delete_node(load_server_info(data_key=NODE_NAME_KEY, file=USER_LOCAL_SERVER_FILE))
        )
    # unpublish event (only if seed node)
    if CLUSTER.is_seed_node():
        unregister_pool()
    
    # disconnect from VPN first, then remove agent, then remove local files
    try:
        vpns = leave_vpn(container_name=DEFAULT_VPN_CONTAINER_NAME)
        if vpns is not None:
            for vpn in vpns:
                logs.append(f"You have left {vpn} VPN")
    except:
        # no vpn
        pass

    # remove local node agent
    CLUSTER.remove_agent()

    # clean local files
    cleanup_local()

    return {"logs": logs}

def list_available_pools(user_only=False):
    pools = get_public_seeds(user_only=user_only, user_cookie=USER_COOKIE)
    return pools

def send_invites(invitees):
    result = send_pool_invite(
        cluster_name=load_server_info(data_key=CLUSTER_NAME_KEY, file=USER_LOCAL_SERVER_FILE),
        invitee_addresses=invitees,
        user_cookie=USER_COOKIE
    )
    return result
