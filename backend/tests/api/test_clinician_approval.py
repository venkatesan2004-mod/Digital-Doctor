def test_clinician_review_queue_and_approval(client):
    """
    Verifies Section 7:
    Mandatory human-in-the-loop review.
    AI drafts start in DRAFT_PENDING_REVIEW and require clinician approval.
    """
    # Login as Dr. Anand
    login = client.post(
        "/api/v1/auth/staff/login",
        json={"username": "dr.anand", "password": "DoctorDemo2026!"}
    )
    token = login.json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}

    # Fetch queue
    queue_res = client.get("/api/v1/clinician-review/queue", headers=headers)
    assert queue_res.status_code == 200
    queue = queue_res.json()
    assert len(queue) > 0

    first_item = queue[0]
    item_type = first_item["item_type"]
    item_id = first_item["item_id"]

    # Approve item
    action_res = client.post(
        f"/api/v1/clinician-review/action/{item_type}/{item_id}",
        json={"action": "APPROVE", "notes": "Clinically indicated based on fever history."},
        headers=headers
    )
    assert action_res.status_code == 200
    data = action_res.json()
    assert data["review_status"] == "APPROVED"
    assert "APPROVED" in data["message"]


def test_unauthorized_user_cannot_approve_clinical_draft(client):
    """Staff without DOCTOR or ADMIN role cannot approve clinical orders."""
    # Login as frontoffice staff
    login = client.post(
        "/api/v1/auth/staff/login",
        json={"username": "frontoffice", "password": "DoctorDemo2026!"}
    )
    token = login.json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}

    action_res = client.post(
        "/api/v1/clinician-review/action/MEDICATION_ORDER/1",
        json={"action": "APPROVE"},
        headers=headers
    )
    assert action_res.status_code == 403
