from datetime import date, timedelta


def make_date(days):
    return (date.today() + timedelta(days=days)).isoformat()


def create_event(admin_client, title, days):
    return admin_client.post("/api/events", json={
        "title": title,
        "description": "A college event",
        "category": "Technical",
        "event_date": make_date(days),
        "start_time": "10:00",
        "end_time": "16:00",
        "venue": "JIIT Noida",
        "capacity": 50,
    })


def test_landing_page_loads(client):
    response = client.get("/")

    assert response.status_code == 200
    assert "College Event Management" in response.get_data(as_text=True)


def test_landing_page_shows_all_categories(client):
    html = client.get("/").get_data(as_text=True)

    for category in ["Technical", "Cultural", "Sports", "Workshops", "Seminars", "Other"]:
        assert category in html


def test_landing_page_shows_upcoming_event(client, admin_client):
    create_event(admin_client, "Annual Tech Fest", days=10)

    html = client.get("/").get_data(as_text=True)

    assert "Annual Tech Fest" in html


def test_landing_page_hides_past_events(client, admin_client):
    create_event(admin_client, "Old Fest", days=-10)

    html = client.get("/").get_data(as_text=True)

    assert "Old Fest" not in html


def test_landing_page_shows_empty_state_without_events(client):
    html = client.get("/").get_data(as_text=True)

    assert "No upcoming events yet" in html


def test_landing_page_has_login_and_register_links(client):
    html = client.get("/").get_data(as_text=True)

    assert 'href="/login"' in html
    assert 'href="/register"' in html


def test_stylesheet_is_served(client):
    assert client.get("/static/css/style.css").status_code == 200