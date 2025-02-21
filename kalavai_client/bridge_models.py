from pydantic import BaseModel

from kalavai_client.core import Job


class CreatePoolRequest(BaseModel):
    cluster_name: str
    ip_address: str
    app_values: dict
    num_gpus: int
    node_name: str
    only_registered_users: bool
    location: str

class DeleteNodesRequest(BaseModel):
    nodes: list[str]

class JoinPoolRequest(BaseModel):
    token: str
    node_name: str = None
    num_gpus: int = None

class JobDetailsRequest(BaseModel):
    jobs: list[Job]


class StopPoolRequest(BaseModel):
    skip_node_deletion: bool = False

class DeployJobRequest(BaseModel):
    template_name: str
    values: dict
    force_namespace: str = None

class DeleteJobRequest(BaseModel):
    name: str
    force_namespace: str = None