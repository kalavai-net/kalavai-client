"""
Core kalavai service.
Used as a bridge between the kalavai-client app and the reflex frontend
"""
from fastapi import FastAPI, HTTPException, Depends
from starlette.requests import Request
import uvicorn

from kalavai_client.bridge_models import (
    CreatePoolRequest,
    InvitesRequest,
    JoinPoolRequest,
    StopPoolRequest,
    DeployJobRequest,
    DeleteJobRequest,
    JobDetailsRequest,
    NodesActionRequest,
    NodeLabelsRequest,
    GetNodeLabelsRequest
)
from kalavai_client.core import (
    create_pool,
    join_pool,
    attach_to_pool,
    send_invites,
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
    cordon_nodes,
    uncordon_nodes,
    add_node_labels,
    get_node_labels,
    TokenType
)
from kalavai_client.utils import load_user_id

app = FastAPI(
    title="Kalavai Bridge API",
    description="API for managing Kalavai pools, jobs, and nodes",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
)

################################
## API Key Validation methods ##
################################
async def verify_api_key(request: Request):
    """
    Verify the API key from the request headers.
    The API key must match the user ID.
    """
    user_id = load_user_id()
    if user_id is None:
        return None
    api_key = request.headers.get("X-API-KEY")
    if api_key != user_id:
        raise HTTPException(status_code=401, detail="Request requires API Key")
    return api_key

@app.post("/create_pool", 
    summary="Create a new pool",
    description="Creates a new pool with the specified configuration",
    response_description="Result of pool creation")
def pool_create(request: CreatePoolRequest, api_key: str = Depends(verify_api_key)):
    """
    Create a new pool with the following parameters:
    
    - **cluster_name**: Name of the cluster
    - **ip_address**: IP address for the pool
    - **app_values**: Application configuration values
    - **num_gpus**: Number of GPUs to allocate
    - **node_name**: Name of the node
    - **only_registered_users**: Whether to restrict to registered users
    - **location**: Location of the pool
    - **description**: Pool description
    - **token_mode**: Token type for authentication
    - **frontend**: Whether this is a frontend request
    """
    result = create_pool(
        cluster_name=request.cluster_name,
        ip_address=request.ip_address,
        app_values=request.app_values,
        num_gpus=request.num_gpus,
        node_name=request.node_name,
        only_registered_users=request.only_registered_users,
        location=request.location,
        description=request.description,
        token_mode=request.token_mode,
        frontend=request.frontend
    )
    return result

@app.post("/join_pool",
    summary="Join an existing pool",
    description="Join a pool using a token",
    response_description="Result of joining the pool")
def pool_join(request: JoinPoolRequest, api_key: str = Depends(verify_api_key)):
    """
    Join a pool with the following parameters:
    
    - **token**: Pool join token
    - **ip_address**: IP address for the node
    - **node_name**: Name of the node
    - **num_gpus**: Number of GPUs to allocate
    - **frontend**: Whether this is a frontend request
    """
    result = join_pool(
        token=request.token,
        num_gpus=request.num_gpus,
        node_name=request.node_name,
        ip_address=request.ip_address,
        frontend=request.frontend
    )
    return result

@app.post("/attach_to_pool",
    summary="Attach to an existing pool",
    description="Attach to a pool using a token",
    response_description="Result of attaching to the pool")
def pool_attach(request: JoinPoolRequest, api_key: str = Depends(verify_api_key)):
    """
    Attach to a pool with the following parameters:
    
    - **token**: Pool token
    - **node_name**: Name of the node
    - **frontend**: Whether this is a frontend request
    """
    result = attach_to_pool(
        token=request.token,
        node_name=request.node_name,
        frontend=request.frontend
    )
    return result

@app.post("/stop_pool",
    summary="Stop a pool",
    description="Stop the current pool",
    response_description="Result of stopping the pool")
def pool_stop(request: StopPoolRequest, api_key: str = Depends(verify_api_key)):
    """
    Stop the pool with the following parameters:
    
    - **skip_node_deletion**: Whether to skip node deletion
    """
    result = stop_pool(
        skip_node_deletion=request.skip_node_deletion
    )
    return result

@app.post("/delete_nodes",
    summary="Delete nodes",
    description="Delete specified nodes from the pool",
    response_description="Result of node deletion")
def device_delete(request: NodesActionRequest, api_key: str = Depends(verify_api_key)):
    """
    Delete nodes with the following parameters:
    
    - **nodes**: List of node names to delete
    """
    result = delete_nodes(
        nodes=request.nodes
    )
    return result

@app.post("/cordon_nodes",
    summary="Cordon nodes",
    description="Mark nodes as unschedulable",
    response_description="Result of cordoning nodes")
def device_cordon(request: NodesActionRequest, api_key: str = Depends(verify_api_key)):
    """
    Cordon nodes with the following parameters:
    
    - **nodes**: List of node names to cordon
    """
    result = cordon_nodes(
        nodes=request.nodes
    )
    return result

@app.post("/uncordon_nodes",
    summary="Uncordon nodes",
    description="Mark nodes as schedulable",
    response_description="Result of uncordoning nodes")
def device_uncordon(request: NodesActionRequest, api_key: str = Depends(verify_api_key)):
    """
    Uncordon nodes with the following parameters:
    
    - **nodes**: List of node names to uncordon
    """
    result = uncordon_nodes(
        nodes=request.nodes
    )
    return result

@app.get("/get_pool_token",
    summary="Get pool token",
    description="Get a token for the pool",
    response_description="Pool token")
def get_token(mode: int, api_key: str = Depends(verify_api_key)):
    """
    Get pool token with the following parameters:
    
    - **mode**: Token type mode
    """
    return get_pool_token(mode=TokenType(mode))

@app.get("/fetch_devices",
    summary="Fetch devices",
    description="Get list of available devices",
    response_description="List of devices")
def get_devices(api_key: str = Depends(verify_api_key)):
    """Get list of available devices"""
    return fetch_devices()

@app.post("/send_pool_invites",
    summary="Send pool invites",
    description="Send invites to join the pool",
    response_description="Result of sending invites")
def send_pool_invites(request: InvitesRequest, api_key: str = Depends(verify_api_key)):
    """
    Send pool invites with the following parameters:
    
    - **invitees**: List of invitee identifiers
    """
    return send_invites(invitees=request.invitees)

@app.get("/fetch_resources",
    summary="Fetch resources",
    description="Get available resources",
    response_description="Resource information")
def resources(api_key: str = Depends(verify_api_key)):
    """Get available resources"""
    return fetch_resources()

@app.get("/fetch_job_names",
    summary="Fetch job names",
    description="Get list of job names",
    response_description="List of job names")
def job_names(api_key: str = Depends(verify_api_key)):
    """Get list of job names"""
    return fetch_job_names()

@app.get("/fetch_gpus",
    summary="Fetch GPUs",
    description="Get list of available GPUs",
    response_description="List of GPUs")
def gpus(available: bool = False, api_key: str = Depends(verify_api_key)):
    """
    Get list of GPUs with the following parameters:
    
    - **available**: Whether to show only available GPUs
    """
    return fetch_gpus(available=available)

@app.post("/fetch_job_details",
    summary="Fetch job details",
    description="Get details for specified jobs",
    response_description="Job details")
def job_details(request: JobDetailsRequest, api_key: str = Depends(verify_api_key)):
    """
    Get job details with the following parameters:
    
    - **jobs**: List of jobs to get details for
    """
    return fetch_job_details(jobs=request.jobs)

@app.get("/fetch_job_logs",
    summary="Fetch job logs",
    description="Get logs for a specific job",
    response_description="Job logs")
def job_logs(
    job_name: str,
    force_namespace: str = None,
    pod_name: str = None,
    tail: int = 100,
    api_key: str = Depends(verify_api_key)
):
    """
    Get job logs with the following parameters:
    
    - **job_name**: Name of the job
    - **force_namespace**: Optional namespace override
    - **pod_name**: Optional pod name
    - **tail**: Number of log lines to return
    """
    return fetch_job_logs(
        job_name=job_name,
        force_namespace=force_namespace,
        pod_name=pod_name,
        tail=tail
    )

@app.get("/fetch_job_templates",
    summary="Fetch job templates",
    description="Get available job templates",
    response_description="List of job templates")
def job_templates(api_key: str = Depends(verify_api_key)):
    """Get available job templates"""
    return fetch_job_templates()

@app.get("/fetch_job_defaults",
    summary="Fetch job defaults",
    description="Get default values for a job template",
    response_description="Job default values")
def job_templates(name: str, api_key: str = Depends(verify_api_key)):
    """
    Get job defaults with the following parameters:
    
    - **name**: Name of the job template
    """
    return fetch_job_defaults(name=name)

@app.post("/deploy_job",
    summary="Deploy job",
    description="Deploy a new job",
    response_description="Result of job deployment")
def job_deploy(request: DeployJobRequest, api_key: str = Depends(verify_api_key)):
    """
    Deploy a job with the following parameters:
    
    - **template_name**: Name of the job template
    - **values**: Job configuration values
    - **force_namespace**: Optional namespace override
    - **target_labels**: Optional target node labels
    """
    result = deploy_job(
        template_name=request.template_name,
        values_dict=request.values,
        force_namespace=request.force_namespace,
        target_labels=request.target_labels
    )
    return result

@app.post("/delete_job",
    summary="Delete job",
    description="Delete a job",
    response_description="Result of job deletion")
def job_delete(request: DeleteJobRequest, api_key: str = Depends(verify_api_key)):
    """
    Delete a job with the following parameters:
    
    - **name**: Name of the job to delete
    - **force_namespace**: Optional namespace override
    """
    result = delete_job(
        name=request.name,
        force_namespace=request.force_namespace
    )
    return result

@app.get("/authenticate_user",
    summary="Authenticate user",
    description="Authenticate a user",
    response_description="Authentication result")
def user_authenticate(user_id: str, api_key: str = Depends(verify_api_key)):
    """
    Authenticate user with the following parameters:
    
    - **user_id**: User identifier
    """
    result = authenticate_user(
        user_id=user_id
    )
    return result

@app.get("/load_user_session",
    summary="Load user session",
    description="Load the current user session",
    response_description="User session information")
def user_session(api_key: str = Depends(verify_api_key)):
    """Load the current user session"""
    result = load_user_session()
    return result

@app.get("/user_logout",
    summary="User logout",
    description="Log out the current user",
    response_description="Logout result")
def logout_user():
    """Log out the current user"""
    result = user_logout()
    return result

@app.get("/is_connected",
    summary="Check connection",
    description="Check if connected to a pool",
    response_description="Connection status")
def pool_connected():
    """Check if connected to a pool"""
    result = is_connected()
    return result

@app.get("/is_agent_running",
    summary="Check agent status",
    description="Check if the agent is running",
    response_description="Agent status")
def agent_running():
    """Check if the agent is running"""
    result = is_agent_running()
    return result

@app.get("/is_server",
    summary="Check server status",
    description="Check if running as server",
    response_description="Server status")
def server():
    """Check if running as server"""
    result = is_server()
    return result

@app.post("/pause_agent",
    summary="Pause agent",
    description="Pause the agent",
    response_description="Result of pausing agent")
def agent_pause():
    """Pause the agent"""
    result = pause_agent()
    return result

@app.post("/resume_agent",
    summary="Resume agent",
    description="Resume the agent",
    response_description="Result of resuming agent")
def agent_resume():
    """Resume the agent"""
    result = resume_agent()
    return result

@app.get("/get_ip_addresses",
    summary="Get IP addresses",
    description="Get available IP addresses",
    response_description="List of IP addresses")
def ip_addresses(subnet: str = None, api_key: str = Depends(verify_api_key)):
    """
    Get IP addresses with the following parameters:
    
    - **subnet**: Optional subnet to filter by
    """
    result = get_ip_addresses(subnet=subnet)
    return result

@app.get("/list_available_pools",
    summary="List available pools",
    description="Get list of available pools",
    response_description="List of available pools")
def pool_connected(user_only: bool = False, api_key: str = Depends(verify_api_key)):
    """
    List available pools with the following parameters:
    
    - **user_only**: Whether to show only user's pools
    """
    result = list_available_pools(user_only=user_only)
    return result

@app.post("/add_node_labels",
    summary="Add node labels",
    description="Add labels to a node",
    response_description="Result of adding labels")
def node_labels(request: NodeLabelsRequest, api_key: str = Depends(verify_api_key)):
    """
    Add node labels with the following parameters:
    
    - **node_name**: Name of the node
    - **labels**: Dictionary of labels to add
    """
    result = add_node_labels(
        node_name=request.node_name,
        labels=request.labels
    )
    return result

@app.post("/get_node_labels",
    summary="Get node labels",
    description="Get labels for specified nodes",
    response_description="Node labels")
def node_labels_get(request: GetNodeLabelsRequest, api_key: str = Depends(verify_api_key)):
    """
    Get node labels with the following parameters:
    
    - **node_names**: List of node names to get labels for
    """
    result = get_node_labels(
        node_names=request.node_names
    )
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
    