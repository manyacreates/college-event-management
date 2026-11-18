import os

from dotenv import load_dotenv

load_dotenv()


class Config:
    """Settings shared by all environments."""
    SECRET_KEY = os.environ.get("SECRET_KEY")
    SQLALCHEMY_DATABASE_URI = os.environ.get("DATABASE_URL", "sqlite:///cems.db")
    SQLALCHEMY_TRACK_MODIFICATIONS = False


class DevelopmentConfig(Config):
    DEBUG = True


class TestingConfig(Config):
    """Used only by the automated tests."""
    TESTING = True
    SECRET_KEY = "test-secret-key"  # test-only value, not a real secret
    SQLALCHEMY_DATABASE_URI = "sqlite:///:memory:"