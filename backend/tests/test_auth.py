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
@pytest.fixture(autouse=True)
def clear_rate_limit():
    from app.modules.auth.router import LOGIN_ATTEMPTS
    LOGIN_ATTEMPTS.clear()

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


def test_totp_verification():
    import time
    from app.modules.auth.mfa import generate_mfa_secret, get_hotp_token, verify_totp_token
    # Generate secret
    secret = generate_mfa_secret()
    assert len(secret) == 32
    
    # Calculate current step token
    current_step = int(time.time() / 30)
    token = get_hotp_token(secret, current_step)
    assert len(token) == 6
    assert token.isdigit()
    
    # Verify correct token
    assert verify_totp_token(secret, token) is True
    
    # Verify incorrect token
    assert verify_totp_token(secret, "000000") is False
    assert verify_totp_token(secret, "123456") is False
    
    # Verify time drift window
    past_token = get_hotp_token(secret, current_step - 1)
    future_token = get_hotp_token(secret, current_step + 1)
    
    # Drift window of 1 allows past and future tokens
    assert verify_totp_token(secret, past_token, window=1) is True
    assert verify_totp_token(secret, future_token, window=1) is True


def test_mfa_enrollment_and_login_flow(client, db_session):
    import time
    from app.modules.auth.mfa import get_hotp_token
    # 1. Create a user
    user = User(
        username="mfauser",
        hashed_password=get_password_hash("MfaSecurePassword123!"),
        role="user",
        is_active=True
    )
    db_session.add(user)
    db_session.commit()

    # 2. Login to get session cookie for enrollment
    login_resp = client.post("/api/auth/login", json={
        "username": "mfauser",
        "password": "MfaSecurePassword123!"
    })
    assert login_resp.status_code == 200
    
    # 3. Request 2FA enrollment
    enroll_resp = client.post("/api/auth/mfa/enroll")
    assert enroll_resp.status_code == 200
    enroll_data = enroll_resp.json()
    assert "secret" in enroll_data
    assert "provisioning_uri" in enroll_data
    secret = enroll_data["secret"]
    
    # 4. Try verifying with wrong code -> 400
    verify_resp_wrong = client.post("/api/auth/mfa/verify", json={"code": "000000"})
    assert verify_resp_wrong.status_code == 400
    
    # 5. Verify with correct current code -> 200
    current_step = int(time.time() / 30)
    correct_token = get_hotp_token(secret, current_step)
    verify_resp = client.post("/api/auth/mfa/verify", json={"code": correct_token})
    assert verify_resp.status_code == 200
    
    # 6. Log out to clear session
    logout_resp = client.post("/api/auth/logout")
    assert logout_resp.status_code == 200
    
    # Clear client cookies to simulate clean login request
    client.cookies.clear()
    
    # 7. Log in again with password -> Should require MFA
    login_resp_2 = client.post("/api/auth/login", json={
        "username": "mfauser",
        "password": "MfaSecurePassword123!"
    })
    assert login_resp_2.status_code == 200
    assert login_resp_2.json()["status"] == "mfa_required"
    assert "session_token" not in client.cookies
    
    # 8. Post MFA code to complete login
    mfa_step = int(time.time() / 30)
    current_mfa_token = get_hotp_token(secret, mfa_step)
    mfa_login_resp = client.post("/api/auth/login/mfa", json={
        "username": "mfauser",
        "code": current_mfa_token
    })
    assert mfa_login_resp.status_code == 200
    assert mfa_login_resp.json()["username"] == "mfauser"
    assert "session_token" in client.cookies or "__Host-session" in client.cookies
    
    # 9. Verify protected routes are now accessible
    me_resp = client.get("/api/auth/me")
    assert me_resp.status_code == 200
    assert me_resp.json()["username"] == "mfauser"
    
    # 10. Disable MFA
    disable_resp = client.post("/api/auth/mfa/disable")
    assert disable_resp.status_code == 200
    
    # Logout & login without MFA
    client.post("/api/auth/logout")
    client.cookies.clear()
    
    login_resp_no_mfa = client.post("/api/auth/login", json={
        "username": "mfauser",
        "password": "MfaSecurePassword123!"
    })
    assert login_resp_no_mfa.status_code == 200
    assert "status" not in login_resp_no_mfa.json()
    assert "session_token" in client.cookies or "__Host-session" in client.cookies
