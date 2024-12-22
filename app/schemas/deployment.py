from pydantic import BaseModel, Field
from typing import Optional, List, Set
from datetime import datetime
from enum import Enum


class DeploymentStatus(str, Enum):
    PENDING = "pending"
    SCHEDULED = "scheduled"
    RUNNING = "running"
    PREEMPTED = "preempted"
    FAILED = "failed"
    COMPLETED = "completed"


class DeploymentPriority(int, Enum):
    LOW = 0
    MEDIUM = 1
    HIGH = 2
    CRITICAL = 3


class DeploymentBase(BaseModel):
    name: str
    description: Optional[str] = None
    priority: DeploymentPriority = DeploymentPriority.MEDIUM


class DeploymentCreate(DeploymentBase):
    cluster_id: int
    cpu_required: float = Field(..., gt=0, description="Required CPU cores")
    memory_required: float = Field(...,
                                   gt=0,
                                   description="Required memory in GB")
    gpu_required: int = Field(0, ge=0, description="Required number of GPUs")
    dependency_ids: Optional[Set[int]] = Field(
        default=None,
        description="IDs of deployments that must complete first")


class Deployment(DeploymentBase):
    id: int
    cluster_id: int
    status: DeploymentStatus
    cpu_required: float
    memory_required: float
    gpu_required: int
    created_at: datetime
    scheduled_at: Optional[datetime]
    started_at: Optional[datetime]
    completed_at: Optional[datetime]
    dependencies: List["Deployment"] = []
    dependents: List["Deployment"] = []

    class Config:
        orm_mode = True


Deployment.update_forward_refs()
