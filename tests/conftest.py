import pytest

from app import create_app
from config import TestingConfig


@pytest.fixture
def app():
    """A fresh application configured for testing."""
    return create_app(TestingConfig)


@pytest.fixture
def client(app):
    """A test client that sends fake HTTP requests to the app."""
    return app.test_client()