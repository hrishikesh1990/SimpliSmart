import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session
from app.models.organization import Organization
from app.models.user import User
from app.models.cluster import Cluster
from app.core import security


@pytest.fixture
def test_org_data():
    return {"name": "Test Organization"}


@pytest.fixture
def test_org(db: Session):
    org = Organization(name="Test Organization", invite_code="test123")
    db.add(org)
    db.commit()
    db.refresh(org)
    return org


@pytest.fixture
def test_user(db: Session):
    user = User(username="testuser",
                email="test@example.com",
                hashed_password=security.get_password_hash("testpassword123"))
    db.add(user)
    db.commit()
    db.refresh(user)
    return user


@pytest.fixture
def auth_headers(test_user: User):
    return {"Authorization": f"Bearer {test_user.id}"}


def test_create_organization(client: TestClient, auth_headers: dict,
                             test_org_data: dict):
    """Test organization creation"""
    response = client.post("/api/v1/organizations/",
                           headers=auth_headers,
                           json=test_org_data)

    assert response.status_code == 200
    data = response.json()
    assert data["name"] == test_org_data["name"]
    assert "invite_code" in data
    assert len(data["invite_code"]) == 8  # Default invite code length


def test_create_organization_duplicate_name(client: TestClient,
                                            auth_headers: dict,
                                            test_org: Organization):
    """Test creating organization with duplicate name"""
    response = client.post("/api/v1/organizations/",
                           headers=auth_headers,
                           json={"name": test_org.name})

    assert response.status_code == 400
    assert "Organization name already exists" in response.json()["detail"]


def test_join_organization(client: TestClient, auth_headers: dict,
                           test_org: Organization, test_user: User):
    """Test joining an organization with invite code"""
    response = client.post(
        f"/api/v1/organizations/{test_org.invite_code}/join",
        headers=auth_headers)

    assert response.status_code == 200
    assert "Successfully joined organization" in response.json()["message"]

    # Verify user is now part of the organization
    user_response = client.get("/api/v1/organizations/current",
                               headers=auth_headers)
    assert user_response.status_code == 200
    assert user_response.json()["id"] == test_org.id


def test_join_organization_invalid_code(client: TestClient,
                                        auth_headers: dict):
    """Test joining with invalid invite code"""
    response = client.post("/api/v1/organizations/invalid123/join",
                           headers=auth_headers)

    assert response.status_code == 404
    assert "Invalid invite code" in response.json()["detail"]


def test_join_organization_already_member(client: TestClient,
                                          auth_headers: dict,
                                          test_org: Organization,
                                          test_user: User, db: Session):
    """Test joining when already a member of an organization"""
    # First join an organization
    test_user.organization_id = test_org.id
    db.add(test_user)
    db.commit()

    # Try to join another organization
    response = client.post(
        f"/api/v1/organizations/{test_org.invite_code}/join",
        headers=auth_headers)

    assert response.status_code == 400
    assert "already a member" in response.json()["detail"].lower()


def test_get_current_organization(client: TestClient, auth_headers: dict,
                                  test_org: Organization, test_user: User,
                                  db: Session):
    """Test getting current organization details"""
    # Set user's organization
    test_user.organization_id = test_org.id
    db.add(test_user)
    db.commit()

    response = client.get("/api/v1/organizations/current",
                          headers=auth_headers)

    assert response.status_code == 200
    data = response.json()
    assert data["name"] == test_org.name
    assert data["id"] == test_org.id


def test_get_organization_no_membership(client: TestClient,
                                        auth_headers: dict):
    """Test getting organization when not a member"""
    response = client.get("/api/v1/organizations/current",
                          headers=auth_headers)

    assert response.status_code == 404
    assert "not a member" in response.json()["detail"].lower()


def test_organization_members(client: TestClient, auth_headers: dict,
                              test_org: Organization, test_user: User,
                              db: Session):
    """Test getting organization members"""
    # Add user to organization
    test_user.organization_id = test_org.id
    db.add(test_user)
    db.commit()

    response = client.get(f"/api/v1/organizations/{test_org.id}/members",
                          headers=auth_headers)

    assert response.status_code == 200
    data = response.json()
    assert len(data) >= 1
    assert any(member["id"] == test_user.id for member in data)


def test_organization_clusters(client: TestClient, auth_headers: dict,
                               test_org: Organization, test_user: User,
                               db: Session):
    """Test getting organization clusters"""
    # Add user to organization
    test_user.organization_id = test_org.id
    db.add(test_user)

    # Create test clusters
    clusters = [
        Cluster(name=f"Test Cluster {i}",
                organization_id=test_org.id,
                cpu_limit=4,
                ram_limit=8,
                gpu_limit=1) for i in range(3)
    ]
    db.add_all(clusters)
    db.commit()

    response = client.get(f"/api/v1/organizations/{test_org.id}/clusters",
                          headers=auth_headers)

    assert response.status_code == 200
    data = response.json()
    assert len(data) == 3


def test_organization_resource_limits(client: TestClient, auth_headers: dict,
                                      test_org: Organization, test_user: User,
                                      db: Session):
    """Test organization resource limits"""
    # Add user to organization
    test_user.organization_id = test_org.id
    db.add(test_user)
    db.commit()

    response = client.get(f"/api/v1/organizations/{test_org.id}/resources",
                          headers=auth_headers)

    assert response.status_code == 200
    data = response.json()
    assert "total_resources" in data
    assert "used_resources" in data
    assert "available_resources" in data


def test_rate_limiting(client: TestClient, auth_headers: dict):
    """Test rate limiting on organization endpoints"""
    responses = []
    for _ in range(61):  # Exceed rate limit
        response = client.get("/api/v1/organizations/current",
                              headers=auth_headers)
        responses.append(response)

    assert any(r.status_code == 429 for r in responses)


def test_organization_invite_code_uniqueness(client: TestClient,
                                             auth_headers: dict, db: Session):
    """Test that invite codes are unique"""
    # Create multiple organizations
    responses = []
    for i in range(5):
        response = client.post("/api/v1/organizations/",
                               headers=auth_headers,
                               json={"name": f"Test Org {i}"})
        responses.append(response.json())

    # Check that all invite codes are unique
    invite_codes = [r["invite_code"] for r in responses]
    assert len(set(invite_codes)) == len(invite_codes)


def test_organization_access_control(client: TestClient,
                                     test_org: Organization, db: Session):
    """Test organization access control"""
    # Create user in different organization
    other_org = Organization(name="Other Org", invite_code="other123")
    db.add(other_org)
    db.commit()

    other_user = User(
        username="otheruser",
        email="other@example.com",
        hashed_password=security.get_password_hash("password123"),
        organization_id=other_org.id)
    db.add(other_user)
    db.commit()

    other_headers = {"Authorization": f"Bearer {other_user.id}"}

    # Try to access another organization's details
    response = client.get(f"/api/v1/organizations/{test_org.id}/members",
                          headers=other_headers)

    assert response.status_code == 404


def test_leave_organization(client: TestClient, auth_headers: dict,
                            test_org: Organization, test_user: User,
                            db: Session):
    """Test leaving an organization"""
    # First join organization
    test_user.organization_id = test_org.id
    db.add(test_user)
    db.commit()

    response = client.post("/api/v1/organizations/leave", headers=auth_headers)

    assert response.status_code == 200
    assert "Successfully left organization" in response.json()["message"]

    # Verify user is no longer in organization
    user_response = client.get("/api/v1/organizations/current",
                               headers=auth_headers)
    assert user_response.status_code == 404
