def test_student_can_register(client):
    response = client.post("/api/auth/register", json={
        "name": "Manya Sharma",
        "email": "manya@example.com",
        "password": "password123",
        "role": "student"
    })

    assert response.status_code == 201
    assert response.get_json() == {
        "success": True,
        "message": "Registration successful"
    }
def test_duplicate_email_is_rejected(client):
    data = {
        "name": "Manya Sharma",
        "email": "manya@example.com",
        "password": "password123",
        "role": "student"
    }

    client.post("/api/auth/register", json=data)

    response = client.post("/api/auth/register", json=data)

    assert response.status_code == 409


def test_short_password_is_rejected(client):
    response = client.post("/api/auth/register", json={
        "name": "Manya Sharma",
        "email": "test@example.com",
        "password": "123",
        "role": "student"
    })

    assert response.status_code == 400


def test_missing_fields_are_rejected(client):
    response = client.post("/api/auth/register", json={
        "name": "Manya Sharma"
    })

    assert response.status_code == 400


def test_admin_registration_is_rejected(client):
    response = client.post("/api/auth/register", json={
        "name": "Manya Sharma",
        "email": "admin@example.com",
        "password": "password123",
        "role": "admin"
    })

    assert response.status_code == 403