import os

from dotenv import load_dotenv

load_dotenv()


class Config:
    """Settings shared by all environments."""
    SECRET_KEY = os.environ.get("SECRET_KEY")


class DevelopmentConfig(Config):
    DEBUG = True


class TestingConfig(Config):
    """Used only by the automated tests."""
    TESTING = True
    SECRET_KEY = "test-secret-key"  # test-only value, not a real secret