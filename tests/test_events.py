from datetime import date, timedelta

import pytest


def future_date(days=30):
    """A date in the future, so the tests never go stale."""
    return (date.today() + timedelta(days=days)).isoformat()


def valid_event(**overrides):
    data = {
        "title": "Annual Tech Fest",
        "description": "Annual college technology festival",
        "category": "Technical",
        "event_date": future_date(),
        "start_time": "10:00",
        "end_time": "16:00",
        "venue": "JIIT Noida",
        "capacity": 200,
    }
    data.update(overrides)
    return data


def create_event(admin_client, **overrides):
    """Helper: create an event through the API and return its id."""
    response = admin_client.post("/api/events", json=valid_event(**overrides))
    return response.get_json()["event"]["id"]


# ---------- List ----------

def test_get_events_returns_empty_list(client):
    response = client.get("/api/events")

    assert response.status_code == 200
    assert response.get_json()["events"] == []


def test_anonymous_user_can_list_events(client, admin_client):
    create_event(admin_client)

    response = client.get("/api/events")

    assert response.status_code == 200
    assert len(response.get_json()["events"]) == 1


def test_search_events_by_title(client, admin_client):
    create_event(admin_client, title="Robotics Workshop", category="Workshops")
    create_event(admin_client, title="Dance Night", category="Cultural")

    response = client.get("/api/events?q=robotics")

    titles = [e["title"] for e in response.get_json()["events"]]
    assert titles == ["Robotics Workshop"]


def test_filter_events_by_category(client, admin_client):
    create_event(admin_client, title="Robotics Workshop", category="Workshops")
    create_event(admin_client, title="Dance Night", category="Cultural")

    response = client.get("/api/events?category=Cultural")

    titles = [e["title"] for e in response.get_json()["events"]]
    assert titles == ["Dance Night"]


# ---------- Create ----------

def test_admin_can_create_event(admin_client):
    response = admin_client.post("/api/events", json=valid_event())

    assert response.status_code == 201
    event = response.get_json()["event"]
    assert event["title"] == "Annual Tech Fest"
    assert event["capacity"] == 200
    assert event["category"] == "Technical"
    assert event["id"] is not None


def test_student_cannot_create_event(student_client):
    response = student_client.post("/api/events", json=valid_event())

    assert response.status_code == 403


def test_anonymous_cannot_create_event(client):
    response = client.post("/api/events", json=valid_event())

    assert response.status_code == 401


def test_create_event_without_title_fails(admin_client):
    data = valid_event()
    del data["title"]

    response = admin_client.post("/api/events", json=data)

    assert response.status_code == 400


def test_create_event_with_invalid_category_fails(admin_client):
    response = admin_client.post("/api/events", json=valid_event(category="Gaming"))

    assert response.status_code == 400


@pytest.mark.parametrize("bad_capacity", [0, -5, "abc", 10.5, None])
def test_create_event_with_invalid_capacity_fails(admin_client, bad_capacity):
    response = admin_client.post(
        "/api/events", json=valid_event(capacity=bad_capacity)
    )

    assert response.status_code == 400


def test_create_event_with_invalid_date_fails(admin_client):
    response = admin_client.post(
        "/api/events", json=valid_event(event_date="31-12-2030")
    )

    assert response.status_code == 400


def test_create_event_with_end_before_start_fails(admin_client):
    response = admin_client.post(
        "/api/events", json=valid_event(start_time="16:00", end_time="10:00")
    )

    assert response.status_code == 400


# ---------- Detail ----------

def test_get_event_details(client, admin_client):
    event_id = create_event(admin_client)

    response = client.get(f"/api/events/{event_id}")

    assert response.status_code == 200
    assert response.get_json()["event"]["title"] == "Annual Tech Fest"


def test_get_unknown_event_returns_404(client):
    response = client.get("/api/events/9999")

    assert response.status_code == 404


# ---------- Update ----------

def test_admin_can_update_event(admin_client):
    event_id = create_event(admin_client)

    response = admin_client.put(
        f"/api/events/{event_id}", json=valid_event(title="Updated Fest")
    )

    assert response.status_code == 200
    assert response.get_json()["event"]["title"] == "Updated Fest"


def test_update_persists_in_database(client, admin_client):
    event_id = create_event(admin_client)
    admin_client.put(
        f"/api/events/{event_id}", json=valid_event(venue="Auditorium")
    )

    response = client.get(f"/api/events/{event_id}")

    assert response.get_json()["event"]["venue"] == "Auditorium"


def test_student_cannot_update_event(admin_client, student_client):
    event_id = create_event(admin_client)

    response = student_client.put(
        f"/api/events/{event_id}", json=valid_event(title="Hacked")
    )

    assert response.status_code == 403


def test_anonymous_cannot_update_event(client, admin_client):
    event_id = create_event(admin_client)

    response = client.put(f"/api/events/{event_id}", json=valid_event())

    assert response.status_code == 401


def test_update_with_invalid_data_fails(admin_client):
    event_id = create_event(admin_client)

    response = admin_client.put(
        f"/api/events/{event_id}", json=valid_event(capacity=0)
    )

    assert response.status_code == 400


def test_update_unknown_event_returns_404(admin_client):
    response = admin_client.put("/api/events/9999", json=valid_event())

    assert response.status_code == 404


# ---------- Delete ----------

def test_admin_can_delete_event(client, admin_client):
    event_id = create_event(admin_client)

    response = admin_client.delete(f"/api/events/{event_id}")

    assert response.status_code == 200
    assert client.get(f"/api/events/{event_id}").status_code == 404


def test_student_cannot_delete_event(admin_client, student_client):
    event_id = create_event(admin_client)

    response = student_client.delete(f"/api/events/{event_id}")

    assert response.status_code == 403


def test_anonymous_cannot_delete_event(client, admin_client):
    event_id = create_event(admin_client)

    response = client.delete(f"/api/events/{event_id}")

    assert response.status_code == 401


def test_delete_unknown_event_returns_404(admin_client):
    response = admin_client.delete("/api/events/9999")

    assert response.status_code == 404