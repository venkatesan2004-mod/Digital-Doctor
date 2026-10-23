def test_health_check_endpoint(client):
    """Verifies that the /health endpoint reports operational status and runtime details."""
    response = client.get("/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "OPERATIONAL"
    assert "Digital Doctor" in data["app_name"]
    assert "timestamp" in data
    assert "database" in data
    assert "ai_provider" in data
