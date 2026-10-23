def test_kiosk_lookup_masks_identity(client):
    """
    Verifies Section 4.3 Requirement:
    Lookup screen masks patient identity and does not expose medical details.
    """
    res = client.post("/api/v1/kiosk/lookup", json={"registration_number": "DD-202610-KART01"})
    assert res.status_code == 200
    data = res.json()
    assert data["registration_number"] == "DD-202610-KART01"
    # Should be masked (e.g. K*** R***)
    assert "***" in data["masked_patient_name"]
    assert "Karthik Raja" not in data["masked_patient_name"]
    assert data["requires_verification"] is True


def test_kiosk_direct_doctor_registration_rejected_at_kiosk(client):
    """Direct doctor registration cannot enter the digital kiosk."""
    res = client.post("/api/v1/kiosk/lookup", json={"registration_number": "HIMS-OPD-78912"})
    assert res.status_code == 404


def test_kiosk_verification_and_session_lifecycle(client):
    """
    Verifies full kiosk verification, session creation/resumption, and closure.
    """
    # 1. Verify with correct birth year "1985"
    verify_res = client.post(
        "/api/v1/kiosk/verify",
        json={"registration_number": "DD-202610-KART01", "verification_factor": "1985"}
    )
    assert verify_res.status_code == 200
    auth_data = verify_res.json()
    assert "session_token" in auth_data
    assert auth_data["patient_full_name"] == "Karthik Raja"

    kiosk_token = auth_data["session_token"]
    headers = {"Authorization": f"Bearer {kiosk_token}"}

    # 2. Start or Resume session
    session_res = client.post(
        "/api/v1/kiosk/session/create-or-resume",
        json={"registration_number": "DD-202610-KART01"},
        headers=headers
    )
    assert session_res.status_code == 200
    session_data = session_res.json()
    session_id = session_data["session_id"]
    assert session_data["status"] in ["ACTIVE", "CREATED", "AWAITING_CLINICIAN_REVIEW"]

    # 3. Close consultation session
    close_res = client.post(
        "/api/v1/kiosk/session/close",
        json={"session_id": session_id, "reason": "Patient Completed Consultation"},
        headers=headers
    )
    assert close_res.status_code == 200
    assert close_res.json()["status"] == "CLOSED"
