from app.extensions import db
from app.models.user import User


def make_admin(email="admin@example.com", password="adminpass123"):
    """Helper: insert an admin directly, the way the CLI will."""
    admin = User(name="Admin User", email=email, role="admin")
    admin.set_password(password)
    db.session.add(admin)
    db.session.commit()


def login(client, email, password):
    return client.post("/api/auth/login", json={
        "email": email,
        "password": password,
    })


def test_create_admin_command_creates_admin(app):
    runner = app.test_cli_runner()

    result = runner.invoke(args=[
        "create-admin",
        "--name", "Admin User",
        "--email", "admin@example.com",
        "--password", "adminpass123",
    ])

    assert result.exit_code == 0
    user = db.session.execute(
        db.select(User).filter_by(email="admin@example.com")
    ).scalar_one()
    assert user.role == "admin"
    assert user.password_hash != "adminpass123"


def test_create_admin_command_rejects_duplicate_email(app):
    make_admin()
    runner = app.test_cli_runner()

    result = runner.invoke(args=[
        "create-admin",
        "--name", "Another Admin",
        "--email", "admin@example.com",
        "--password", "adminpass123",
    ])

    assert result.exit_code != 0


def test_create_admin_command_rejects_short_password(app):
    runner = app.test_cli_runner()

    result = runner.invoke(args=[
        "create-admin",
        "--name", "Admin User",
        "--email", "admin@example.com",
        "--password", "123",
    ])

    assert result.exit_code != 0


def test_admin_can_log_in_and_has_admin_role(app, client):
    make_admin()

    response = login(client, "admin@example.com", "adminpass123")

    assert response.status_code == 200
    assert response.get_json()["user"]["role"] == "admin"


def test_admin_ping_allows_admin(app, client):
    make_admin()
    login(client, "admin@example.com", "adminpass123")

    response = client.get("/api/admin/ping")

    assert response.status_code == 200


def test_admin_ping_rejects_student_with_403(client):
    client.post("/api/auth/register", json={
        "name": "Manya Sharma",
        "email": "manya@example.com",
        "password": "password123",
        "role": "student",
    })
    login(client, "manya@example.com", "password123")

    response = client.get("/api/admin/ping")

    assert response.status_code == 403


def test_admin_ping_rejects_anonymous_with_401(client):
    response = client.get("/api/admin/ping")

    assert response.status_code == 401