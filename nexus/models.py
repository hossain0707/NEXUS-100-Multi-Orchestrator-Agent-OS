from datetime import datetime, timezone
from enum import Enum
from uuid import UUID, uuid4
from pydantic import BaseModel, Field
class Risk(str, Enum):
    low="low"; medium="medium"; high="high"; critical="critical"
class TaskStatus(str, Enum):
    planned="planned"; queued="queued"; running="running"; waiting_approval="waiting_approval"; completed="completed"; failed="failed"
class AgentSpec(BaseModel):
    id: str
    name: str
    domain: str
    capabilities: list[str]
    tool_scopes: list[str] = ["READ","ANALYZE","PROPOSE"]
class RouteStep(BaseModel):
    order: int
    domain: str
    orchestrator: str
    agent_id: str
    capability: str
    status: TaskStatus = TaskStatus.planned
class Mission(BaseModel):
    id: UUID = Field(default_factory=uuid4)
    objective: str
    priority: str = "normal"
    status: TaskStatus = TaskStatus.planned
    route: list[RouteStep] = Field(default_factory=list)
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
class Approval(BaseModel):
    id: UUID = Field(default_factory=uuid4)
    mission_id: UUID | None = None
    action: str
    reason: str
    risk: Risk = Risk.high
    status: str = "awaiting_human_approval"
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
