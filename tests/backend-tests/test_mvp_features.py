from fastapi.testclient import TestClient

from backend.api.main import app

client = TestClient(app)


def test_auth_assessment_and_skill_gap_flow() -> None:
    register_payload = {
        "name": "Student One",
        "email": "student1@example.com",
        "password": "secure123",
        "education_level": "Undergraduate",
        "current_skills": ["Python", "Basic Math"],
        "target_role": "AI Engineer",
        "learning_goals": ["Become ML Engineer"],
    }
    register_response = client.post("/api/register", json=register_payload)
    assert register_response.status_code == 200

    token = register_response.json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}

    assessment_start = client.get("/api/assessment/start", headers=headers)
    assert assessment_start.status_code == 200
    assert assessment_start.json()["target_role"] == "AI Engineer"

    submit_payload = {
        "scores": {
            "Python": 80,
            "Statistics": 25,
            "Linear Algebra": 15,
            "Machine Learning": 10,
            "Deep Learning": 5,
        }
    }
    submit_response = client.post("/api/assessment/submit", json=submit_payload, headers=headers)
    assert submit_response.status_code == 200

    result_response = client.get("/api/assessment/result", headers=headers)
    assert result_response.status_code == 200
    assert result_response.json()["scores"]["Python"] == 80

    gap_response = client.get("/api/skill-gap/analyze", headers=headers)
    assert gap_response.status_code == 200
    body = gap_response.json()
    assert body["target_role"] == "AI Engineer"
    assert "readiness_percent" in body
    assert len(body["skills"]) > 0
