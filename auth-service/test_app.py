import pytest
from app import create_app

@pytest.fixture
def client():
    app = create_app({
        "TESTING": True,
        "SQLALVHEMY_DATABASE_URI":"sqlite:///:memory",
        "JWT_SECRET_KEY":"test-secret-key-at-least-32-bytes-long"
    })
    with app.test_client() as client:
        yield client
def test_health(client):
    res = client.get("/health")
    assert res.status_code == 200
    assert res.get_json() == {"status":"ok"}
def test_register_and_duplicate(client):
    res = client.post(
        "/register",
        json = {"email":"test@example.com","password":"password123"},
    )
    assert res.status_code == 201
    assert res.get_json()["email"] == "test@example.com"

    res_dup = client.post(
        "/register",
        json = {"email":"test@example.com","password":"password123"}
    )
    assert res_dup.status_code == 409
def test_login_success_and_failure(client):
    client.post(
        "/register",
        json={"email":"login@example.com","password":"correctpassword"},
    )
    res_ok = client.post(
        "/login",
        json = {"email":"login@example.com","password":"correctpassword"},
    )
    assert res_ok.status_code == 200
    assert "access_token" in res_ok.get_json()

    res_bad = client.post(
        "/login",
        json = {"email":"login@example.com","password":"wrongpassword"},
    )
    assert res_bad.status_code == 401
