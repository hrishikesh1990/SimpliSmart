from fastapi import APIRouter, Depends, HTTPException, status, BackgroundTasks, Request
from sqlalchemy.orm import Session
from typing import List, Optional
from datetime import datetime
from app.core import deps
from app.schemas.deployment import Deployment, DeploymentCreate, DeploymentStatus, DeploymentPriority
from app.models.deployment import Deployment as DeploymentModel
from app.models.cluster import Cluster as ClusterModel
from app.models.user import User
from app.core.rate_limiter import rate_limiter

router = APIRouter()


def check_cluster_access(db: Session, cluster_id: int, user: User):
    """Verify user has access to the cluster through their organization"""
    cluster = db.query(ClusterModel).filter(
        ClusterModel.id == cluster_id,
        ClusterModel.organization_id == user.organization_id).first()

    if not cluster:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND,
                            detail="Cluster not found or access denied")
    return cluster


def preempt_lower_priority_deployments(db: Session, cluster: ClusterModel,
                                       required_cpu: float,
                                       required_memory: float,
                                       required_gpu: int,
                                       priority: int) -> bool:
    """Attempt to preempt lower priority deployments to free up resources"""
    running_deployments = db.query(DeploymentModel).filter(
        DeploymentModel.cluster_id == cluster.id,
        DeploymentModel.status == DeploymentStatus.RUNNING,
        DeploymentModel.priority
        < priority).order_by(DeploymentModel.priority).all()

    freed_cpu = freed_memory = freed_gpu = 0
    preempted_deployments = []

    for deployment in running_deployments:
        freed_cpu += deployment.cpu_required
        freed_memory += deployment.memory_required
        freed_gpu += deployment.gpu_required
        preempted_deployments.append(deployment)

        # Check if we have enough resources after preemption
        if (freed_cpu >= required_cpu and freed_memory >= required_memory
                and freed_gpu >= required_gpu):
            break

    if (freed_cpu >= required_cpu and freed_memory >= required_memory
            and freed_gpu >= required_gpu):
        # Preempt the selected deployments
        for deployment in preempted_deployments:
            deployment.status = DeploymentStatus.PREEMPTED
            db.add(deployment)
        return True

    return False


def schedule_deployment(db: Session, deployment: DeploymentModel,
                        background_tasks: BackgroundTasks):
    """Schedule a deployment based on available resources and dependencies"""
    # Check dependencies first
    if deployment.dependencies and not all(
            d.status == DeploymentStatus.COMPLETED
            for d in deployment.dependencies):
        return

    cluster = deployment.cluster

    # Check if there are enough available resources
    available_cpu = cluster.cpu_limit - cluster.cpu_used
    available_memory = cluster.ram_limit - cluster.ram_used
    available_gpu = cluster.gpu_limit - cluster.gpu_used

    can_schedule = (available_cpu >= deployment.cpu_required
                    and available_memory >= deployment.memory_required
                    and available_gpu >= deployment.gpu_required)

    if not can_schedule:
        # Try preemption for high priority deployments
        if deployment.priority >= DeploymentPriority.HIGH:
            if preempt_lower_priority_deployments(db, cluster,
                                                  deployment.cpu_required,
                                                  deployment.memory_required,
                                                  deployment.gpu_required,
                                                  deployment.priority):
                can_schedule = True

    if can_schedule:
        # Update cluster resource usage
        cluster.cpu_used += deployment.cpu_required
        cluster.ram_used += deployment.memory_required
        cluster.gpu_used += deployment.gpu_required

        # Update deployment status
        deployment.status = DeploymentStatus.SCHEDULED
        deployment.scheduled_at = datetime.utcnow()

        db.add(cluster)
        db.add(deployment)
        db.commit()

        # Schedule actual deployment start in background
        background_tasks.add_task(start_deployment, db, deployment.id)
    else:
        deployment.status = DeploymentStatus.PENDING


async def start_deployment(db: Session, deployment_id: int):
    """Start a scheduled deployment"""
    deployment = db.query(DeploymentModel).filter(
        DeploymentModel.id == deployment_id).first()

    if deployment and deployment.status == DeploymentStatus.SCHEDULED:
        deployment.status = DeploymentStatus.RUNNING
        deployment.started_at = datetime.utcnow()
        db.add(deployment)
        db.commit()


@router.post("/", response_model=Deployment)
async def create_deployment(request: Request,
                            *,
                            db: Session = Depends(deps.get_db),
                            deployment_in: DeploymentCreate,
                            current_user: User = Depends(
                                deps.get_current_user),
                            background_tasks: BackgroundTasks):
    """Create a new deployment with dependencies"""
    await rate_limiter.check_rate_limit(request)

    # Verify cluster access
    cluster = check_cluster_access(db, deployment_in.cluster_id, current_user)

    # Create deployment
    deployment = DeploymentModel(name=deployment_in.name,
                                 description=deployment_in.description,
                                 cluster_id=deployment_in.cluster_id,
                                 cpu_required=deployment_in.cpu_required,
                                 memory_required=deployment_in.memory_required,
                                 gpu_required=deployment_in.gpu_required,
                                 priority=deployment_in.priority)

    # Add dependencies if specified
    if deployment_in.dependency_ids:
        dependencies = db.query(DeploymentModel).filter(
            DeploymentModel.id.in_(deployment_in.dependency_ids),
            DeploymentModel.cluster_id == cluster.id).all()

        if len(dependencies) != len(deployment_in.dependency_ids):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="One or more dependency deployments not found")

        deployment.dependencies.extend(dependencies)

    db.add(deployment)
    db.commit()
    db.refresh(deployment)

    # Only schedule if no dependencies or all dependencies are completed
    if not deployment.dependencies or all(
            d.status == DeploymentStatus.COMPLETED
            for d in deployment.dependencies):
        schedule_deployment(db, deployment, background_tasks)

    return deployment


@router.get("/", response_model=List[Deployment])
def list_deployments(db: Session = Depends(deps.get_db),
                     current_user: User = Depends(deps.get_current_user),
                     cluster_id: Optional[int] = None,
                     status: Optional[DeploymentStatus] = None,
                     skip: int = 0,
                     limit: int = 100):
    """List deployments with optional filters"""
    query = db.query(DeploymentModel).join(ClusterModel).filter(
        ClusterModel.organization_id == current_user.organization_id)

    if cluster_id:
        query = query.filter(DeploymentModel.cluster_id == cluster_id)
    if status:
        query = query.filter(DeploymentModel.status == status)

    deployments = query.offset(skip).limit(limit).all()
    return deployments


@router.delete("/{deployment_id}")
async def delete_deployment(deployment_id: int,
                            db: Session = Depends(deps.get_db),
                            current_user: User = Depends(
                                deps.get_current_user)):
    """Delete a deployment and free its resources"""
    # Find deployment and verify access
    deployment = db.query(DeploymentModel).join(ClusterModel).filter(
        DeploymentModel.id == deployment_id,
        ClusterModel.organization_id == current_user.organization_id).first()

    if not deployment:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND,
                            detail="Deployment not found")

    # Free resources if deployment was running
    if deployment.status == DeploymentStatus.RUNNING:
        cluster = deployment.cluster
        cluster.cpu_used -= deployment.cpu_required
        cluster.ram_used -= deployment.memory_required
        cluster.gpu_used -= deployment.gpu_required
        db.add(cluster)

    db.delete(deployment)
    db.commit()

    return {"message": "Deployment successfully deleted"}
