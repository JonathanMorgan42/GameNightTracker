"""Routes package."""
from app.routes.main import main_bp
from app.routes.auth import auth_bp
from app.routes.admin import admin_bp

__all__ = ['main_bp', 'auth_bp', 'admin_bp']
