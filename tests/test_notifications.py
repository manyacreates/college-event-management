from datetime import date, timedelta


def make_date(days):
    return (date.today() + timedelta(days=days)).isoformat()


def event_payload(**overrides):
    data = {
        "title": "Annual Tech Fest",
        "description": "Annual college technology festival",
        "category": "Technical",
        "event_date": make_date(30),
        "start_time": "10:00",
        "end_time": "16:00",
        "venue": "JIIT Noida",
        "capacity": 50,
    }
    data.update(overrides)
    return data


def create_event(admin_client, **overrides):
    response = admin_client.post("/api/events", json=event_payload(**overrides))
    return response.get_json()["event"]["id"]


def register(client, event_id):
    return client.post(f"/api/events/{event_id}/register")


def cancel(client, event_id):
    return client.delete(f"/api/events/{event_id}/register")


def my_notifications(client):
    return client.get("/api/notifications").get_json()


# ---------- Created by actions ----------

def test_registering_creates_notification(admin_client, student_client):
    event_id = create_event(admin_client)

    register(student_client, event_id)

    data = my_notifications(student_client)
    assert len(data["notifications"]) == 1
    assert "registered" in data["notifications"][0]["message"].lower()
    assert data["notifications"][0]["event_id"] == event_id


def test_cancelling_creates_notification(admin_client, student_client):
    event_id = create_event(admin_client)
    register(student_client, event_id)

    cancel(student_client, event_id)

    data = my_notifications(student_client)
    assert len(data["notifications"]) == 2
    assert "cancel" in data["notifications"][0]["message"].lower()


def test_updating_event_notifies_registered_students(admin_client, student_client):
    event_id = create_event(admin_client)
    register(student_client, event_id)

    admin_client.put(
        f"/api/events/{event_id}", json=event_payload(venue="Main Auditorium")
    )

    data = my_notifications(student_client)
    assert len(data["notifications"]) == 2
    assert "updated" in data["notifications"][0]["message"].lower()


def test_updating_event_does_not_notify_cancelled_students(
    admin_client, student_client
):
    event_id = create_event(admin_client)
    register(student_client, event_id)
    cancel(student_client, event_id)

    admin_client.put(
        f"/api/events/{event_id}", json=event_payload(venue="Main Auditorium")
    )

    assert len(my_notifications(student_client)["notifications"]) == 2


# ---------- Announcements ----------

def test_admin_announcement_notifies_registered_students(
    admin_client, student_client, make_student_client
):
    event_id = create_event(admin_client)
    register(student_client, event_id)
    outsider = make_student_client("outsider@example.com")

    response = admin_client.post(
        f"/api/events/{event_id}/announcements",
        json={"message": "Bring your ID card"},
    )

    assert response.status_code == 201
    student_messages = [
        n["message"] for n in my_notifications(student_client)["notifications"]
    ]
    assert any("Bring your ID card" in m for m in student_messages)
    assert my_notifications(outsider)["notifications"] == []


def test_announcement_requires_message(admin_client):
    event_id = create_event(admin_client)

    response = admin_client.post(
        f"/api/events/{event_id}/announcements", json={"message": "   "}
    )

    assert response.status_code == 400


def test_student_cannot_publish_announcement(admin_client, student_client):
    event_id = create_event(admin_client)

    response = student_client.post(
        f"/api/events/{event_id}/announcements", json={"message": "Hi"}
    )

    assert response.status_code == 403


def test_anonymous_cannot_publish_announcement(client, admin_client):
    event_id = create_event(admin_client)

    response = client.post(
        f"/api/events/{event_id}/announcements", json={"message": "Hi"}
    )

    assert response.status_code == 401


def test_announcement_for_unknown_event_returns_404(admin_client):
    response = admin_client.post(
        "/api/events/9999/announcements", json={"message": "Hi"}
    )

    assert response.status_code == 404


# ---------- Listing and read status ----------

def test_notifications_start_unread(admin_client, student_client):
    event_id = create_event(admin_client)
    register(student_client, event_id)

    data = my_notifications(student_client)

    assert data["notifications"][0]["is_read"] is False
    assert data["unread_count"] == 1


def test_notifications_include_timestamp(admin_client, student_client):
    event_id = create_event(admin_client)
    register(student_client, event_id)

    data = my_notifications(student_client)

    assert data["notifications"][0]["created_at"]


def test_notifications_require_login(client):
    assert client.get("/api/notifications").status_code == 401


def test_admin_cannot_use_student_notifications(admin_client):
    assert admin_client.get("/api/notifications").status_code == 403


def test_mark_notification_as_read(admin_client, student_client):
    event_id = create_event(admin_client)
    register(student_client, event_id)
    notification_id = my_notifications(student_client)["notifications"][0]["id"]

    response = student_client.post(f"/api/notifications/{notification_id}/read")

    assert response.status_code == 200
    data = my_notifications(student_client)
    assert data["notifications"][0]["is_read"] is True
    assert data["unread_count"] == 0


def test_cannot_mark_another_students_notification(
    admin_client, student_client, make_student_client
):
    event_id = create_event(admin_client)
    register(student_client, event_id)
    notification_id = my_notifications(student_client)["notifications"][0]["id"]
    other = make_student_client("other@example.com")

    response = other.post(f"/api/notifications/{notification_id}/read")

    assert response.status_code == 404
    assert my_notifications(student_client)["unread_count"] == 1


def test_mark_unknown_notification_returns_404(student_client):
    assert student_client.post("/api/notifications/9999/read").status_code == 404


def test_mark_all_notifications_as_read(admin_client, student_client):
    event_id = create_event(admin_client)
    register(student_client, event_id)
    cancel(student_client, event_id)

    response = student_client.post("/api/notifications/read-all")

    assert response.status_code == 200
    assert my_notifications(student_client)["unread_count"] == 0


# ---------- Event deletion ----------

def test_deleting_event_keeps_notifications(admin_client, student_client):
    event_id = create_event(admin_client)
    register(student_client, event_id)

    admin_client.delete(f"/api/events/{event_id}")

    data = my_notifications(student_client)
    assert len(data["notifications"]) == 1
    assert data["notifications"][0]["event_id"] is None