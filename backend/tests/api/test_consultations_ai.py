def test_consultation_ai_rag_response_format(client):
    """
    Verifies Section 6.3:
    AI response conforms to the validated StructuredAIResponse schema.
    """
    session_id = "a1b2c3d4-e5f6-47a8-b9c0-112233445566"

    # Verify session and get token
    verify_res = client.post(
        "/api/v1/kiosk/verify",
        json={"registration_number": "DD-202610-KART01", "verification_factor": "1985"}
    )
    token = verify_res.json()["session_token"]
    headers = {"Authorization": f"Bearer {token}"}

    payload = {
        "session_id": session_id,
        "message": "I have had a mild dry cough and slight fever for two days.",
        "language": "en"
    }

    res = client.post("/api/v1/consultations/message", json=payload, headers=headers)
    assert res.status_code == 200
    data = res.json()

    assert "answer" in data
    assert "symptom_summary" in data
    assert "source_references" in data
    assert len(data["source_references"]) > 0
    assert "uncertainties" in data
    assert len(data["uncertainties"]) > 0
    assert data["requires_clinician_review"] is True
    assert data["response_status"] == "COMPLETED"


def test_consultation_ai_emergency_detection(client):
    """
    Verifies Section 7.1:
    Emergency red-flag symptom input immediately escalates with emergency warnings.
    """
    session_id = "a1b2c3d4-e5f6-47a8-b9c0-112233445566"

    verify_res = client.post(
        "/api/v1/kiosk/verify",
        json={"registration_number": "DD-202610-KART01", "verification_factor": "1985"}
    )
    token = verify_res.json()["session_token"]
    headers = {"Authorization": f"Bearer {token}"}

    payload = {
        "session_id": session_id,
        "message": "I am experiencing severe chest pain radiating to left arm and cannot breathe.",
        "language": "en"
    }

    res = client.post("/api/v1/consultations/message", json=payload, headers=headers)
    assert res.status_code == 200
    data = res.json()

    assert data["response_status"] == "EMERGENCY_ESCALATION"
    assert len(data["safety_alerts"]) > 0
    assert any("CRITICAL EMERGENCY" in alert for alert in data["safety_alerts"])
