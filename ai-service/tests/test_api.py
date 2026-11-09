import requests
import pytest

BASE_URL = "http://localhost:5002"

def test_health_check():
    """Ensure the API is accessible."""
    response = requests.get(f"{BASE_URL}/health")
    assert response.status_code == 200
    assert response.json() == {"status": "ok"}

def test_agent_schema_enforcement():
    """
    Evaluates if the LangGraph agent strictly returns the 4 required dictionary keys
    for the frontend UI, regardless of local LLM variance.
    """
    payload = {
        "text": "Looking for a Junior React developer with TypeScript experience."
    }

    response = requests.post(f"{BASE_URL}/agent/run", json=payload)
    assert response.status_code == 200, f"API failed with: {response.text}"

    data = response.json()
    assert "copilot_results" in data

    results = data["copilot_results"]

    # 1. Verify Analysis Node
    assert "analysis" in results
    assert "required_skills" in results["analysis"]
    assert isinstance(results["analysis"]["required_skills"], list)

    # 2. Verify Match Node
    assert "match_data" in results
    assert "score" in results["match_data"]
    assert isinstance(results["match_data"]["score"], int)

    # 3. Verify Tailor Node
    assert "tailored_bullets" in results
    assert isinstance(results["tailored_bullets"], list)

    # 4. Verify Prep Node
    assert "prep_questions" in results
    assert isinstance(results["prep_questions"], list)
