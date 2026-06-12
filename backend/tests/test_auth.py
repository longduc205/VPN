import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from main import app
from app.core.database import get_db
from sqlalchemy.pool import StaticPool
from app.models.base import Base
from app.models.user import User
from app.modules.auth.helpers import get_password_hash, verify_password, create_access_token, verify_token

# Setup in-memory SQLite database with StaticPool to share connection across threads
SQLALCHEMY_DATABASE_URL = "sqlite:///:memory:"
engine = create_engine(
    SQLALCHEMY_DATABASE_URL,
    connect_args={"check_same_thread": False},
    poolclass=StaticPool
)
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


@pytest.fixture(name="db_session")
def fixture_db_session():
    Base.metadata.create_all(bind=engine)
    db = TestingSessionLocal()
    try:
        yield db
    finally:
        db.close()
        Base.metadata.drop_all(bind=engine)


@pytest.fixture(name="client")
def fixture_client(db_session):
    def override_get_db():
        try:
            yield db_session
        finally:
            pass
    app.dependency_overrides[get_db] = override_get_db
    with TestClient(app) as c:
        yield c
    app.dependency_overrides.clear()


def test_password_hashing():
    pwd = "MySuperSecretPassword123!"
    hashed = get_password_hash(pwd)
    assert hashed != pwd
    assert verify_password(plain_password=pwd, hashed_password=hashed) is True
    assert verify_password(plain_password="wrongpassword", hashed_password=hashed) is False


def test_jwt_operations():
    payload = {"sub": "user_id_123", "role": "user"}
    token = create_access_token(payload)
    assert token is not None
    
    decoded = verify_token(token)
    assert decoded is not None
    assert decoded["sub"] == "user_id_123"
    assert decoded["role"] == "user"


def test_login_flow(client, db_session):
    # 1. Create a test user in DB
    user = User(
        username="testuser",
        hashed_password=get_password_hash("TestSecurePassword123!"),
        role="user",
        is_active=True
    )
    db_session.add(user)
    db_session.commit()

    # 2. Test successful login
    response = client.post("/api/auth/login", json={
        "username": "testuser",
        "password": "TestSecurePassword123!"
    })
    assert response.status_code == 200
    assert response.json()["username"] == "testuser"
    assert response.json()["role"] == "user"
    assert "session_token" in response.cookies or "__Host-session" in response.cookies

    # 3. Test failed login (wrong password)
    response_wrong = client.post("/api/auth/login", json={
        "username": "testuser",
        "password": "WrongPassword123!"
    })
    assert response_wrong.status_code == 400
    assert response_wrong.json()["detail"] == "Invalid username or password."


def test_protected_routes(client, db_session):
    # 1. Access /me without login -> 401
    resp = client.get("/api/auth/me")
    assert resp.status_code == 401

    # 2. Add admin user
    admin = User(
        username="adminuser",
        hashed_password=get_password_hash("AdminSecurePassword123!"),
        role="admin",
        is_active=True
    )
    db_session.add(admin)
    db_session.commit()

    # 3. Login as admin
    login_resp = client.post("/api/auth/login", json={
        "username": "adminuser",
        "password": "AdminSecurePassword123!"
    })
    assert login_resp.status_code == 200

    # 4. Access /me -> 200
    me_resp = client.get("/api/auth/me")
    assert me_resp.status_code == 200
    assert me_resp.json()["username"] == "adminuser"
    assert me_resp.json()["role"] == "admin"
