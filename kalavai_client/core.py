from collections import defaultdict
import math

from pydantic import BaseModel

from kalavai_client.utils import (
    request_to_server,
    load_server_info
)
from kalavai_client.env import (
    USER_COOKIE,
    USER_LOCAL_SERVER_FILE,
    TEMPLATE_LABEL,
    SERVER_IP_KEY
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