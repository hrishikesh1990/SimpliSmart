import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session
from app.main import app
from app.models.deployment import Deployment, DeploymentStatus, DeploymentPriority
from app.models.cluster import Cluster
from app.models.organization import Organization
from app.models.user import User
from datetime import datetime


@pytest.fixture
def test_org(db: Session):
    org = Organization(name="Test Org", invite_code="test123")
    db.add(org)
    db.commit()
    return org


@pytest.fixture
def test_user(db: Session, test_org: Organization):
    user = User(username="testuser",
                email="test@example.com",
                hashed_password="dummyhash",
                organization_id=test_org.id)
    db.add(user)
    db.commit()
    return user


@pytest.fixture
def test_cluster(db: Session, test_org: Organization):
    cluster = Cluster(name="Test Cluster",
                      organization_id=test_org.id,
                      cpu_limit=10,
                      ram_limit=32,
                      gpu_limit=2)
    db.add(cluster)
    db.commit()
    return cluster


@pytest.fixture
def auth_headers(test_user: User):
    return {"Authorization": f"Bearer {test_user.id}"}


def test_create_deployment(client: TestClient, db: Session,
                           test_cluster: Cluster, auth_headers: dict):
    response = client.post("/api/v1/deployments/",
                           headers=auth_headers,
                           json={
                               "name": "Test Deployment",
                               "description": "Test Description",
                               "cluster_id": test_cluster.id,
                               "cpu_required": 2,
                               "memory_required": 8,
                               "gpu_required": 1,
                               "priority": DeploymentPriority.MEDIUM
                           })

    assert response.status_code == 200
    data = response.json()
    assert data["name"] == "Test Deployment"
    assert data["status"] == DeploymentStatus.SCHEDULED


def test_deployment_dependencies(client: TestClient, db: Session,
                                 test_cluster: Cluster, auth_headers: dict):
    # Create first deployment
    response1 = client.post("/api/v1/deployments/",
                            headers=auth_headers,
                            json={
                                "name": "Deployment A",
                                "cluster_id": test_cluster.id,
                                "cpu_required": 1,
                                "memory_required": 4,
                                "priority": DeploymentPriority.MEDIUM
                            })

    dep_a_id = response1.json()["id"]

    # Create dependent deployment
    response2 = client.post("/api/v1/deployments/",
                            headers=auth_headers,
                            json={
                                "name": "Deployment B",
                                "cluster_id": test_cluster.id,
                                "cpu_required": 1,
                                "memory_required": 4,
                                "priority": DeploymentPriority.MEDIUM,
                                "dependency_ids": [dep_a_id]
                            })

    assert response2.status_code == 200
    data = response2.json()
    assert data["status"] == DeploymentStatus.PENDING
    assert len(data["dependencies"]) == 1


def test_rate_limiting(client: TestClient, auth_headers: dict):
    # Make multiple requests quickly
    responses = []
    for _ in range(61):  # Exceed the rate limit
        response = client.get("/api/v1/deployments/", headers=auth_headers)
        responses.append(response)

    # Check that at least one request was rate limited
    assert any(r.status_code == 429 for r in responses)


def test_preemption(client: TestClient, db: Session, test_cluster: Cluster,
                    auth_headers: dict):
    # Create low priority deployment
    response1 = client.post("/api/v1/deployments/",
                            headers=auth_headers,
                            json={
                                "name": "Low Priority",
                                "cluster_id": test_cluster.id,
                                "cpu_required": 8,
                                "memory_required": 16,
                                "priority": DeploymentPriority.LOW
                            })

    # Create high priority deployment
    response2 = client.post("/api/v1/deployments/",
                            headers=auth_headers,
                            json={
                                "name": "High Priority",
                                "cluster_id": test_cluster.id,
                                "cpu_required": 8,
                                "memory_required": 16,
                                "priority": DeploymentPriority.CRITICAL
                            })

    # Check that high priority deployment preempted low priority
    low_priority_dep = db.query(Deployment).get(response1.json()["id"])
    assert low_priority_dep.status == DeploymentStatus.PREEMPTED

    high_priority_dep = db.query(Deployment).get(response2.json()["id"])
    assert high_priority_dep.status == DeploymentStatus.SCHEDULED
