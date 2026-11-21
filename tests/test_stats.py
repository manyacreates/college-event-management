from datetime import date, timedelta


def make_date(days):
    return (date.today() + timedelta(days=days)).isoformat()


def event_payload(title="Annual Tech Fest", days=30):
    return {
        "title": title,
        "description": "A college event",
        "category": "Technical",
        "event_date": make_date(days),
        "start_time": "10:00",
        "end_time": "16:00",
        "venue": "JIIT Noida",
        "capacity": 50,
    }


def create_event(admin_client, title="Annual Tech Fest", days=30):
    response = admin_client.post("/api/events", json=event_payload(title, days))
    return response.get_json()["event"]["id"]


def get_stats(admin_client):
    return admin_client.get("/api/admin/stats").get_json()["stats"]


def test_stats_on_empty_database(admin_client):
    response = admin_client.get("/api/admin/stats")

    assert response.status_code == 200
    stats = response.get_json()["stats"]
    assert stats["total_users"] == 0
    assert stats["total_events"] == 0
    assert stats["upcoming_events"] == 0
    assert stats["completed_events"] == 0
    assert stats["total_registrations"] == 0
    assert stats["average_rating"] is None
    assert stats["popular_events"] == []


def test_stats_count_students_not_admins(admin_client, student_client):
    assert get_stats(admin_client)["total_users"] == 1


def test_stats_split_upcoming_and_completed(admin_client):
    create_event(admin_client, "Future Fest", days=10)
    create_event(admin_client, "Past Fest", days=-10)

    stats = get_stats(admin_client)

    assert stats["total_events"] == 2
    assert stats["upcoming_events"] == 1
    assert stats["completed_events"] == 1


def test_stats_count_only_active_registrations(
    admin_client, student_client, make_student_client
):
    event_id = create_event(admin_client)
    student_client.post(f"/api/events/{event_id}/register")
    other = make_student_client("other@example.com")
    other.post(f"/api/events/{event_id}/register")
    other.delete(f"/api/events/{event_id}/register")

    assert get_stats(admin_client)["total_registrations"] == 1


def test_stats_popular_events_ordered_by_registrations(
    admin_client, student_client, make_student_client
):
    quiet_id = create_event(admin_client, "Quiet Event")
    busy_id = create_event(admin_client, "Busy Event")
    other = make_student_client("other@example.com")
    student_client.post(f"/api/events/{quiet_id}/register")
    student_client.post(f"/api/events/{busy_id}/register")
    other.post(f"/api/events/{busy_id}/register")

    popular = get_stats(admin_client)["popular_events"]

    assert [e["title"] for e in popular] == ["Busy Event", "Quiet Event"]
    assert popular[0]["registrations"] == 2


def test_stats_popular_events_limited_to_five(admin_client):
    for number in range(7):
        create_event(admin_client, f"Event {number}")

    assert len(get_stats(admin_client)["popular_events"]) == 5


def test_stats_average_rating_across_feedback(
    admin_client, student_client, make_student_client
):
    event_id = create_event(admin_client)
    student_client.post(f"/api/events/{event_id}/register")
    other = make_student_client("other@example.com")
    other.post(f"/api/events/{event_id}/register")
    admin_client.put(f"/api/events/{event_id}", json=event_payload(days=-5))
    student_client.post(f"/api/events/{event_id}/feedback", json={"rating": 4})
    other.post(f"/api/events/{event_id}/feedback", json={"rating": 5})

    assert get_stats(admin_client)["average_rating"] == 4.5


def test_student_cannot_view_stats(student_client):
    assert student_client.get("/api/admin/stats").status_code == 403


def test_anonymous_cannot_view_stats(client):
    assert client.get("/api/admin/stats").status_code == 401