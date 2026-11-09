import pytest
from unittest.mock import patch, MagicMock
from app import create_app
from flask_jwt_extended import create_access_token

@pytest.fixture
def app():
    return create_app({
        "TESTING": True,
        "SQLALCHEMY_DATABASE_URI": "sqlite:///:memory:",
        "JWT_SECRET_KEY": "test-secret-key",
        "AI_SERVICE_URL": "http://ai-service:5002",
    })

@pytest.fixture
def client(app):
    with app.test_client() as client:
        yield client

@pytest.fixture
def auth_headers(app):
    with app.app_context():
        token = create_access_token(identity="1")
    return {"Authorization": f"Bearer {token}"}

def test_health(client):
    res = client.get("/health")
    assert res.status_code == 200
    assert res.get_json() == {"status": "ok"}

def test_unauthorized_access_blocked(client):
    res = client.get("/jobs")
    assert res.status_code == 401

def test_create_and_list_jobs(client, auth_headers):
    res = client.get("/jobs", headers=auth_headers)
    assert res.status_code == 200
    assert res.get_json() == []

    res = client.post("/jobs", json={"company": "Stripe", "role": "backend engineer"}, headers=auth_headers)
    assert res.status_code == 201
    data = res.get_json()
    assert data["user_id"] == 1
    assert data["company"] == "Stripe"
    assert data["role"] == "backend engineer"
    assert data["status"] == "applied"
    assert data["match_score"] is None
    assert data["tailored_bullets"] == []

    res = client.get("/jobs", headers=auth_headers)
    assert len(res.get_json()) == 1

def test_create_job_missing_fields(client, auth_headers):
    res = client.post("/jobs", json={"company": "Stripe"}, headers=auth_headers)
    assert res.status_code == 400

def test_update_and_delete_job(client, auth_headers):
    created = client.post("/jobs", json={"company": "Google", "role": "SWE"}, headers=auth_headers).get_json()
    job_id = created["id"]

    res = client.put(f"/jobs/{job_id}", json={"status": "interviewing"}, headers=auth_headers)
    assert res.status_code == 200
    assert res.get_json()["status"] == "interviewing"
    assert res.get_json()["company"] == "Google"

    res = client.delete(f"/jobs/{job_id}", headers=auth_headers)
    assert res.status_code == 204

    res = client.get(f"/jobs/{job_id}", headers=auth_headers)
    assert res.status_code == 404

def test_save_and_retrieve_ai_fields(client, auth_headers):
    created = client.post("/jobs", json={"company": "OpenAI", "role": "Research Engineer"}, headers=auth_headers).get_json()
    job_id = created["id"]

    update_payload = {
        "match_score": 92,
        "tailored_bullets": ["Implemented RAG pipeline reducing latency by 40%"],
        "prep_questions": ["Explain vector embeddings vs BM25."],
        "skills": ["Python", "PyTorch", "ChromaDB"],
        "job_description": "Looking for PyTorch and RAG engineer.",
    }
    res = client.put(f"/jobs/{job_id}", json=update_payload, headers=auth_headers)
    assert res.status_code == 200
    data = res.get_json()
    assert data["match_score"] == 92
    assert data["tailored_bullets"] == ["Implemented RAG pipeline reducing latency by 40%"]
    assert data["prep_questions"] == ["Explain vector embeddings vs BM25."]
    assert data["skills"] == ["Python", "PyTorch", "ChromaDB"]
    assert data["job_description"] == "Looking for PyTorch and RAG engineer."

def test_copilot_service_integration(client, auth_headers):
    created = client.post("/jobs", json={"company": "Anthropic", "role": "AI Engineer"}, headers=auth_headers).get_json()
    job_id = created["id"]

    mock_ai_response = {
        "copilot_results": {
            "analysis": {"title": "AI Engineer", "required_skills": ["Python", "LangGraph"]},
            "match_data": {"score": 88, "matches": []},
            "tailored_bullets": [{"bullet": "Built LangGraph workflow", "source_chunk_id": "chunk-0"}],
            "prep_questions": ["What is a stateful LangGraph node?"]
        }
    }

    with patch("requests.post") as mock_post:
        mock_resp = MagicMock()
        mock_resp.status_code = 200
        mock_resp.json.return_value = mock_ai_response
        mock_post.return_value = mock_resp

        res = client.post(
            f"/jobs/{job_id}/copilot",
            json={"text": "Seeking engineer skilled in Python and LangGraph."},
            headers=auth_headers
        )
        assert res.status_code == 200
        data = res.get_json()
        assert "job" in data
        assert data["job"]["match_score"] == 88
        assert data["job"]["skills"] == ["Python", "LangGraph"]
        assert data["job"]["tailored_bullets"] == ["Built LangGraph workflow"]
        assert data["job"]["prep_questions"] == ["What is a stateful LangGraph node?"]

def test_proxy_resume_index(client, auth_headers):
    with patch("requests.post") as mock_post:
        mock_resp = MagicMock()
        mock_resp.status_code = 201
        mock_resp.json.return_value = {"chunks_indexed": 5}
        mock_post.return_value = mock_resp

        res = client.post(
            "/resume/index",
            json={"text": "Experienced Python Engineer. 5 years building microservices."},
            headers=auth_headers
        )
        assert res.status_code == 201
        assert res.get_json() == {"chunks_indexed": 5}

def test_proxy_resume_upload(client, auth_headers):
    import io
    with patch("requests.post") as mock_post:
        mock_resp = MagicMock()
        mock_resp.status_code = 201
        mock_resp.json.return_value = {"chunks_indexed": 6, "filename": "resume.pdf"}
        mock_post.return_value = mock_resp

        fake_pdf = (io.BytesIO(b"%PDF-1.4 fake pdf binary data"), "resume.pdf")
        res = client.post(
            "/resume/upload",
            data={"file": fake_pdf},
            content_type="multipart/form-data",
            headers=auth_headers
        )
        assert res.status_code == 201
        assert res.get_json()["chunks_indexed"] == 6

def test_user_isolation(app, client, auth_headers):
    created = client.post("/jobs", json={"company": "Meta", "role": "AI Engineer"}, headers=auth_headers).get_json()
    job_id = created["id"]

    with app.app_context():
        user2_token = create_access_token(identity="2")
    user2_headers = {"Authorization": f"Bearer {user2_token}"}
    assert client.get("/jobs", headers=user2_headers).get_json() == []
    assert client.get(f"/jobs/{job_id}", headers=user2_headers).status_code == 404
