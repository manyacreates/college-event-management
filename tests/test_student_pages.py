def test_events_page_loads(client):
    assert client.get("/events").status_code == 200


def test_event_detail_page_loads(client, admin_client):
    created = admin_client.post("/api/events", json={
        "title": "Annual Tech Fest", "description": "Fest", "category": "Technical",
        "event_date": "2099-01-01", "start_time": "10:00", "end_time": "16:00",
        "venue": "JIIT Noida", "capacity": 10,
    })
    event_id = created.get_json()["event"]["id"]

    response = client.get(f"/events/{event_id}")

    assert response.status_code == 200
    assert "Annual Tech Fest" in response.get_data(as_text=True)


def test_unknown_event_page_returns_404(client):
    assert client.get("/events/9999").status_code == 404


def test_dashboard_redirects_anonymous_to_login(client):
    response = client.get("/dashboard")

    assert response.status_code == 302
    assert response.headers["Location"].endswith("/login")


def test_dashboard_redirects_admin_to_login(admin_client):
    assert admin_client.get("/dashboard").status_code == 302


def test_student_can_open_dashboard_and_notifications(student_client):
    assert student_client.get("/dashboard").status_code == 200
    assert student_client.get("/notifications").status_code == 200