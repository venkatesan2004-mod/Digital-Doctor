def test_staff_login_success(client):
    """Verifies that an authorized clinician can authenticate with demo credentials."""
    response = client.post(
        "/api/v1/auth/staff/login",
        json={"username": "dr.anand", "password": "DoctorDemo2026!"}
    )
    assert response.status_code == 200
    data = response.json()
    assert "access_token" in data
    assert data["token_type"] == "bearer"
    assert data["role"] == "DOCTOR"
    assert "Dr. Anand" in data["full_name"]


def test_staff_login_invalid_credentials(client):
    """Verifies that incorrect credentials are rejected with HTTP 401."""
    response = client.post(
        "/api/v1/auth/staff/login",
        json={"username": "dr.anand", "password": "WrongPassword123!"}
    )
    assert response.status_code == 401
    assert "Invalid username or password" in response.json()["detail"]


def test_staff_me_endpoint_authorized(client):
    """Verifies /auth/staff/me returns staff profile when authenticated."""
    login_res = client.post(
        "/api/v1/auth/staff/login",
        json={"username": "dr.anand", "password": "DoctorDemo2026!"}
    )
    token = login_res.json()["access_token"]

    me_res = client.get(
        "/api/v1/auth/staff/me",
        headers={"Authorization": f"Bearer {token}"}
    )
    assert me_res.status_code == 200
    me_data = me_res.json()
    assert me_data["username"] == "dr.anand"
    assert me_data["role"] == "DOCTOR"
