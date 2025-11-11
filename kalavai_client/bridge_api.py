"""
Core kalavai service.
Used as a bridge between the kalavai-client app and the reflex frontend
"""
from fastapi import FastAPI, HTTPException, Depends, Query, Body
from typing import Optional, List
from fastapi_mcp import FastApiMCP
from starlette.requests import Request
import uvicorn

from kalavai_client.core import Job
from kalavai_client.env import (
    KALAVAI_SERVICE_LABEL,
    KALAVAI_SERVICE_LABEL_VALUE
)
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
    WorkerConfigRequest
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
    fetch_pod_logs,
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
    generate_worker_package,
    TokenType
)
from kalavai_client.utils import (
    load_user_id,
    extract_auth_token
)

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
    api_key = extract_auth_token(headers=request.headers)
    if api_key != user_id:
        raise HTTPException(status_code=401, detail="Request requires API Key")
    return api_key

@app.post("/create_pool", 
    operation_id="create_pool",
    summary="Create a new Kalavai compute pool",
    tags=["pool_management"],
    description="Creates a new distributed compute pool that allows multiple nodes to join and share GPU resources. The pool acts as a Kubernetes cluster where users can deploy and manage machine learning jobs across multiple devices.",
    response_description="Result of pool creation")
def pool_create(request: CreatePoolRequest, api_key: str = Depends(verify_api_key)):
    """
    Create a new pool with the following parameters:
    
    - **cluster_name**: Name of the cluster
    - **ip_address**: IP address for the pool
    - **num_gpus**: Number of GPUs to allocate
    - **node_name**: Name of the node
    - **location**: Location of the pool
    - **description**: Pool description
    - **token_mode**: Token type for authentication
    """
    result = create_pool(
        cluster_name=request.cluster_name,
        ip_address=request.ip_address,
        num_gpus=request.num_gpus,
        node_name=request.node_name,
        location=request.location,
        description=request.description,
        token_mode=request.token_mode
    )
    return result

@app.post("/join_pool",
    operation_id="join_pool",
    summary="Join an existing Kalavai pool as a compute node",
    description="Joins a running Kalavai pool by providing a valid join token. This endpoint registers the current machine as a compute node in the pool, making its GPU resources available for job scheduling. The node will receive workloads based on the pool's scheduling policy.",
    tags=["pool_management"],
    response_description="Result of joining the pool")
def pool_join(request: JoinPoolRequest, api_key: str = Depends(verify_api_key)):
    """
    Join a pool with the following parameters:
    
    - **token**: Pool join token
    - **ip_address**: IP address for the node
    - **node_name**: Name of the node
    - **num_gpus**: Number of GPUs to allocate
    """
    result = join_pool(
        token=request.token,
        num_gpus=request.num_gpus,
        node_name=request.node_name,
        ip_address=request.ip_address
    )
    return result

@app.post("/attach_to_pool",
    operation_id="attach_to_pool",
    summary="Attach to a pool for management purposes",
    description="Attaches to an existing Kalavai pool for administrative and monitoring purposes without contributing compute resources. This is typically used by frontend applications or management tools that need to interact with the pool but don't provide GPU resources.",
    tags=["pool_management"],
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
    operation_id="stop_pool",
    summary="Stop and clean up the current Kalavai pool",
    description="Gracefully shuts down the current Kalavai pool, terminating all running jobs and optionally removing all compute nodes from the cluster. This operation is irreversible and will disconnect all nodes from the pool.",
    tags=["pool_management"],
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
    operation_id="delete_nodes",
    summary="Remove specific nodes from the pool",
    description="Removes specified compute nodes from the Kalavai pool. This operation will terminate any jobs running on the target nodes and clean up their resources. Use with caution as it may interrupt running workloads.",
    tags=["pool_management"],
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
    operation_id="cordon_nodes",
    summary="Mark nodes as unschedulable",
    description="Marks specified nodes as unschedulable, preventing new jobs from being assigned to them while allowing existing jobs to complete. This is useful for maintenance operations or when you want to gradually remove nodes from the pool.",
    tags=["pool_management"],
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
    operation_id="uncordon_nodes",
    summary="Mark nodes as schedulable again",
    description="Re-enables job scheduling on previously cordoned nodes, allowing them to receive new workloads. This reverses the effect of the cordon operation.",
    tags=["pool_management"],
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
    operation_id="get_pool_token",
    summary="Generate a token for pool access",
    description="Generates a secure token that can be used to join or attach to the current Kalavai pool. Different token types provide different levels of access - join tokens allow nodes to contribute resources, while attach tokens allow management access.",
    tags=["auth"],
    response_description="Pool token")
def get_token(mode: int, api_key: str = Depends(verify_api_key)):
    """
    Get pool token with the following parameters:
    
    - **mode**: Token type mode
    """
    return get_pool_token(mode=TokenType(mode))

@app.post("/generate_worker_config",
    operation_id="generate_worker_config",
    summary="Generate a config file for a remote worker to connect to the pool",
    description="Generate a config file for a remote worker to connect to the pool. Different token types provide different levels of access - join tokens allow nodes to contribute resources, while attach tokens allow management access.",
    tags=["pool_management"],
    response_description="Worker config file")
def generate_worker_config(request: WorkerConfigRequest, api_key: str = Depends(verify_api_key)):
    return generate_worker_package(
        node_name=request.node_name,
        mode=TokenType(request.mode),
        target_platform=request.target_platform,
        num_gpus=request.num_gpus,
        ip_address=request.ip_address,
        storage_compatible=request.storage_compatible)

@app.get("/fetch_devices",
    operation_id="fetch_devices",
    summary="Get list of all compute devices in the pool",
    description="Retrieves information about all compute devices (nodes) currently connected to the Kalavai pool, including their status, available resources, and current workload distribution.",
    tags=["info"],
    response_description="List of devices")
def get_devices(api_key: str = Depends(verify_api_key)):
    """Get list of available devices"""
    return fetch_devices()

@app.get("/fetch_service_logs",
    operation_id="fetch_service_logs",
    summary="Get logs for the kalavai API service",
    description="Get logs for the kalavai API service, including internal logs, debugging messages and status of the service.",
    tags=["info"],
    response_description="Logs")
def get_service_logs(tail: int=100, api_key: str = Depends(verify_api_key)):
    return fetch_pod_logs(label_key=KALAVAI_SERVICE_LABEL, label_value=KALAVAI_SERVICE_LABEL_VALUE, force_namespace="kalavai", tail=tail)

@app.post("/send_pool_invites",
    operation_id="send_pool_invites",
    summary="Send invitations to join the pool",
    description="Sends invitations to potential users or nodes to join the current Kalavai pool. Invitees will receive tokens that allow them to connect to the pool and contribute their resources.",
    tags=["avoid"],
    response_description="Result of sending invites")
def send_pool_invites(request: InvitesRequest, api_key: str = Depends(verify_api_key)):
    """
    Send pool invites with the following parameters:
    
    - **invitees**: List of invitee identifiers
    """
    return send_invites(invitees=request.invitees)

@app.get("/fetch_resources",
    operation_id="fetch_resources",
    summary="Get resource utilization for specific nodes",
    description="Retrieves detailed resource information (CPU, memory, GPU usage) for the pool; optionally for a list of specified nodes in the pool (as {'nodes': node_list}). This helps monitor resource utilization and plan workload distribution.",
    tags=["info"],
    response_description="Resource information")
def resources(request: Optional[NodesActionRequest]=NodesActionRequest(), api_key: str = Depends(verify_api_key)):
    """Get available resources"""
    return fetch_resources(node_names=request.nodes)

@app.get("/fetch_job_names",
    operation_id="fetch_job_names",
    summary="Get list of all jobs (model deployments) in the pool",
    description="Retrieves the names of all jobs and models currently deployed or scheduled in the Kalavai pool. This provides an overview of all workloads in the system.",
    tags=["info"],
    response_description="List of job names")
def job_names(api_key: str = Depends(verify_api_key)):
    """Get list of job names"""
    return fetch_job_names()

@app.get("/fetch_gpus",
    operation_id="fetch_gpus",
    summary="Get GPU information across the pool",
    description="Retrieves detailed information about all GPUs in the Kalavai pool, including their availability status, current utilization, and which jobs are using them. Can filter to show only available GPUs.",
    tags=["info"],
    response_description="List of GPUs")
def gpus(available: bool = False, api_key: str = Depends(verify_api_key)):
    """
    Get list of GPUs with the following parameters:
    
    - **available**: Whether to show only available GPUs
    """
    return fetch_gpus(available=available)

@app.get("/fetch_job_details",
    operation_id="fetch_job_details",
    summary="Get detailed information about specific job and model deployments",
    description="Retrieves comprehensive information about jobs or models including their status, resource usage, runtime, and configuration. Useful for monitoring and debugging job execution.",
    tags=["info"],
    response_description="Job details")
def job_details(force_namespace: str = Query(None), api_key: str = Depends(verify_api_key)):
    """Get job details"""
    return fetch_job_details(force_namespace=force_namespace)

@app.get("/fetch_job_logs",
    operation_id="fetch_job_logs",
    summary="Get execution logs for a specific job",
    description="Retrieves the execution logs for a specified job, providing real-time or historical output from the job's containers. Useful for debugging, monitoring progress, and understanding job behavior.",
    tags=["info", "avoid"],
    response_description="Job logs")
def job_logs(
    job_name: str,
    force_namespace: str = Query(None),
    pod_name: str = Query(None),
    tail: int = Query(100),
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
    operation_id="fetch_job_templates",
    summary="Get available job templates",
    description="Retrieves a list of all available job templates that can be used to deploy workloads. Templates provide predefined configurations for frameworks.",
    tags=["info"],
    response_description="List of job templates")
def job_templates(api_key: str = Depends(verify_api_key)):
    return fetch_job_templates()

@app.get("/fetch_model_templates",
    operation_id="fetch_model_templates",
    summary="Get available model engines templates",
    description="Retrieves a list of all available model engine templates that can be used to deploy models. Templates provide predefined configurations for model engine frameworks.",
    tags=["info"],
    response_description="List of model engine templates")
def model_templates(api_key: str = Depends(verify_api_key)):
    return fetch_job_templates(type="model")

@app.get("/fetch_job_defaults",
    operation_id="fetch_job_defaults",
    summary="Get default values for a job or model engine template deployment",
    description="Retrieves the default values for a specific job or model engine template deployment. This helps users understand what parameters are required and what their default values are before deploying a job.",
    tags=["info"],
    response_description="Job and model engine default values")
def job_defaults(name: str, api_key: str = Depends(verify_api_key)):
    result = fetch_job_defaults(name=name)
    return result["defaults"]

@app.get("/fetch_job_metadata",
    operation_id="fetch_job_metadata",
    summary="Get metadata with information about a given job or model engine template deployment",
    description="Retrieves the metadata associated with a specific job or model engine template deployment. This helps users understand what the template can be used for.",
    tags=["info"],
    response_description="Job and model engine metadata values")
def job_metadata(name: str, api_key: str = Depends(verify_api_key)):
    result = fetch_job_defaults(name=name)
    return result["metadata"]

@app.get("/fetch_job_rules",
    operation_id="fetch_job_rules",
    summary="Get the rules associated with the use of a given job or model engine template",
    description="Retrieves the rules associated with a specific job or model engine template deployment. This helps users and AI agents determine if a given model engine template is adequate for the task.",
    tags=["info"],
    response_description="Job and model engine rules")
def job_rules(name: str, api_key: str = Depends(verify_api_key)):
    result = job_metadata(name=name)
    return result["template_rules"]

@app.get("/fetch_job_values_rules",
    operation_id="fetch_job_values_rules",
    summary="Get information on how to provide values to the parameters of a specific job or model engine template",
    description="Retrieves information necessary to fill up the values required to deploy a specific job or model engine template. This helps users and AI agents generate the values dictionary for a job or model engine template deployment.",
    tags=["info"],
    response_description="Job and model engine info for values")
def job_values_rules(name: str, api_key: str = Depends(verify_api_key)):
    result = job_metadata(name=name)
    return result["values_rules"]

@app.post("/deploy_job",
    operation_id="deploy_job",
    summary="Deploy a new job to the pool",
    description="Deploys a new job to the Kalavai pool using a specified template and configuration. The job will be scheduled on appropriate nodes based on resource availability and any specified target labels.",
    tags=["job_management"],
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
    operation_id="delete_job",
    summary="Terminate and remove a job from the pool",
    description="Terminates a running job and removes it from the Kalavai pool. This will stop all containers associated with the job and free up the resources they were using.",
    tags=["job_management"],
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
    operation_id="authenticate_user",
    summary="Authenticate a user with the Kalavai system",
    description="Authenticates a user against the Kalavai system, establishing their identity and permissions. This is required for accessing pool management features and deploying jobs.",
    tags=["info", "auth"],
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
    operation_id="load_user_session",
    summary="Load current user session information",
    description="Retrieves information about the currently authenticated user's session, including their identity, permissions, and any active connections to pools.",
    tags=["info", "auth"],
    response_description="User session information")
def user_session(api_key: str = Depends(verify_api_key)):
    """Load the current user session"""
    result = load_user_session()
    return result

@app.get("/user_logout",
    operation_id="user_logout",
    summary="Log out the current user",
    description="Terminates the current user's session and clears authentication credentials. This should be called when the user is done using the system to ensure proper cleanup.",
    tags=["auth"],
    response_description="Logout result")
def logout_user():
    """Log out the current user"""
    result = user_logout()
    return result

@app.get("/is_connected",
    operation_id="is_connected",
    summary="Check if connected to a Kalavai pool",
    description="Verifies whether the current instance is connected to a Kalavai pool. Returns connection status and pool information if connected.",
    tags=["agent_management"],
    response_description="Connection status")
def pool_connected():
    """Check if connected to a pool"""
    result = is_connected()
    return result

@app.get("/is_agent_running",
    operation_id="is_agent_running",
    summary="Check if the Kalavai agent is running",
    description="Verifies whether the Kalavai agent service is currently running on this machine. The agent is responsible for managing pool connections and job execution.",
    tags=["agent_management"],
    response_description="Agent status")
def agent_running():
    """Check if the agent is running"""
    result = is_agent_running()
    return result

@app.get("/is_server",
    operation_id="is_server",
    summary="Check if running as a pool server",
    description="Determines whether this instance is running as a Kalavai pool server (coordinator) or as a client node. Server instances manage the pool while client instances contribute resources.",
    tags=["agent_management"],
    response_description="Server status")
def server():
    """Check if running as server"""
    result = is_server()
    return result

@app.post("/pause_agent",
    operation_id="pause_agent",
    summary="Pause the Kalavai agent service",
    description="Temporarily pauses the Kalavai agent, stopping it from accepting new jobs or participating in pool operations. Existing jobs will continue running until completion.",
    tags=["agent_management"],
    response_description="Result of pausing agent")
def agent_pause():
    """Pause the agent"""
    result = pause_agent()
    return result

@app.post("/resume_agent",
    operation_id="resume_agent",
    summary="Resume the Kalavai agent service",
    description="Resumes the previously paused Kalavai agent, allowing it to accept new jobs and participate in pool operations again.",
    tags=["agent_management"],
    response_description="Result of resuming agent")
def agent_resume():
    """Resume the agent"""
    result = resume_agent()
    return result

@app.get("/get_ip_addresses",
    operation_id="get_ip_addresses",
    summary="Get available IP addresses for pool configuration",
    description="Retrieves a list of available IP addresses that can be used for pool configuration. Optionally filters by subnet to help with network planning and pool setup.",
    tags=["agent_management"],
    response_description="List of IP addresses")
def ip_addresses(subnet: str = None, api_key: str = Depends(verify_api_key)):
    """
    Get IP addresses with the following parameters:
    
    - **subnet**: Optional subnet to filter by
    """
    result = get_ip_addresses(subnet=subnet)
    return result

@app.get("/list_available_pools",
    operation_id="list_available_pools",
    summary="List all available Kalavai pools",
    description="Retrieves a list of all Kalavai pools that are currently available for connection. Can filter to show only pools owned by the current user or all public pools.",
    tags=["agent_management"],
    response_description="List of available pools")
def pool_connected(user_only: bool = False, api_key: str = Depends(verify_api_key)):
    """
    List available pools with the following parameters:
    
    - **user_only**: Whether to show only user's pools
    """
    result = list_available_pools(user_only=user_only)
    return result

@app.post("/add_node_labels",
    operation_id="add_node_labels",
    summary="Add custom labels to a compute node",
    description="Adds custom labels to a specific compute node in the pool. Labels can be used for job scheduling, resource allocation, and organizational purposes. Labels are key-value pairs that help categorize and identify nodes.",
    tags=["pool_management"],
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

@app.get("/get_node_labels",
    operation_id="get_node_labels",
    summary="Get labels for specified compute nodes",
    description="Retrieves all labels associated with specified compute nodes in the pool. Labels provide metadata about nodes and can be used for filtering and scheduling decisions.",
    tags=["info"],
    response_description="Node labels")
def node_labels_get(nodes: Optional[List[str]] = Query(None), api_key: str = Depends(verify_api_key)):
    """
    Get node labels with the following parameters:
    
    - **nodes**: List of node names to get labels for
    """
    result = get_node_labels(
        node_names=nodes
    )
    return result

### BUILD MCP WRAPPER ###
mcp = FastApiMCP(
    app,
    name="Protected MCP",
    #exclude_operations=[],
    exclude_tags=[
        "auth",
        "agent_management",
        "job_management",
        "pool_management",
        "avoid"
    ]
)
mcp.mount()
##########################


def run_api(host="0.0.0.0", port=8001, log_level="critical"):
    uvicorn.run(
        app,
        host=host,
        port=port,
        log_level=log_level
    )

if __name__ == "__main__":
    run_api()
    