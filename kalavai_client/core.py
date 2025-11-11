import os
import yaml
import time
from collections import defaultdict
import random
import json
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
    get_max_gpus,
    NODE_NAME_KEY,
    MANDATORY_TOKEN_FIELDS,
    PUBLIC_LOCATION_KEY,
    CLUSTER_IP_KEY,
    CLUSTER_NAME_KEY,
    AUTH_KEY,
    USER_ID_KEY,
    WATCHER_SERVICE_KEY,
    CLUSTER_TOKEN_KEY,
    READONLY_AUTH_KEY,
    WRITE_AUTH_KEY,
    WATCHER_PORT_KEY,
    WATCHER_SERVICE_KEY,
    WATCHER_IMAGE_TAG_KEY,
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
    MODEL_DEPLOYMENT_VALUES_MAPPING,
    POOL_CONFIG_TEMPLATE,
    FORBIDEDEN_IPS,
    DEFAULT_POOL_CONFIG_TEMPLATE
)

class Job(BaseModel):
    owner: Optional[str] = "default"
    name: Optional[str] = None
    workers: Optional[str] = None
    endpoint: Optional[str] = None
    status: Optional[str] = None
    host_nodes: Optional[str] = None

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
        run_cmd("docker ps", hide_output=True)
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
        run_cmd("docker ps", hide_output=True)
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

def fetch_resources(node_names: list[str]=None):
    data = {}
    if node_names is not None:
        data["node_names"] = node_names
    try:
        total = request_to_server(
            method="post",
            endpoint="/v1/get_cluster_total_resources",
            data=data,
            server_creds=USER_LOCAL_SERVER_FILE,
            user_cookie=USER_COOKIE
        )
        available = request_to_server(
            method="post",
            endpoint="/v1/get_cluster_available_resources",
            data=data,
            server_creds=USER_LOCAL_SERVER_FILE,
            user_cookie=USER_COOKIE
        )
    except Exception as e:
        return {"error": str(e)}
        
    return {"total": total, "available": available}

def fetch_job_defaults(name):
    data = {
        "template_name": name
    }
    try:
        metadata = request_to_server(
            method="get",
            endpoint="/v1/job_defaults",
            params=data,
            server_creds=USER_LOCAL_SERVER_FILE,
            user_cookie=USER_COOKIE
        )
        return metadata
    except Exception as e:
        return {"error": str(e)}
    
def fetch_job_templates(type: str=None):
    data = None
    if type is not None:
        data = {"type": type}
    try:
        templates = request_to_server(
            method="get",
            endpoint="/v1/get_job_templates",
            server_creds=USER_LOCAL_SERVER_FILE,
            data=None,
            params=data,
            user_cookie=USER_COOKIE
        )
        return templates
    except Exception as e:
        return {"error": str(e)}

def fetch_job_names():
    data_groups = [
        {
            "group": "batch.volcano.sh",
            "api_version": "v1alpha1",
            "plural": "jobs"
        },
        {
            "group": "ray.io",
            "api_version": "v1",
            "plural": "rayclusters"
        }
    ]
    try:
        all_jobs = []
        for data in data_groups:
            jobs = request_to_server(
                method="post",
                endpoint="/v1/get_objects_of_type",
                data=data,
                server_creds=USER_LOCAL_SERVER_FILE,
                user_cookie=USER_COOKIE
            )
            for ns, ds in jobs.items():
                all_jobs.extend([Job(owner=ns, name=d["metadata"]["labels"][TEMPLATE_LABEL]) for d in ds["items"]])
            
    except Exception as e:
        return {"error": str(e)}
    
    return all_jobs  

def fetch_job_details(force_namespace=None):
    """Get jobs overview details (status and services)"""
    job_details = []
    # fetch all details at once
    data = {"labels": [TEMPLATE_LABEL]}
    if force_namespace is not None:
        data["force_namespace"] = force_namespace
    result = request_to_server(
        method="post",
        endpoint="/v1/get_jobs_overview",
        data=data,
        server_creds=USER_LOCAL_SERVER_FILE,
        user_cookie=USER_COOKIE)

    for namespace, deployments in result.items():
        """deployments --> "matched_label_value": {"pods": [], "services": []} }"""
        print("Fetch job details namespace", namespace)
        for job_name, job in deployments.items():
            print("Job name", job_name)
            workers_status = defaultdict(int)
            restart_counts = 0
            host_nodes = set()
            # parse pods
            if "pods" in job and job["pods"] is not None:
                for name, values in job["pods"].items():
                    if "conditions" in values and values["conditions"] is not None:
                        restart_counts = sum([c["restart_count"] for c in values["conditions"]])
                    workers_status[values["status"]] += 1
                    # get nodes involved in deployment (needs kubewatcher)
                    if "node_name" in values and values["node_name"] is not None:
                        host_nodes.add(values["node_name"])
                    workers = "\n".join([f"{k}: {v}" for k, v in workers_status.items()])
                    if restart_counts > 0:
                        workers += f"\n({restart_counts} restart)"
            else:
                print("Skip pods")
            # parse services
            node_ports = []
            if "services" in job and job["services"] is not None:
                for name, values in job["services"].items():
                    node_ports.extend(
                        [f"{port['node_port']}" for port in values["ports"]]
                    )
            else:
                print("Skip service")
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
                    name=job_name,
                    workers=workers,
                    endpoint="\n".join(urls),
                    status=str(status),
                    host_nodes=" ".join(host_nodes))
            )
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
    return fetch_pod_logs(
        label_key=TEMPLATE_LABEL,
        label_value=job_name,
        pod_name=pod_name,
        force_namespace=force_namespace,
        tail=tail
    )

def fetch_pod_logs(label_key, label_value, force_namespace=None, pod_name=None, tail=100):
    data = {
        "label": label_key,
        "value": label_value,
        "tail_lines": tail
    }
    if force_namespace is not None:
        data["force_namespace"] = force_namespace
    try:
        # send tail as parameter (fetch only last _tail_ lines)
        all_logs = request_to_server(
            method="post",
            endpoint="/v1/get_job_details",
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
                row_gpus.append( (f"{gpu['model']} ({gpu['memory']} vRAM)", str(status)))
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
        return {"status": True, "data": data}
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
        node_name = socket.gethostname()
    
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

def generate_worker_package(
        target_platform="amd64",
        num_gpus=0,
        node_name=None,
        ip_address="0.0.0.0",
        storage_compatible=True,
        mode=TokenType.WORKER
):
    # get pool data from token  
    token = get_pool_token(mode=mode)
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
        target_platform=target_platform,
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


def join_pool(
        token,
        num_gpus=None,
        node_name=None,
        ip_address=None,
        target_platform="amd64",
        mtu="",
        node_labels={},
        is_seed=False
):
    compatibility = check_worker_compatibility()
    if len(compatibility["issues"]) > 0:
        return {"error": compatibility["issues"]}

    if num_gpus is None:
        num_gpus = get_max_gpus()

    if node_name is None:
        node_name = socket.gethostname()
    
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
        **node_labels,
        STORAGE_CLASS_LABEL: is_storage_compatible(),
        NODE_ROLE_LABEL: "worker" if not is_seed else "server"
    }  
    # local agent join
    # Generate docker compose recipe
    generate_compose_config(
        target_platform=target_platform,
        role="agent" if not is_seed else "seed",
        node_ip_address=ip_address,
        pool_ip=f"https://{kalavai_seed_ip}:6443",
        pool_token=kalavai_token,
        num_gpus=num_gpus,
        vpn_token=public_location,
        mtu=mtu,
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
    cluster_name: str=None,
    ip_address: str=None,
    lb_ip_address: str=None,
    location: str=None,
    target_platform: str="amd64",
    watcher_image_tag: str=None,
    pool_config_file: str=None,
    description: str="",
    token_mode: TokenType=TokenType.USER,
    num_gpus: int=-1,
    node_name: str=None,
    mtu: str="",
    apps: list=[],
    node_labels: dict={}
):

    if not check_seed_compatibility():
        return {"error": "Requirements failed"}
    
    if pool_config_file is None:
        pool_config_file = DEFAULT_POOL_CONFIG_TEMPLATE

    if node_name is None:
        node_name = socket.gethostname()

    user_id = load_user_id()
    
    node_labels = {
        **node_labels,
        STORAGE_CLASS_LABEL: is_storage_compatible(),
        NODE_ROLE_LABEL: "server"
    }
        
    if num_gpus < 0:
        num_gpus = get_max_gpus()

    # load values from pool config
    with open(pool_config_file, "r") as f:
        config_values = yaml.safe_load(f)
    # use default values if not provided
    try:
        watcher_image_tag = config_values["server"]["watcher_image_tag"] if watcher_image_tag is None else watcher_image_tag
        cluster_name = config_values["server"]["name"] if cluster_name is None else cluster_name
        ip_address = config_values["server"]["ip_address"] if ip_address is None else ip_address
        location = config_values["server"]["location"] if location is None else location
        target_platform = config_values["server"]["platform"] if target_platform is None else target_platform
        mtu = config_values["server"]["mtu"] if mtu == "" or mtu is None else mtu
        app_values = config_values["core"]
        post_config_values = config_values["pool"]
        deploy_apps = {
            f"deploy_{app}": True for app in config_values["core"]["deploy"]
        }
        for app in apps:
            deploy_apps[f"deploy_{app}"] = True
    except Exception as e:
        return {"error": f"Error when loading pool config. Missing format? {str(e)}"}

    # Generate docker compose recipe
    if ip_address is None:
        ip_address = "0.0.0.0"
    generate_compose_config(
        target_platform=target_platform,
        role="server",
        vpn_token=location,
        node_ip_address=ip_address,
        lb_ip_address=lb_ip_address,
        num_gpus=num_gpus,
        node_name=node_name,
        node_labels=node_labels,
        mtu=mtu,
        host_root_path=config_values["server"]["host_root_path"]
    )

    # start server
    CLUSTER.start_seed_node()
    while not CLUSTER.is_agent_running():
        time.sleep(10)
    
    
    # select IP address (for external discovery)
    if ip_address is None or location is not None:
        # load VPN ip
        ip_address = None
        while ip_address is None or len(ip_address) == 0:
            ip_address = CLUSTER.get_vpn_ip()
            time.sleep(10)

    # populate local cred files
    auth_key = user_id if user_id is not None else str(uuid.uuid4())
    write_auth_key = str(uuid.uuid4())
    readonly_auth_key = str(uuid.uuid4())
    watcher_service = f"{ip_address}:{DEFAULT_WATCHER_PORT}"
    values = {
        #CLUSTER_NAME_KEY: cluster_name,
        CLUSTER_IP_KEY: ip_address if lb_ip_address is None else lb_ip_address,
        USER_ID_KEY: user_id if user_id is not None else "",
        AUTH_KEY: auth_key,
        READONLY_AUTH_KEY: readonly_auth_key,
        WRITE_AUTH_KEY: write_auth_key,
        WATCHER_PORT_KEY: DEFAULT_WATCHER_PORT,
        WATCHER_SERVICE_KEY: watcher_service,
        USER_NODE_LABEL_KEY: USER_NODE_LABEL,
        WATCHER_IMAGE_TAG_KEY: watcher_image_tag,
        ALLOW_UNREGISTERED_USER_KEY: True # Change this if only registered users are allowed
    }

    store_server_info(
        server_ip=ip_address if lb_ip_address is None else lb_ip_address,
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
        values={**values, **deploy_apps, **app_values},
        #default_values_path=app_values,
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
    
    # wait until the server is ready to create objects
    while True:
        time.sleep(30)
        if is_watcher_alive(server_creds=USER_LOCAL_SERVER_FILE, user_cookie=USER_COOKIE):
            break

    result = pool_init(config_values=post_config_values)
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

def update_pool(debug=True):
    try:
        CLUSTER.validate_cluster()
    except Exception as e:
        return {"error": f"Problems with your pool: {str(e)}"}
    
    if not CLUSTER.is_seed_node():
        return {"error": "You can only update a pool from the seed node."}
    
    # update dependencies
    try:
        CLUSTER.update_dependencies(debug=debug)
        return {"success": "Pool updating. Expect some downtime on core services"}
    except Exception as e:
        return {"error": f"[red]Error when updating pool: {str(e)}"}


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

def pool_init(config_values=None):
    """Deploy configured objects to initialise pool"""
    if config_values is None:
        return
    
    # load template config and populate with values
    sidecar_template_yaml = load_template(
        template_path=POOL_CONFIG_TEMPLATE,
        values=config_values)

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

def add_node_labels(node_name: str, labels: dict):
    """
    Add labels to a node in the cluster.
    
    Args:
        node_name (str): Name of the node to label
        labels (dict): Dictionary of labels to add to the node
        
    Returns:
        dict: Result of the operation with either success or error message
    """
    data = {
        "node_name": node_name,
        "labels": labels
    }
    try:
        result = request_to_server(
            method="post",
            endpoint="/v1/add_labels_to_node",
            data=data,
            server_creds=USER_LOCAL_SERVER_FILE,
            user_cookie=USER_COOKIE
        )
        if "error" in result:
            return {"error": result["error"]}
        else:
            return {"success": result}

    except Exception as e:
        return {"error": f"Error when adding labels to node {node_name}: {str(e)}"}

def get_node_labels(node_names: list[str]):
    """
    Get labels for specified nodes in the cluster.
    
    Args:
        node_names (list[str]): List of node names to fetch labels from
        
    Returns:
        dict: Result containing the labels for each node or error message
    """
    data = {
        "node_names": node_names
    }
    try:
        result = request_to_server(
            method="post",
            endpoint="/v1/get_node_labels",
            data=data,
            server_creds=USER_LOCAL_SERVER_FILE,
            user_cookie=USER_COOKIE
        )
        if result is not None:
            return {"labels": result}
        else:
            return {"error": "Failed to fetch node labels"}
    except Exception as e:
        return {"error": f"Error when fetching node labels: {str(e)}"}
