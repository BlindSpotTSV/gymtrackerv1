def login(client, email="member@example.com"):
    response = client.post(
        "/api/auth/login",
        json={"email": email, "password": "test-password-123"},
    )
    assert response.status_code == 200


def test_member_can_log_workout(client):
    login(client)
    response = client.post(
        "/api/workouts",
        json={
            "name": "Push Day",
            "sets": [
                {"exercise_id": 1, "set_number": 1, "reps": 10, "weight_kg": 40},
                {"exercise_id": 1, "set_number": 2, "reps": 8, "weight_kg": 45},
            ],
        },
    )
    assert response.status_code == 201
    body = response.get_json()
    assert body["workout"]["name"] == "Push Day"
    assert len(body["workout"]["sets"]) == 2


def test_member_cannot_access_coach_endpoint(client):
    login(client)
    response = client.get("/api/coach/clients")
    assert response.status_code == 403


def test_member_cannot_read_missing_workout(client):
    login(client)
    response = client.get("/api/workouts/9999")
    assert response.status_code == 404
