from pydantic import BaseModel, Field
from typing import List, Dict, Union, Optional, Literal
from enum import Enum


class Job(BaseModel):
    job_id: Optional[str] = None
    spec: Optional[dict] = {}
    conditions: Optional[dict] = {}
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

class TokenType(str, Enum):
    ADMIN = "admin"
    USER = "user"
    WORKER = "worker"

class CreatePoolRequest(BaseModel):
    cluster_name: str = Field(description="Name of the cluster to create")
    ip_address: str = Field(description="IP address for the pool")
    num_gpus: int = Field(None, description="Number of GPUs to allocate")
    node_name: str = Field(None, description="Name of the node")
    location: str = Field(None, description="Geographic location of the pool")

class WorkerConfigRequest(BaseModel):
    node_name: str = Field(None, description="Name for the worker node")
    mode: int = Field(2, description="Access mode for the worker (admin, worker or user)")
    target_platform: str = Field("amd64", description="Target platform architecture for the worker (amd64 or arm64)")
    num_gpus: int = Field(0, description="Number of GPUs to use on the worker node")
    ip_address: str = Field("0.0.0.0", description="IP address of the worker node")
    storage_compatible: bool = Field(True, description="Whether to use the node's storage capacity for volumes")


class NodesActionRequest(BaseModel):
    nodes: list[str] = Field(None, description="List of node names to perform the action on, defaults to None")

class JoinPoolRequest(BaseModel):
    token: str = Field(description="Token to join the pool")
    ip_address: str = Field(None, description="IP address for the node")
    node_name: str = Field(None, description="Name of the node")
    num_gpus: int = Field(None, description="Number of GPUs to allocate")
    frontend: bool = Field(False, description="Whether this is a frontend request")

class JobDetailsRequest(BaseModel):
    jobs: list[Job] = Field(description="List of jobs to get details for")

class StopPoolRequest(BaseModel):
    skip_node_deletion: bool = Field(False, description="Whether to skip node deletion when stopping the pool")

class DeployJobRequest(BaseModel):
    name: str = Field(description="Name of the job")
    template_name: str = Field(description="Job template to use")
    template_repo: Optional[str] = Field("kalavai-templates", description="Repository to find the job template")
    values: dict = Field(description="Job configuration values")
    force_namespace: Optional[Union[str, None]] = Field(None, description="Optional namespace override")
    target_labels: Optional[Union[dict[str, Union[str, List]], None]] = Field(None, description="Optional target node labels")
    target_labels_ops: Optional[Literal["OR", "AND"]] = Field("AND", description="Optional target node labels operator")

class CustomDeployJobRequest(BaseModel):
    template_str: str = Field(description="YAML str containing the custom template job to use")
    values: dict = Field(description="Job configuration values")
    default_values: str = Field(description="YAML str containing the default values for the template job to use")
    force_namespace: Optional[Union[str, None]] = Field(None, description="Optional namespace override")
    target_labels: Optional[Union[dict[str, Union[str, List]], None]] = Field(None, description="Optional target node labels")

class DeleteJobRequest(BaseModel):
    name: str = Field(description="Name of the job to delete")
    force_namespace: Optional[Union[str, None]] = Field(None, description="Optional namespace override")

class NodeLabelsRequest(BaseModel):
    node_name: str = Field(description="Name of the node to add labels to")
    labels: Dict[str, str] = Field(description="Dictionary of labels to add to the node")
