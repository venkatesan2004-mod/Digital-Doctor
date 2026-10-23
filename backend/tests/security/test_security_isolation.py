from app.ai.retrieval.vector_store import vector_store


def test_cross_patient_data_isolation(client):
    """
    Verifies Section 16 Requirement:
    Patient session tokens cannot access or modify records of another patient.
    """
    # Verify Patient 1 (Karthik Raja)
    verify_p1 = client.post(
        "/api/v1/kiosk/verify",
        json={"registration_number": "DD-202610-KART01", "verification_factor": "1985"}
    )
    token_p1 = verify_p1.json()["session_token"]
    headers_p1 = {"Authorization": f"Bearer {token_p1}"}

    # Attempt to access Patient 2's session (b2c3d4e5-f6a7-48b9-c0d1-223344556677) using Patient 1's token
    p2_session_id = "b2c3d4e5-f6a7-48b9-c0d1-223344556677"
    res = client.get(
        f"/api/v1/clinical-records/session/{p2_session_id}/history",
        headers=headers_p1
    )
    assert res.status_code == 403
    assert "Cross-patient" in res.json()["detail"] or "Forbidden" in res.json()["detail"]


def test_vector_store_strict_patient_boundary():
    """
    Verifies Section 13 & 16:
    Vector search for Patient 2 MUST NOT retrieve private clinical chunks indexed for Patient 1.
    """
    # Index private note for patient 100
    vector_store.index_document(
        doc_id="private_note_100",
        content="Patient has severe allergy to penicillin and history of anaphylaxis.",
        metadata={
            "patient_id": 100,
            "is_public": False,
            "title": "Private Allergy Record",
            "doc_type": "Allergy Note"
        }
    )

    # Search on behalf of patient 200
    results_for_p200 = vector_store.search_authorized(
        query="penicillin allergy and anaphylaxis",
        patient_id=200,
        limit=5
    )

    # Patient 200 must NOT see patient 100's private record
    retrieved_ids = [doc["id"] for doc in results_for_p200]
    assert "private_note_100" not in retrieved_ids

    # Search on behalf of patient 100
    results_for_p100 = vector_store.search_authorized(
        query="penicillin allergy and anaphylaxis",
        patient_id=100,
        limit=5
    )
    p100_ids = [doc["id"] for doc in results_for_p100]
    assert "private_note_100" in p100_ids
