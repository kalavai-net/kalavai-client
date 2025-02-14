import os
import time
from collections import defaultdict
import math
import uuid
import socket

from pydantic import BaseModel

from kalavai_client.cluster import CLUSTER
from kalavai_client.utils import (
    request_to_server,
    load_server_info,
    decode_dict,
    get_vpn_details,
    validate_join_public_seed,
    generate_compose_config,
    store_server_info,
    is_watcher_alive,
    run_cmd,
    leave_vpn,
    safe_remove,
    NODE_NAME_KEY,
    MANDATORY_TOKEN_FIELDS,
    PUBLIC_LOCATION_KEY,
    CLUSTER_IP_KEY,
    CLUSTER_NAME_KEY,
    AUTH_KEY,
    WATCHER_SERVICE_KEY
)
from kalavai_client.auth import (
    KalavaiAuthClient
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
    USER_TEMPLATES_FOLDER
)

class Job(BaseModel):
    owner: str = None
    name: str = None
    workers: str = None
    endpoint: str = None
    status: str = None

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
            if "Ready" in workers_status and len(workers_status) == 1:
                status = "running"
            elif any([st in workers_status for st in ["Failed", "Completed"]]):
                status = "error"
            else:
                status = "pending"
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

def deploy_job(template_name, values_dict, force_namespace=None):

    # deploy template with kube-watcher
    data = {
        "template": template_name,
        "template_values": values_dict
    }
    if force_namespace is not None:
        data["force_namespace"] = force_namespace

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
        return {pod: logs for pod, logs in all_logs.items() if pod_name is None or pod_name == pod}

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

def load_user_session():
    auth = KalavaiAuthClient(
        user_cookie_file=USER_COOKIE
    )
    return auth.load_user_session()
    
def authenticate_user(username=None, password=None):
    auth = KalavaiAuthClient(
        user_cookie_file=USER_COOKIE
    )
    user = auth.load_user_session()
    if user is None:
        user = auth.login(username=username, password=password)
    
    if user is None:
        return {"error": "Username or password incorrect"}
    return user

def user_logout():
    auth = KalavaiAuthClient(
        user_cookie_file=USER_COOKIE
    )
    auth.logout()
    return True

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
        vpn = defaultdict(lambda: None)
    except Exception as e:
        return {"error": f"Invalid token. {str(e)}"} 
    
    user = defaultdict(lambda: None)
    if public_location is not None:
        user = load_user_session()
        if user is None:
            return {"error ": "Must be logged in to join public pools"}
        try:
            vpn = get_vpn_details(
                location=public_location,
                user_cookie=USER_COOKIE)
        except Exception as e:
            return {"error": f"Are you authenticated? {str(e)}"}
        try:
            validate_join_public_seed(
                cluster_name=cluster_name,
                join_key=token,
                user_cookie=USER_COOKIE
            )
        except Exception as e:
            return {"error": f"Error when joining network: {str(e)}"}
        
    # local agent join
    # 1. Generate local cache files
    # Generate docker compose recipe
    generate_compose_config(
        role="",
        vpn_token=vpn["key"],
        node_name=node_name,
        is_public=public_location is not None)
    
    store_server_info(
        server_ip=kalavai_seed_ip,
        auth_key=auth_key,
        file=USER_LOCAL_SERVER_FILE,
        watcher_service=watcher_service,
        node_name=node_name,
        cluster_name=cluster_name,
        public_location=public_location,
        user_api_key=user["api_key"])
    
    run_cmd(f"docker compose -f {USER_COMPOSE_FILE} up -d")
    # ensure we are connected
    while True:
        time.sleep(30)
        if is_watcher_alive(server_creds=USER_LOCAL_SERVER_FILE, user_cookie=USER_COOKIE):
            break

    return cluster_name

def is_connected():
    if not os.path.isfile(USER_LOCAL_SERVER_FILE):
        return False
    return is_watcher_alive(server_creds=USER_LOCAL_SERVER_FILE, user_cookie=USER_COOKIE)

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
    
    # disconnect from VPN first, then remove agent, then remove local files
    try:
        vpns = leave_vpn(container_name=DEFAULT_VPN_CONTAINER_NAME)
        if vpns is not None:
            for vpn in vpns:
                logs.append(f"You have left {vpn} VPN")
    except:
        # no vpn
        pass

    CLUSTER.remove_agent()

    # clean local files
    cleanup_local()

    return logs