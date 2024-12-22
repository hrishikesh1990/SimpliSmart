from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List
from app.core import deps
from app.schemas.cluster import Cluster, ClusterCreate, ClusterWithResources
from app.models.user import User
from app.models.cluster import Cluster as ClusterModel, ClusterStatus

router = APIRouter()


def validate_resources(cluster_in: ClusterCreate):
    """Validate resource constraints"""
    if cluster_in.cpu_limit <= 0:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST,
                            detail="CPU limit must be greater than 0")

    if cluster_in.ram_limit <= 0:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST,
                            detail="Memory limit must be greater than 0")

    if cluster_in.gpu_limit < 0:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST,
                            detail="GPU limit cannot be negative")


@router.post("/", response_model=ClusterWithResources)
def create_cluster(*,
                   db: Session = Depends(deps.get_db),
                   cluster_in: ClusterCreate,
                   current_user: User = Depends(deps.get_current_user)):
    """Create a new cluster with resource limits"""
    if not current_user.organization_id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="User must be a member of an organization to create clusters"
        )

    # Validate resource constraints
    validate_resources(cluster_in)

    # Check organization's total resource usage
    org_clusters = db.query(ClusterModel).filter(
        ClusterModel.organization_id == current_user.organization_id).all()

    total_cpu = sum(c.cpu_limit for c in org_clusters)
    total_memory = sum(c.ram_limit for c in org_clusters)
    total_gpu = sum(c.gpu_limit for c in org_clusters)

    # Example resource limits per organization (adjust as needed)
    ORG_CPU_LIMIT = 100  # cores
    ORG_ram_limit = 1024  # GB
    ORG_GPU_LIMIT = 8  # GPUs

    if total_cpu + cluster_in.cpu_limit > ORG_CPU_LIMIT:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=
            f"Organization CPU limit exceeded. Available: {ORG_CPU_LIMIT - total_cpu} cores"
        )

    if total_memory + cluster_in.ram_limit > ORG_ram_limit:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=
            f"Organization memory limit exceeded. Available: {ORG_ram_limit - total_memory} GB"
        )

    if total_gpu + cluster_in.gpu_limit > ORG_GPU_LIMIT:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=
            f"Organization GPU limit exceeded. Available: {ORG_GPU_LIMIT - total_gpu} GPUs"
        )

    # Create new cluster
    cluster = ClusterModel(name=cluster_in.name,
                           description=cluster_in.description,
                           organization_id=current_user.organization_id,
                           cloud_provider=cluster_in.cloud_provider,
                           region=cluster_in.region,
                           status=ClusterStatus.PENDING,
                           cpu_limit=cluster_in.cpu_limit,
                           ram_limit=cluster_in.ram_limit,
                           gpu_limit=cluster_in.gpu_limit)

    db.add(cluster)
    db.commit()
    db.refresh(cluster)

    return cluster


@router.get("/", response_model=List[Cluster])
def list_clusters(db: Session = Depends(deps.get_db),
                  current_user: User = Depends(deps.get_current_user),
                  skip: int = 0,
                  limit: int = 100):
    """List all clusters in the user's organization"""
    if not current_user.organization_id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="User must be a member of an organization to view clusters")

    clusters = db.query(ClusterModel).filter(
        ClusterModel.organization_id == current_user.organization_id).offset(
            skip).limit(limit).all()

    return clusters


@router.get("/{cluster_id}", response_model=Cluster)
def get_cluster(cluster_id: int,
                db: Session = Depends(deps.get_db),
                current_user: User = Depends(deps.get_current_user)):
    """Get a specific cluster by ID"""
    if not current_user.organization_id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="User must be a member of an organization to view clusters")

    cluster = db.query(ClusterModel).filter(
        ClusterModel.id == cluster_id,
        ClusterModel.organization_id == current_user.organization_id).first()

    if not cluster:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND,
                            detail="Cluster not found")

    return cluster


@router.delete("/{cluster_id}")
def delete_cluster(cluster_id: int,
                   db: Session = Depends(deps.get_db),
                   current_user: User = Depends(deps.get_current_user)):
    """Delete a specific cluster"""
    if not current_user.organization_id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="User must be a member of an organization to manage clusters"
        )

    cluster = db.query(ClusterModel).filter(
        ClusterModel.id == cluster_id,
        ClusterModel.organization_id == current_user.organization_id).first()

    if not cluster:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND,
                            detail="Cluster not found")

    db.delete(cluster)
    db.commit()

    return {"message": "Cluster successfully deleted"}


@router.get("/resources")
def get_organization_resources(db: Session = Depends(deps.get_db),
                               current_user: User = Depends(
                                   deps.get_current_user)):
    """Get organization's resource usage and limits"""
    if not current_user.organization_id:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST,
                            detail="User must be a member of an organization")

    clusters = db.query(ClusterModel).filter(
        ClusterModel.organization_id == current_user.organization_id).all()

    total_cpu = sum(c.cpu_limit for c in clusters)
    total_memory = sum(c.ram_limit for c in clusters)
    total_gpu = sum(c.gpu_limit for c in clusters)

    used_cpu = sum(c.cpu_used for c in clusters)
    used_memory = sum(c.ram_used for c in clusters)
    used_gpu = sum(c.gpu_used for c in clusters)

    return {
        "total_resources": {
            "cpu": total_cpu,
            "memory": total_memory,
            "gpu": total_gpu
        },
        "used_resources": {
            "cpu": used_cpu,
            "memory": used_memory,
            "gpu": used_gpu
        },
        "available_resources": {
            "cpu": 100 - total_cpu,  # Organization limit
            "memory": 1024 - total_memory,  # Organization limit
            "gpu": 8 - total_gpu  # Organization limit
        }
    }


@router.put("/{cluster_id}/resources")
def update_cluster_resources(cluster_id: int,
                             cpu_used: float,
                             ram_used: float,
                             gpu_used: int,
                             db: Session = Depends(deps.get_db),
                             current_user: User = Depends(
                                 deps.get_current_user)):
    """Update cluster resource usage"""
    cluster = db.query(ClusterModel).filter(
        ClusterModel.id == cluster_id,
        ClusterModel.organization_id == current_user.organization_id).first()

    if not cluster:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND,
                            detail="Cluster not found")

    # Validate resource usage against limits
    if cpu_used > cluster.cpu_limit:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST,
                            detail="CPU usage exceeds limit")

    if ram_used > cluster.ram_limit:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST,
                            detail="Memory usage exceeds limit")

    if gpu_used > cluster.gpu_limit:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST,
                            detail="GPU usage exceeds limit")

    cluster.cpu_used = cpu_used
    cluster.ram_used = ram_used
    cluster.gpu_used = gpu_used

    db.commit()
    db.refresh(cluster)

    return cluster
