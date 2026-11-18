import pytest
from flask import g

from app import create_app
from app.extensions import db
from app.models.user import User
from config import TestingConfig


@pytest.fixture
def app():
    app = create_app(TestingConfig)

    @app.before_request
    def reset_cached_login_user():
        # The test keeps one app context open, so g would otherwise
        # remember the last logged-in user across different clients.
        g.pop("_login_user", None)

    with app.app_context():
        db.create_all()

        yield app

        db.session.remove()
        db.drop_all()


@pytest.fixture
def client(app):
    """An anonymous (not logged in) client."""
    return app.test_client()


def _logged_in_client(app, name, email, password, role):
    user = User(name=name, email=email, role=role)
    user.set_password(password)
    db.session.add(user)
    db.session.commit()

    test_client = app.test_client()
    test_client.post("/api/auth/login", json={
        "email": email,
        "password": password,
    })
    return test_client


@pytest.fixture
def admin_client(app):
    """A client already logged in as an admin."""
    return _logged_in_client(
        app, "Admin User", "admin@example.com", "adminpass123", "admin"
    )


@pytest.fixture
def student_client(app):
    """A client already logged in as a student."""
    return _logged_in_client(
        app, "Student User", "student@example.com", "studentpass123", "student"
    )