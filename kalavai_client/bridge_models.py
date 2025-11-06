from pydantic import BaseModel, Field
from typing import List, Dict, Union

from kalavai_client.core import Job, TokenType


class InvitesRequest(BaseModel):
    invitees: list[str] = Field(description="List of user identifiers to invite to the pool")

class CreatePoolRequest(BaseModel):
    cluster_name: str = Field(description="Name of the cluster to create")
    ip_address: str = Field(description="IP address for the pool")
    num_gpus: int = Field(None, description="Number of GPUs to allocate")
    node_name: str = Field(None, description="Name of the node")
    location: str = Field(None, description="Geographic location of the pool")
    token_mode: TokenType = Field(TokenType.USER, description="Token type for authentication")
    description: str = Field("", description="Description of the pool")

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
    template_name: str = Field(description="Name of the job template to use")
    values: dict = Field(description="Job configuration values")
    force_namespace: str = Field(None, description="Optional namespace override")
    target_labels: dict[str, Union[str, List]] = Field(None, description="Optional target node labels")

class DeleteJobRequest(BaseModel):
    name: str = Field(description="Name of the job to delete")
    force_namespace: str = Field(None, description="Optional namespace override")

class NodeLabelsRequest(BaseModel):
    node_name: str = Field(description="Name of the node to add labels to")
    labels: Dict[str, str] = Field(description="Dictionary of labels to add to the node")
