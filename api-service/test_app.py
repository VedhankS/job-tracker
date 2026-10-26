import pytest
from werkzeug.datastructures import auth, headers
from app import create_app
from flask_jwt_extended import create_access_token

@pytest.fixture
def app():
    return create_app({
        "TESTING" :True,
        "SQLALCHEMY_DATABASE_URI":"sqlite:///:memory:",
        "JWT_SECRET_KEY":"test-secret-key",
    })

@pytest.fixture
def client(app):
    with app.test_client() as client:
        yield client

@pytest.fixture
def auth_headers(app):
    with app.app_context():
        token = create_access_token(identity = "1")
    return {"Authorization":f"Bearer {token}"}

def test_health(client):
    res = client.get("/health")
    assert res.status_code == 200
    assert res.get_json() == {"status":"ok"}

def test_unauthorized_access_blocked(client):
    res = client.get("/jobs")
    assert res.status_code == 401

def test_create_and_list_jobs(client,auth_headers):
    res = client.get("/jobs",headers = auth_headers)
    assert res.status_code == 200
    assert res.get_json() == []

    res = client.post("/jobs", json={"company":"Stripe","role":"backend engineer"},headers = auth_headers)
    assert res.status_code == 201
    data =  res.get_json()
    assert data["user_id"] == 1
    assert data["company"] == "Stripe"
    assert data["role"] == "backend engineer"
    assert data["status"] == "applied"

    res = client.get("/jobs", headers=auth_headers)
    assert len(res.get_json()) == 1

def test_create_job_missing_fields(client,auth_headers):
    res = client.post("/jobs",json={"company":"Stripe"},headers=auth_headers)
    assert res.status_code == 400

def test_update_and_delete_job(client,auth_headers):
    created = client.post("/jobs", json={"company": "Google", "role": "SWE"},headers = auth_headers).get_json()
    job_id = created["id"]

    res = client.put(f"/jobs/{job_id}", json={"status": "interviewing"},headers = auth_headers)
    assert res.status_code == 200
    assert res.get_json()["status"] == "interviewing"
    assert res.get_json()["company"] == "Google"

    res = client.delete(f"/jobs/{job_id}",headers = auth_headers)
    assert res.status_code == 204

    res = client.get(f"/jobs/{job_id}",headers = auth_headers)
    assert res.status_code == 404

def test_user_isolation(app,client,auth_headers):
    created = client.post("/jobs",json={"company":"Meta","role":"AI Engineer"},headers = auth_headers).get_json()
    job_id = created["id"]

    with app.app_context():
        user2_token = create_access_token(identity="2")
    user2_headers = {"Authorization":f"Bearer {user2_token}"}
    assert client.get("/jobs",headers = user2_headers).get_json() == []
    assert client.get(f"/jobs/{job_id}",headers = user2_headers).status_code == 404
