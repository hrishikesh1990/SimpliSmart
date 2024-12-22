from pydantic import BaseModel, Field
from typing import Optional
from enum import Enum


class ClusterStatus(str, Enum):
    PENDING = "pending"
    RUNNING = "running"
    STOPPED = "stopped"
    ERROR = "error"


class ClusterBase(BaseModel):
    name: str
    description: Optional[str] = None
    cloud_provider: str
    region: str


class ClusterCreate(ClusterBase):
    cpu_limit: float = Field(..., gt=0, description="CPU cores limit")
    ram_limit: float = Field(..., gt=0, description="Memory limit in GB")
    gpu_limit: int = Field(0, ge=0, description="Number of GPUs")


class ClusterWithResources(ClusterBase):
    id: int
    organization_id: int
    status: ClusterStatus
    cpu_limit: float
    ram_limit: float
    gpu_limit: int
    cpu_used: float
    ram_used: float
    gpu_used: int

    class Config:
        orm_mode = True
