import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session
from app.models.user import User
from app.core import security
from app.schemas.user import UserCreate


@pytest.fixture
def test_user_data():
    return {
        "username": "testuser",
        "email": "test@example.com",
        "password": "testpassword123"
    }


@pytest.fixture
def test_user(db: Session, test_user_data):
    user = User(username=test_user_data["username"],
                email=test_user_data["email"],
                hashed_password=security.get_password_hash(
                    test_user_data["password"]))
    db.add(user)
    db.commit()
    db.refresh(user)
    return user


def test_register_user(client: TestClient, db: Session):
    """Test user registration"""
    user_data = {
        "username": "newuser",
        "email": "new@example.com",
        "password": "newpassword123"
    }

    response = client.post("/api/v1/auth/register", json=user_data)

    assert response.status_code == 200
    data = response.json()
    assert data["username"] == user_data["username"]
    assert data["email"] == user_data["email"]
    assert "id" in data
    assert "hashed_password" not in data


def test_register_duplicate_username(client: TestClient, test_user: User):
    """Test registration with duplicate username"""
    user_data = {
        "username": test_user.username,  # Duplicate username
        "email": "different@example.com",
        "password": "password123"
    }

    response = client.post("/api/v1/auth/register", json=user_data)

    assert response.status_code == 400
    assert "Username already registered" in response.json()["detail"]


def test_register_duplicate_email(client: TestClient, test_user: User):
    """Test registration with duplicate email"""
    user_data = {
        "username": "differentuser",
        "email": test_user.email,  # Duplicate email
        "password": "password123"
    }

    response = client.post("/api/v1/auth/register", json=user_data)

    assert response.status_code == 400
    assert "Email already registered" in response.json()["detail"]


def test_register_invalid_password(client: TestClient):
    """Test registration with invalid password"""
    user_data = {
        "username": "validuser",
        "email": "valid@example.com",
        "password": "short"  # Too short password
    }

    response = client.post("/api/v1/auth/register", json=user_data)

    assert response.status_code == 422


def test_login_success(client: TestClient, test_user: User,
                       test_user_data: dict):
    """Test successful login"""
    response = client.post("/api/v1/auth/login",
                           data={
                               "username": test_user_data["username"],
                               "password": test_user_data["password"]
                           })

    assert response.status_code == 200
    assert response.json()["message"] == "Successfully logged in"
    assert "session" in response.cookies


def test_login_wrong_password(client: TestClient, test_user: User):
    """Test login with wrong password"""
    response = client.post("/api/v1/auth/login",
                           data={
                               "username": test_user.username,
                               "password": "wrongpassword"
                           })

    assert response.status_code == 401
    assert "Incorrect username or password" in response.json()["detail"]


def test_login_nonexistent_user(client: TestClient):
    """Test login with nonexistent user"""
    response = client.post("/api/v1/auth/login",
                           data={
                               "username": "nonexistent",
                               "password": "password123"
                           })

    assert response.status_code == 401
    assert "Incorrect username or password" in response.json()["detail"]


def test_logout(client: TestClient, test_user: User):
    """Test logout functionality"""
    # First login
    login_response = client.post("/api/v1/auth/login",
                                 data={
                                     "username": test_user.username,
                                     "password": "testpassword123"
                                 })
    assert login_response.status_code == 200

    # Then logout
    logout_response = client.post("/api/v1/auth/logout")
    assert logout_response.status_code == 200
    assert logout_response.json()["message"] == "Successfully logged out"


def test_session_persistence(client: TestClient, test_user: User,
                             test_user_data: dict):
    """Test session persistence across requests"""
    # Login first
    login_response = client.post("/api/v1/auth/login",
                                 data={
                                     "username": test_user_data["username"],
                                     "password": test_user_data["password"]
                                 })
    assert login_response.status_code == 200

    # Try accessing a protected endpoint
    response = client.get("/api/v1/organizations/current")
    assert response.status_code != 401


def test_rate_limiting_login(client: TestClient, test_user_data: dict):
    """Test rate limiting on login endpoint"""
    responses = []
    for _ in range(61):  # Exceed rate limit
        response = client.post("/api/v1/auth/login",
                               data={
                                   "username": test_user_data["username"],
                                   "password": test_user_data["password"]
                               })
        responses.append(response)

    assert any(r.status_code == 429 for r in responses)


def test_password_hashing(client: TestClient, db: Session):
    """Test password hashing functionality"""
    user_data = {
        "username": "hashtest",
        "email": "hash@example.com",
        "password": "testpassword123"
    }

    response = client.post("/api/v1/auth/register", json=user_data)

    # Get user from database
    user = db.query(User).filter(User.username == "hashtest").first()
    assert user is not None
    assert user.hashed_password != user_data["password"]
    assert security.verify_password(user_data["password"],
                                    user.hashed_password)


def test_session_expiry(client: TestClient, test_user: User,
                        test_user_data: dict):
    """Test session expiration"""
    # This test might need to be adjusted based on your session configuration
    login_response = client.post("/api/v1/auth/login",
                                 data={
                                     "username": test_user_data["username"],
                                     "password": test_user_data["password"]
                                 })
    assert login_response.status_code == 200

    # Check session cookie attributes
    session_cookie = login_response.cookies.get("session")
    assert session_cookie is not None
    # Add assertions for cookie attributes based on your configuration


def test_concurrent_sessions(client: TestClient, test_user: User,
                             test_user_data: dict):
    """Test handling of concurrent sessions"""
    # Create two clients
    client1 = TestClient(client.app)
    client2 = TestClient(client.app)

    # Login with both clients
    response1 = client1.post("/api/v1/auth/login",
                             data={
                                 "username": test_user_data["username"],
                                 "password": test_user_data["password"]
                             })
    response2 = client2.post("/api/v1/auth/login",
                             data={
                                 "username": test_user_data["username"],
                                 "password": test_user_data["password"]
                             })

    assert response1.status_code == 200
    assert response2.status_code == 200

    # Verify both sessions are active
    assert client1.get("/api/v1/organizations/current").status_code != 401
    assert client2.get("/api/v1/organizations/current").status_code != 401


def test_invalid_session(client: TestClient):
    """Test handling of invalid session"""
    # Try accessing protected endpoint without login
    response = client.get("/api/v1/organizations/current")
    assert response.status_code == 401
