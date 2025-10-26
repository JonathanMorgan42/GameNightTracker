"""Application Configuration."""
import os
from datetime import timedelta
from pathlib import Path

# Get absolute path to project root
BASE_DIR = Path(__file__).resolve().parent
INSTANCE_DIR = BASE_DIR / 'instance'
INSTANCE_DIR.mkdir(exist_ok=True)

# Create feedback directory
FEEDBACK_DIR = INSTANCE_DIR / 'feedback'
FEEDBACK_DIR.mkdir(exist_ok=True)


class Config:
    """Base configuration."""
    SECRET_KEY = os.environ.get('SECRET_KEY', 'dev-secret-key-change-in-production')
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    SQLALCHEMY_RECORD_QUERIES = True

    # Session cookie settings (HTTPOnly for security)
    SESSION_COOKIE_HTTPONLY = True
    PERMANENT_SESSION_LIFETIME = timedelta(hours=24)

    # CSRF Protection settings
    WTF_CSRF_ENABLED = True
    WTF_CSRF_TIME_LIMIT = None

    # Admin credentials
    ADMIN_USERNAME = os.environ.get('ADMIN_USERNAME', 'admin')
    ADMIN_DEFAULT_PASSWORD = os.environ.get('ADMIN_PASSWORD', 'admin')
    DEVADMIN_USERNAME = os.environ.get('DEVADMIN_USERNAME', 'devadmin')
    DEVADMIN_PASSWORD = os.environ.get('DEVADMIN_PASSWORD', 'devpassword')

    LOG_LEVEL = os.environ.get('LOG_LEVEL', 'INFO')

    # Feedback settings
    FEEDBACK_DIR = FEEDBACK_DIR
    FEEDBACK_RATE_LIMIT = '5 per hour'  # Max 5 feedback submissions per hour per IP


class DevelopmentConfig(Config):
    """Development configuration."""
    DEBUG = True
    TESTING = False
    SQLALCHEMY_DATABASE_URI = f'sqlite:///{INSTANCE_DIR}/gamenight_dev.db'
    SQLALCHEMY_ECHO = True

    # Development uses Lax (works fine for local HTTP)
    SESSION_COOKIE_SAMESITE = 'Lax'
    SESSION_COOKIE_SECURE = False

    # Disable rate limiting in development to allow for testing
    RATELIMIT_ENABLED = False


class TestingConfig(Config):
    """Testing configuration."""
    DEBUG = False
    TESTING = True
    SQLALCHEMY_DATABASE_URI = 'sqlite:///:memory:'
    SQLALCHEMY_ECHO = False
    WTF_CSRF_ENABLED = False
    RATELIMIT_ENABLED = False  # Disable rate limiting in tests


class ProductionConfig(Config):
    """Production configuration."""
    DEBUG = False
    TESTING = False
    SQLALCHEMY_DATABASE_URI = f'sqlite:///{INSTANCE_DIR}/gamenight.db'
    SQLALCHEMY_ECHO = False

    # Server-side session storage
    SESSION_TYPE = 'filesystem'
    SESSION_FILE_DIR = INSTANCE_DIR / 'flask_session'
    SESSION_PERMANENT = True
    SESSION_USE_SIGNER = True

    # Session cookie settings (HTTPS via Cloudflare Tunnel)
    SESSION_COOKIE_SECURE = True
    SESSION_COOKIE_SAMESITE = 'Lax'
    SESSION_COOKIE_HTTPONLY = True
    SESSION_COOKIE_DOMAIN = None

    # CSRF protection (session-based, not cookie-based)
    WTF_CSRF_TIME_LIMIT = None
    WTF_CSRF_METHODS = ['POST', 'PUT', 'PATCH', 'DELETE']

    # Reverse proxy configuration
    PREFERRED_URL_SCHEME = 'https'
    APPLICATION_ROOT = '/'


config_by_name = {
    'development': DevelopmentConfig,
    'testing': TestingConfig,
    'production': ProductionConfig,
    'default': DevelopmentConfig
}
