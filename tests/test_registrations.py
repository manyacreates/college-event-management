from datetime import date, timedelta


def make_date(days):
    return (date.today() + timedelta(days=days)).isoformat()


def create_event(admin_client, capacity=50, days=30):
    """Helper: create an event through the API and return its id."""
    response = admin_client.post("/api/events", json={
        "title": "Annual Tech Fest",
        "description": "Annual college technology festival",
        "category": "Technical",
        "event_date": make_date(days),
        "start_time": "10:00",
        "end_time": "16:00",
        "venue": "JIIT Noida",
        "capacity": capacity,
    })
    return response.get_json()["event"]["id"]


def register(client, event_id):
    return client.post(f"/api/events/{event_id}/register")


def cancel(client, event_id):
    return client.delete(f"/api/events/{event_id}/register")


# ---------- Register ----------

def test_student_can_register_for_event(admin_client, student_client):
    event_id = create_event(admin_client)

    response = register(student_client, event_id)

    assert response.status_code == 201
    assert response.get_json()["registration"]["status"] == "registered"


def test_duplicate_registration_is_rejected(admin_client, student_client):
    event_id = create_event(admin_client)
    register(student_client, event_id)

    response = register(student_client, event_id)

    assert response.status_code == 409


def test_registration_rejected_when_event_is_full(
    admin_client, student_client, make_student_client
):
    event_id = create_event(admin_client, capacity=1)
    register(student_client, event_id)
    second_student = make_student_client("second@example.com")

    response = register(second_student, event_id)

    assert response.status_code == 409


def test_registration_rejected_for_past_event(admin_client, student_client):
    event_id = create_event(admin_client, days=-5)

    response = register(student_client, event_id)

    assert response.status_code == 400


def test_register_for_unknown_event_returns_404(student_client):
    response = register(student_client, 9999)

    assert response.status_code == 404


def test_admin_cannot_register_for_event(admin_client):
    event_id = create_event(admin_client)

    response = register(admin_client, event_id)

    assert response.status_code == 403


def test_anonymous_cannot_register_for_event(client, admin_client):
    event_id = create_event(admin_client)

    response = register(client, event_id)

    assert response.status_code == 401


# ---------- Cancel ----------

def test_student_can_cancel_registration(admin_client, student_client):
    event_id = create_event(admin_client)
    register(student_client, event_id)

    response = cancel(student_client, event_id)

    assert response.status_code == 200
    mine = student_client.get("/api/registrations/me").get_json()
    assert mine["registrations"][0]["status"] == "cancelled"


def test_cancel_without_registration_returns_404(admin_client, student_client):
    event_id = create_event(admin_client)

    response = cancel(student_client, event_id)

    assert response.status_code == 404


def test_cancel_twice_returns_404(admin_client, student_client):
    event_id = create_event(admin_client)
    register(student_client, event_id)
    cancel(student_client, event_id)

    response = cancel(student_client, event_id)

    assert response.status_code == 404


def test_anonymous_cannot_cancel_registration(client, admin_client):
    event_id = create_event(admin_client)

    response = cancel(client, event_id)

    assert response.status_code == 401


def test_cancellation_frees_a_seat(
    admin_client, student_client, make_student_client
):
    event_id = create_event(admin_client, capacity=1)
    register(student_client, event_id)
    cancel(student_client, event_id)
    second_student = make_student_client("second@example.com")

    response = register(second_student, event_id)

    assert response.status_code == 201


def test_student_can_register_again_after_cancelling(
    admin_client, student_client
):
    event_id = create_event(admin_client)
    register(student_client, event_id)
    cancel(student_client, event_id)

    response = register(student_client, event_id)

    assert response.status_code == 201
    mine = student_client.get("/api/registrations/me").get_json()
    assert len(mine["registrations"]) == 1
    assert mine["registrations"][0]["status"] == "registered"


# ---------- My registrations ----------

def test_student_sees_own_registrations(admin_client, student_client):
    event_id = create_event(admin_client)
    register(student_client, event_id)

    response = student_client.get("/api/registrations/me")

    assert response.status_code == 200
    registrations = response.get_json()["registrations"]
    assert len(registrations) == 1
    assert registrations[0]["event"]["id"] == event_id


def test_my_registrations_requires_login(client):
    response = client.get("/api/registrations/me")

    assert response.status_code == 401


# ---------- Participants (admin) ----------

def test_admin_can_list_participants(
    admin_client, student_client, make_student_client
):
    event_id = create_event(admin_client)
    register(student_client, event_id)
    other = make_student_client("other@example.com")
    register(other, event_id)
    cancel(other, event_id)

    response = admin_client.get(f"/api/events/{event_id}/participants")

    assert response.status_code == 200
    participants = response.get_json()["participants"]
    assert [p["email"] for p in participants] == ["student@example.com"]


def test_student_cannot_list_participants(admin_client, student_client):
    event_id = create_event(admin_client)

    response = student_client.get(f"/api/events/{event_id}/participants")

    assert response.status_code == 403


def test_anonymous_cannot_list_participants(client, admin_client):
    event_id = create_event(admin_client)

    response = client.get(f"/api/events/{event_id}/participants")

    assert response.status_code == 401


def test_participants_of_unknown_event_returns_404(admin_client):
    response = admin_client.get("/api/events/9999/participants")

    assert response.status_code == 404


# ---------- Availability ----------

def test_event_shows_registered_count_and_spots_left(
    client, admin_client, student_client
):
    event_id = create_event(admin_client, capacity=10)
    register(student_client, event_id)

    event = client.get(f"/api/events/{event_id}").get_json()["event"]

    assert event["registered_count"] == 1
    assert event["spots_left"] == 9