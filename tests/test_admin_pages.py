def test_admin_pages_redirect_anonymous_to_admin_login(client):
    for url in ["/admin/dashboard", "/admin/events"]:
        response = client.get(url)
        assert response.status_code == 302
        assert response.headers["Location"].endswith("/admin/login")


def test_student_cannot_open_admin_pages(student_client):
    assert student_client.get("/admin/dashboard").status_code == 302


def test_admin_can_open_admin_pages(admin_client):
    assert admin_client.get("/admin/dashboard").status_code == 200
    assert admin_client.get("/admin/events").status_code == 200


def test_admin_manage_page_loads_and_unknown_is_404(admin_client):
    created = admin_client.post("/api/events", json={
        "title": "Annual Tech Fest", "description": "Fest", "category": "Technical",
        "event_date": "2099-01-01", "start_time": "10:00", "end_time": "16:00",
        "venue": "JIIT Noida", "capacity": 10,
    })
    event_id = created.get_json()["event"]["id"]

    assert admin_client.get(f"/admin/events/{event_id}").status_code == 200
    assert admin_client.get("/admin/events/9999").status_code == 404