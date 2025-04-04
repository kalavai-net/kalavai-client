from pydantic import BaseModel

from kalavai_client.core import Job, TokenType


class InvitesRequest(BaseModel):
    invitees: list[str]

class CreatePoolRequest(BaseModel):
    cluster_name: str
    ip_address: str
    app_values: dict = None
    num_gpus: int = None
    node_name: str = None
    only_registered_users: bool = False
    location: str = None
    token_mode: TokenType = TokenType.USER
    description: str = ""
    frontend: bool = False

class NodesActionRequest(BaseModel):
    nodes: list[str]

class JoinPoolRequest(BaseModel):
    token: str
    ip_address: str = None
    node_name: str = None
    num_gpus: int = None
    frontend: bool = False
class JobDetailsRequest(BaseModel):
    jobs: list[Job]


class StopPoolRequest(BaseModel):
    skip_node_deletion: bool = False

class DeployJobRequest(BaseModel):
    template_name: str
    values: dict
    force_namespace: str = None
    target_labels: dict[str, str] = None

class DeleteJobRequest(BaseModel):
    name: str
    force_namespace: str = None