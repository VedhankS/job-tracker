import pytest
from app import create_app

@pytest.fixture
def client():
    app = create_app({
        "TESTING":True,
        "SQLALCHEMY_DATABASE_URI":"sqlite:///:memory:",
    })
    with app.test_client() as client:
        yield client

def test_health(client):
    res = client.get("/health")
    assert res.status_code == 200
    assert res.get_json() == {"status":"ok"}

def test_create_and_list_jobs(client):
    res = client.get("/jobs")
    assert res.status_code == 200
    assert res.get_json() == []

    res = client.post("/jobs", json={"company":"Stripe","role":"backend engineer"})
    assert res.status_code == 201
    data =  res.get_json()
    assert data["id"] == 1
    assert data["company"] == "Stripe"
    assert data["role"] == "backend engineer"
    assert data["status"] == "applied"

    res = client.get("/jobs")
    assert len(res.get_json()) == 1

def test_create_job_missing_fields(client):
    created = client.post("/jobs", json={"company":"google","role":"SWE"}).get_json()
    job_id = created["id"]

    res = client.put(f"/jobs/{job_id}", json={"status":"interviewing"})
    assert res.status_code == 200
    assert res.get_json()["status"] == "interviewing"
    assert res.get_json()["company"] == "google"
    res = client.delete(f"/jobs/{job_id}")
    assert res.status_code == 204

    res = client.get(f"/jobs/{job_id}")
    assert res.status_code == 404
    assert res.get_json() == {"error":"Not Found"}
def test_update_and_delete_job(client):
    # 1. Create a job first
    created = client.post("/jobs", json={"company": "Google", "role": "SWE"}).get_json()
    job_id = created["id"]

        # 2. Update its status
    res = client.put(f"/jobs/{job_id}", json={"status": "interviewing"})
    assert res.status_code == 200
    assert res.get_json()["status"] == "interviewing"
    assert res.get_json()["company"] == "Google"  # unchanged field stays intact

        # 3. Delete the job
    res = client.delete(f"/jobs/{job_id}")
    assert res.status_code == 204

        # 4. Confirm fetching it now returns 404
    res = client.get(f"/jobs/{job_id}")
    assert res.status_code == 404
    assert res.get_json() == {"error": "Not Found"}
