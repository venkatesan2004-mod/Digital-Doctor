def test_front_office_direct_doctor_pathway(client):
    """
    Verifies Section 4.1 Requirement:
    DIRECT_DOCTOR pathway must dispatch exclusively to mock HIMS
    and NOT allow the patient into the digital kiosk workflow.
    """
    # Authenticate as frontoffice staff
    login = client.post(
        "/api/v1/auth/staff/login",
        json={"username": "frontoffice", "password": "DoctorDemo2026!"}
    )
    token = login.json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}

    payload = {
        "first_name": "Ramesh",
        "last_name": "Chandran",
        "date_of_birth": "1975-04-10",
        "gender": "Male",
        "contact_phone": "+91 99887 76655",
        "preferred_language": "en",
        "department_id": 1,
        "assigned_doctor_id": 1,
        "consultation_type": "DIRECT_DOCTOR"
    }

    res = client.post("/api/v1/front-office/register", json=payload, headers=headers)
    assert res.status_code == 200
    data = res.json()
    assert data["consultation_type"] == "DIRECT_DOCTOR"
    assert data["kiosk_eligible"] is False
    assert data["hims_dispatch_status"] == "DISPATCHED_TO_HIMS"
    assert "Direct Doctor Consultation" in data["message"]


def test_front_office_digital_doctor_pathway(client):
    """
    Verifies Section 4.1 Requirement:
    DIGITAL_DOCTOR pathway creates a valid registration and confirms kiosk eligibility.
    """
    login = client.post(
        "/api/v1/auth/staff/login",
        json={"username": "frontoffice", "password": "DoctorDemo2026!"}
    )
    token = login.json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}

    payload = {
        "first_name": "Ananya",
        "last_name": "Krishnan",
        "date_of_birth": "1992-09-18",
        "gender": "Female",
        "contact_phone": "+91 99887 76656",
        "preferred_language": "ta",
        "department_id": 1,
        "assigned_doctor_id": 1,
        "consultation_type": "DIGITAL_DOCTOR",
        "secondary_verification_pin": "1992"
    }

    res = client.post("/api/v1/front-office/register", json=payload, headers=headers)
    assert res.status_code == 200
    data = res.json()
    assert data["consultation_type"] == "DIGITAL_DOCTOR"
    assert data["kiosk_eligible"] is True
    assert data["registration_number"].startswith("DD-")
    assert "Digital Doctor Consultation" in data["message"]
