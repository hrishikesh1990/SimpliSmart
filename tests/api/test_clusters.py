import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session
from app.models.cluster import Cluster, ClusterStatus
from app.models.organization import Organization
from app.models.user import User
from app.models.deployment import Deployment, DeploymentStatus, DeploymentPriority


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
def auth_headers(test_user: User):
    return {"Authorization": f"Bearer {test_user.id}"}


@pytest.fixture
def test_cluster(db: Session, test_org: Organization):
    cluster = Cluster(name="Test Cluster",
                      description="Test Description",
                      organization_id=test_org.id,
                      cloud_provider="aws",
                      region="us-east-1",
                      cpu_limit=10.0,
                      ram_limit=32.0,
                      gpu_limit=2)
    db.add(cluster)
    db.commit()
    return cluster


def test_create_cluster(client: TestClient, db: Session, auth_headers: dict):
    """Test cluster creation"""
    response = client.post("/api/v1/clusters/",
                           headers=auth_headers,
                           json={
                               "name": "New Cluster",
                               "description": "Test Description",
                               "cloud_provider": "aws",
                               "region": "us-east-1",
                               "cpu_limit": 8.0,
                               "ram_limit": 16.0,
                               "gpu_limit": 1
                           })

    assert response.status_code == 200
    data = response.json()
    assert data["name"] == "New Cluster"
    assert data["status"] == ClusterStatus.PENDING
    assert data["cpu_limit"] == 8.0
    assert data["ram_limit"] == 16.0
    assert data["gpu_limit"] == 1


def test_create_cluster_validation(client: TestClient, auth_headers: dict):
    """Test cluster creation validation"""
    # Test invalid resource limits
    response = client.post(
        "/api/v1/clusters/",
        headers=auth_headers,
        json={
            "name": "Invalid Cluster",
            "cloud_provider": "aws",
            "region": "us-east-1",
            "cpu_limit": -1,  # Invalid value
            "ram_limit": 16.0,
            "gpu_limit": 1
        })
    assert response.status_code == 422


def test_list_clusters(client: TestClient, db: Session, test_cluster: Cluster,
                       auth_headers: dict):
    """Test cluster listing"""
    response = client.get("/api/v1/clusters/", headers=auth_headers)
    assert response.status_code == 200
    data = response.json()
    assert len(data) >= 1
    assert any(cluster["name"] == "Test Cluster" for cluster in data)


def test_get_cluster(client: TestClient, test_cluster: Cluster,
                     auth_headers: dict):
    """Test getting a specific cluster"""
    response = client.get(f"/api/v1/clusters/{test_cluster.id}",
                          headers=auth_headers)
    assert response.status_code == 200
    data = response.json()
    assert data["name"] == "Test Cluster"
    assert data["cpu_limit"] == 10.0


def test_get_nonexistent_cluster(client: TestClient, auth_headers: dict):
    """Test getting a nonexistent cluster"""
    response = client.get("/api/v1/clusters/99999", headers=auth_headers)
    assert response.status_code == 404


def test_delete_cluster(client: TestClient, test_cluster: Cluster,
                        auth_headers: dict):
    """Test cluster deletion"""
    response = client.delete(f"/api/v1/clusters/{test_cluster.id}",
                             headers=auth_headers)
    assert response.status_code == 200

    # Verify cluster is deleted
    response = client.get(f"/api/v1/clusters/{test_cluster.id}",
                          headers=auth_headers)
    assert response.status_code == 404


def test_cluster_resource_management(client: TestClient, db: Session,
                                     test_cluster: Cluster,
                                     auth_headers: dict):
    """Test cluster resource management"""
    # Create a deployment that uses resources
    response = client.post("/api/v1/deployments/",
                           headers=auth_headers,
                           json={
                               "name": "Resource Test",
                               "cluster_id": test_cluster.id,
                               "cpu_required": 4.0,
                               "memory_required": 8.0,
                               "gpu_required": 1,
                               "priority": DeploymentPriority.MEDIUM
                           })
    assert response.status_code == 200

    # Check cluster resource usage
    response = client.get(f"/api/v1/clusters/{test_cluster.id}/resources",
                          headers=auth_headers)
    assert response.status_code == 200
    data = response.json()
    assert data["used_resources"]["cpu"] == 4.0
    assert data["used_resources"]["memory"] == 8.0
    assert data["used_resources"]["gpu"] == 1


def test_cluster_resource_limits(client: TestClient, test_cluster: Cluster,
                                 auth_headers: dict):
    """Test cluster resource limits"""
    # Try to create deployment exceeding limits
    response = client.post(
        "/api/v1/deployments/",
        headers=auth_headers,
        json={
            "name": "Exceed Limits",
            "cluster_id": test_cluster.id,
            "cpu_required": 20.0,  # Exceeds cluster limit
            "memory_required": 64.0,  # Exceeds cluster limit
            "gpu_required": 3,  # Exceeds cluster limit
            "priority": DeploymentPriority.MEDIUM
        })
    assert response.status_code == 400


def test_cluster_authorization(client: TestClient, db: Session,
                               test_cluster: Cluster):
    """Test cluster access authorization"""
    # Create user in different organization
    other_org = Organization(name="Other Org", invite_code="other123")
    db.add(other_org)
    db.commit()

    other_user = User(username="otheruser",
                      email="other@example.com",
                      hashed_password="dummyhash",
                      organization_id=other_org.id)
    db.add(other_user)
    db.commit()

    other_headers = {"Authorization": f"Bearer {other_user.id}"}

    # Try to access cluster from different organization
    response = client.get(f"/api/v1/clusters/{test_cluster.id}",
                          headers=other_headers)
    assert response.status_code == 404


def test_cluster_status_updates(client: TestClient, test_cluster: Cluster,
                                auth_headers: dict):
    """Test cluster status updates"""
    response = client.put(f"/api/v1/clusters/{test_cluster.id}/status",
                          headers=auth_headers,
                          json={"status": ClusterStatus.RUNNING})
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == ClusterStatus.RUNNING


def test_rate_limiting(client: TestClient, auth_headers: dict):
    """Test rate limiting on cluster endpoints"""
    responses = []
    for _ in range(61):  # Exceed rate limit
        response = client.get("/api/v1/clusters/", headers=auth_headers)
        responses.append(response)

    assert any(r.status_code == 429 for r in responses)


def test_cluster_metrics(client: TestClient, test_cluster: Cluster,
                         auth_headers: dict, db: Session):
    """Test cluster metrics and statistics"""
    # Create some deployments
    for i in range(3):
        deployment = Deployment(name=f"Metric Test {i}",
                                cluster_id=test_cluster.id,
                                cpu_required=1.0,
                                memory_required=2.0,
                                gpu_required=0,
                                status=DeploymentStatus.RUNNING)
        db.add(deployment)
    db.commit()

    response = client.get(f"/api/v1/clusters/{test_cluster.id}/metrics",
                          headers=auth_headers)
    assert response.status_code == 200
    data = response.json()
    assert "deployment_count" in data
    assert "resource_utilization" in data
    assert data["deployment_count"] == 3
