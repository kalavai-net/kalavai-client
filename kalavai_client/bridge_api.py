"""
Core kalavai service.
Used as a bridge between the kalavai-client app and the reflex frontend
"""
from fastapi import FastAPI
import uvicorn

from kalavai_client.bridge_models import (
    CreatePoolRequest,
    JoinPoolRequest,
    StopPoolRequest,
    DeployJobRequest,
    DeleteJobRequest,
    JobDetailsRequest,
    DeleteNodesRequest
)
from kalavai_client.core import (
    create_pool,
    join_pool,
    attach_to_pool,
    stop_pool,
    fetch_devices,
    fetch_resources,
    fetch_job_names,
    fetch_gpus,
    fetch_job_details,
    fetch_job_logs,
    fetch_job_templates,
    fetch_job_defaults,
    deploy_job,
    delete_job,
    authenticate_user,
    load_user_session,
    user_logout,
    is_connected,
    list_available_pools,
    is_agent_running,
    is_server,
    pause_agent,
    resume_agent,
    get_ip_addresses,
    get_pool_token,
    delete_nodes,
    TokenType
)

app = FastAPI()

@app.post("/create_pool")
def pool_create(request: CreatePoolRequest):
    result = create_pool(
        cluster_name=request.cluster_name,
        ip_address=request.ip_address,
        app_values=request.app_values,
        num_gpus=request.num_gpus,
        node_name=request.node_name,
        only_registered_users=request.only_registered_users,
        location=request.location
    )
    return result

@app.post("/join_pool")
def pool_join(request: JoinPoolRequest):
    result = join_pool(
        token=request.token,
        num_gpus=request.num_gpus,
        node_name=request.node_name
    )
    return result

@app.post("/attach_to_pool")
def pool_attach(request: JoinPoolRequest):
    result = attach_to_pool(
        token=request.token,
        node_name=request.node_name
    )
    return result

@app.post("/stop_pool")
def pool_stop(request: StopPoolRequest):
    result = stop_pool(
        skip_node_deletion=request.skip_node_deletion
    )
    return result

@app.post("/delete_nodes")
def device_delete(request: DeleteNodesRequest):
    result = delete_nodes(
        nodes=request.nodes
    )
    return result

@app.get("/get_pool_token")
def devices(mode: int):

    return get_pool_token(mode=TokenType(mode))

@app.get("/fetch_devices")
def devices():
    return fetch_devices()

@app.get("/fetch_resources")
def resources():
    return fetch_resources()

@app.get("/fetch_job_names")
def job_names():
    return fetch_job_names()

@app.get("/fetch_gpus")
def gpus(available: bool = False):
    return fetch_gpus(available=available)

@app.post("/fetch_job_details")
def job_details(request: JobDetailsRequest):
    return fetch_job_details(jobs=request.jobs)

@app.get("/fetch_job_logs")
def job_logs(job_name: str, force_namespace: str=None, pod_name: str=None, tail: int=100):
    return fetch_job_logs(
        job_name=job_name,
        force_namespace=force_namespace,
        pod_name=pod_name,
        tail=tail
    )

@app.get("/fetch_job_templates")
def job_templates():
    return fetch_job_templates()

@app.get("/fetch_job_defaults")
def job_templates(name: str):
    return fetch_job_defaults(name=name)

@app.post("/deploy_job")
def job_deploy(request: DeployJobRequest):
    result = deploy_job(
        template_name=request.template_name,
        values_dict=request.values,
        force_namespace=request.force_namespace
    )
    return result

@app.post("/delete_job")
def job_delete(request: DeleteJobRequest):
    result = delete_job(
        name=request.name,
        force_namespace=request.force_namespace
    )
    return result

@app.get("/authenticate_user")
def user_authenticate(username: str, password: str):
    result = authenticate_user(
        username=username,
        password=password
    )
    return result

@app.get("/load_user_session")
def user_session():
    result = load_user_session()
    return result

@app.get("/user_logout")
def logout_user():
    result = user_logout()
    return result

@app.get("/is_connected")
def pool_connected():
    result = is_connected()
    return result

@app.get("/is_agent_running")
def agent_running():
    result = is_agent_running()
    return result

@app.get("/is_server")
def server():
    result = is_server()
    return result

@app.post("/pause_agent")
def agent_pause():
    result = pause_agent()
    return result

@app.post("/resume_agent")
def agent_resume():
    result = resume_agent()
    return result

@app.get("/get_ip_addresses")
def ip_addresses(subnet: str=None):
    result = get_ip_addresses(subnet=subnet)
    return result

@app.get("/list_available_pools")
def pool_connected(user_only: bool=False):
    result = list_available_pools(user_only=user_only)
    return result


def run_api(host="0.0.0.0", port=8001, log_level="critical"):
    uvicorn.run(
        app,
        host=host,
        port=port,
        log_level=log_level
    )

if __name__ == "__main__":
    run_api()
    