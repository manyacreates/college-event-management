def register_student(client):
    """Helper: create a student account through the real API."""
    return client.post("/api/auth/register", json={
        "name": "Manya Sharma",
        "email": "manya@example.com",
        "password": "password123",
        "role": "student",
    })


def test_login_with_correct_credentials(client):
    register_student(client)

    response = client.post("/api/auth/login", json={
        "email": "manya@example.com",
        "password": "password123",
    })

    assert response.status_code == 200
    assert response.get_json()["success"] is True


def test_login_with_wrong_password_is_rejected(client):
    register_student(client)

    response = client.post("/api/auth/login", json={
        "email": "manya@example.com",
        "password": "wrong-password",
    })

    assert response.status_code == 401


def test_login_with_unknown_email_is_rejected(client):
    response = client.post("/api/auth/login", json={
        "email": "nobody@example.com",
        "password": "password123",
    })

    assert response.status_code == 401


def test_login_with_missing_fields_is_rejected(client):
    response = client.post("/api/auth/login", json={"email": "manya@example.com"})

    assert response.status_code == 400


def test_me_requires_login(client):
    response = client.get("/api/auth/me")

    assert response.status_code == 401


def test_me_returns_current_user_after_login(client):
    register_student(client)
    client.post("/api/auth/login", json={
        "email": "manya@example.com",
        "password": "password123",
    })

    response = client.get("/api/auth/me")

    assert response.status_code == 200
    assert response.get_json()["user"]["email"] == "manya@example.com"
    assert response.get_json()["user"]["role"] == "student"


def test_logout_ends_the_session(client):
    register_student(client)
    client.post("/api/auth/login", json={
        "email": "manya@example.com",
        "password": "password123",
    })

    logout_response = client.post("/api/auth/logout")
    me_response = client.get("/api/auth/me")

    assert logout_response.status_code == 200
    assert me_response.status_code == 401