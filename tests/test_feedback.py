from datetime import date, timedelta

import pytest


def make_date(days):
    return (date.today() + timedelta(days=days)).isoformat()


def event_payload(days=30):
    return {
        "title": "Annual Tech Fest",
        "description": "Annual college technology festival",
        "category": "Technical",
        "event_date": make_date(days),
        "start_time": "10:00",
        "end_time": "16:00",
        "venue": "JIIT Noida",
        "capacity": 50,
    }


def create_event(admin_client, days=30):
    response = admin_client.post("/api/events", json=event_payload(days))
    return response.get_json()["event"]["id"]


def register(client, event_id):
    return client.post(f"/api/events/{event_id}/register")


def end_event(admin_client, event_id):
    """Move the event into the past, as if it had finished."""
    response = admin_client.put(
        f"/api/events/{event_id}", json=event_payload(days=-5)
    )
    assert response.status_code == 200


def ended_event_with_student(admin_client, student_client):
    """Helper: an event that has ended, with the student registered."""
    event_id = create_event(admin_client)
    register(student_client, event_id)
    end_event(admin_client, event_id)
    return event_id


def submit(client, event_id, rating=5, comments="Great event"):
    return client.post(
        f"/api/events/{event_id}/feedback",
        json={"rating": rating, "comments": comments},
    )


# ---------- Submit ----------

def test_student_can_submit_feedback(admin_client, student_client):
    event_id = ended_event_with_student(admin_client, student_client)

    response = submit(student_client, event_id, rating=4, comments="Loved it")

    assert response.status_code == 201
    feedback = response.get_json()["feedback"]
    assert feedback["rating"] == 4
    assert feedback["comments"] == "Loved it"


def test_feedback_without_comments_is_allowed(admin_client, student_client):
    event_id = ended_event_with_student(admin_client, student_client)

    response = student_client.post(
        f"/api/events/{event_id}/feedback", json={"rating": 3}
    )

    assert response.status_code == 201


def test_feedback_rejected_before_event_ends(admin_client, student_client):
    event_id = create_event(admin_client)
    register(student_client, event_id)

    response = submit(student_client, event_id)

    assert response.status_code == 400


@pytest.mark.parametrize("bad_rating", [0, 6, -1, "5", 3.5, True, None])
def test_feedback_with_invalid_rating_fails(
    admin_client, student_client, bad_rating
):
    event_id = ended_event_with_student(admin_client, student_client)

    response = submit(student_client, event_id, rating=bad_rating)

    assert response.status_code == 400


def test_feedback_with_too_long_comment_fails(admin_client, student_client):
    event_id = ended_event_with_student(admin_client, student_client)

    response = submit(student_client, event_id, comments="x" * 1001)

    assert response.status_code == 400


def test_unregistered_student_cannot_submit_feedback(
    admin_client, student_client, make_student_client
):
    event_id = ended_event_with_student(admin_client, student_client)
    outsider = make_student_client("outsider@example.com")

    response = submit(outsider, event_id)

    assert response.status_code == 403


def test_cancelled_registration_cannot_submit_feedback(
    admin_client, student_client
):
    event_id = create_event(admin_client)
    register(student_client, event_id)
    student_client.delete(f"/api/events/{event_id}/register")
    end_event(admin_client, event_id)

    response = submit(student_client, event_id)

    assert response.status_code == 403


def test_duplicate_feedback_is_rejected(admin_client, student_client):
    event_id = ended_event_with_student(admin_client, student_client)
    submit(student_client, event_id)

    response = submit(student_client, event_id)

    assert response.status_code == 409


def test_feedback_for_unknown_event_returns_404(student_client):
    assert submit(student_client, 9999).status_code == 404


def test_admin_cannot_submit_feedback(admin_client, student_client):
    event_id = ended_event_with_student(admin_client, student_client)

    assert submit(admin_client, event_id).status_code == 403


def test_anonymous_cannot_submit_feedback(client, admin_client, student_client):
    event_id = ended_event_with_student(admin_client, student_client)

    assert submit(client, event_id).status_code == 401


# ---------- Edit ----------

def test_student_can_edit_own_feedback(admin_client, student_client):
    event_id = ended_event_with_student(admin_client, student_client)
    submit(student_client, event_id, rating=2, comments="Meh")

    response = student_client.put(
        f"/api/events/{event_id}/feedback",
        json={"rating": 5, "comments": "Changed my mind"},
    )

    assert response.status_code == 200
    assert response.get_json()["feedback"]["rating"] == 5


def test_edit_is_visible_to_admin(admin_client, student_client):
    event_id = ended_event_with_student(admin_client, student_client)
    submit(student_client, event_id, rating=2)
    student_client.put(
        f"/api/events/{event_id}/feedback",
        json={"rating": 5, "comments": "Better"},
    )

    data = admin_client.get(f"/api/events/{event_id}/feedback").get_json()

    assert data["count"] == 1
    assert data["feedback"][0]["rating"] == 5
    assert data["feedback"][0]["comments"] == "Better"


def test_edit_without_existing_feedback_returns_404(
    admin_client, student_client
):
    event_id = ended_event_with_student(admin_client, student_client)

    response = student_client.put(
        f"/api/events/{event_id}/feedback", json={"rating": 4}
    )

    assert response.status_code == 404


def test_edit_with_invalid_rating_fails(admin_client, student_client):
    event_id = ended_event_with_student(admin_client, student_client)
    submit(student_client, event_id)

    response = student_client.put(
        f"/api/events/{event_id}/feedback", json={"rating": 9}
    )

    assert response.status_code == 400


# ---------- Admin view ----------

def test_admin_sees_feedback_and_average_rating(
    admin_client, student_client, make_student_client
):
    event_id = create_event(admin_client)
    register(student_client, event_id)
    second = make_student_client("second@example.com")
    register(second, event_id)
    end_event(admin_client, event_id)
    submit(student_client, event_id, rating=4, comments="Good")
    submit(second, event_id, rating=5, comments="Excellent")

    response = admin_client.get(f"/api/events/{event_id}/feedback")

    assert response.status_code == 200
    data = response.get_json()
    assert data["count"] == 2
    assert data["average_rating"] == 4.5
    assert {f["comments"] for f in data["feedback"]} == {"Good", "Excellent"}


def test_event_without_feedback_has_no_average(admin_client):
    event_id = create_event(admin_client)

    data = admin_client.get(f"/api/events/{event_id}/feedback").get_json()

    assert data["count"] == 0
    assert data["average_rating"] is None
    assert data["feedback"] == []


def test_student_cannot_view_event_feedback(admin_client, student_client):
    event_id = create_event(admin_client)

    response = student_client.get(f"/api/events/{event_id}/feedback")

    assert response.status_code == 403


def test_anonymous_cannot_view_event_feedback(client, admin_client):
    event_id = create_event(admin_client)

    assert client.get(f"/api/events/{event_id}/feedback").status_code == 401


def test_view_feedback_of_unknown_event_returns_404(admin_client):
    assert admin_client.get("/api/events/9999/feedback").status_code == 404