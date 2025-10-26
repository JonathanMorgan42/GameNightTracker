"""Application Factory."""
from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager
from flask_wtf.csrf import CSRFProtect
from flask_migrate import Migrate
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address
from flask_session import Session
from flask_socketio import SocketIO
from werkzeug.middleware.proxy_fix import ProxyFix
from sqlalchemy import event
from sqlalchemy.engine import Engine

db = SQLAlchemy()
socketio = SocketIO()


# Enable foreign key constraints for SQLite
@event.listens_for(Engine, "connect")
def set_sqlite_pragma(dbapi_conn, connection_record):
    """Enable foreign key constraints for SQLite."""
    cursor = dbapi_conn.cursor()
    cursor.execute("PRAGMA foreign_keys=ON")
    cursor.close()


login_manager = LoginManager()
csrf = CSRFProtect()
migrate = Migrate()
session = Session()
limiter = Limiter(
    key_func=get_remote_address,
    default_limits=["200 per day", "50 per hour"],
    storage_uri="memory://"
)


def create_app(config_name='development'):
    """Create and configure the application."""
    app = Flask(__name__)

    from config import config_by_name
    app.config.from_object(config_by_name[config_name])

    # Initialize structured logging
    from app.utils.logger import GameNightLogger
    GameNightLogger.setup(app, config_name)

    # Add ProxyFix middleware for production (handles X-Forwarded-* headers)
    if config_name == 'production':
        app.wsgi_app = ProxyFix(
            app.wsgi_app, x_for=1, x_proto=1, x_host=1, x_prefix=1
        )

    db.init_app(app)
    login_manager.init_app(app)

    # Initialize session before CSRF (CSRF needs session)
    if config_name == 'production':
        session.init_app(app)

    csrf.init_app(app)
    migrate.init_app(app, db)

    # Only enable rate limiting if configured
    if app.config.get('RATELIMIT_ENABLED', True):
        limiter.init_app(app)
    else:
        # Disable limiter for testing
        limiter.enabled = False

    # Initialize SocketIO
    socketio.init_app(
        app,
        cors_allowed_origins="*",  # Will be restricted by Flask's CORS policy
        async_mode='threading',
        manage_session=False,  # Use Flask-Login sessions
        logger=False,
        engineio_logger=False
    )
    
    login_manager.login_view = 'auth.login'
    login_manager.login_message = 'Please log in to access this page.'
    
    @login_manager.user_loader
    def load_user(user_id):
        from app.models.admin import Admin
        return Admin.query.get(int(user_id))
    
    # Force HTTPS in production
    @app.before_request
    def force_https():
        """Redirect HTTP to HTTPS in production."""
        if config_name == 'production':
            from flask import request, redirect
            if request.headers.get('X-Forwarded-Proto') == 'http':
                url = request.url.replace('http://', 'https://', 1)
                return redirect(url, code=301)

    # Add security headers
    @app.after_request
    def set_security_headers(response):
        """Add security headers to all responses."""
        response.headers['X-Content-Type-Options'] = 'nosniff'
        response.headers['X-Frame-Options'] = 'DENY'
        response.headers['X-XSS-Protection'] = '1; mode=block'
        response.headers['Referrer-Policy'] = 'strict-origin-when-cross-origin'

        # Add HSTS only in production with HTTPS
        if config_name == 'production':
            response.headers['Strict-Transport-Security'] = 'max-age=31536000; includeSubDomains'

        # Content Security Policy - allows inline scripts/styles (needed for app)
        # Also allows socket.io CDN and WebSocket connections
        response.headers['Content-Security-Policy'] = (
            "default-src 'self'; "
            "script-src 'self' 'unsafe-inline' https://cdn.socket.io; "
            "style-src 'self' 'unsafe-inline' https://fonts.googleapis.com https://cdnjs.cloudflare.com; "
            "img-src 'self' data:; "
            "font-src 'self' https://fonts.gstatic.com https://cdnjs.cloudflare.com; "
            "connect-src 'self' ws: wss: https://cdn.socket.io; "
            "frame-ancestors 'none';"
        )

        return response

    # Register error handlers
    from flask import render_template
    from app.exceptions import GameNightException
    from app.utils.logger import get_logger
    error_logger = get_logger('app.errors')

    @app.errorhandler(404)
    def not_found_error(error):
        """Handle 404 errors."""
        error_logger.warning(f"404 error: {error}")
        return render_template('errors/404.html'), 404

    @app.errorhandler(403)
    def forbidden_error(error):
        """Handle 403 errors."""
        error_logger.warning(f"403 error: {error}")
        return render_template('errors/403.html'), 403

    @app.errorhandler(500)
    def internal_error(error):
        """Handle 500 errors."""
        db.session.rollback()
        error_logger.error(f"500 error: {error}", exc_info=True)
        return render_template('errors/500.html'), 500

    @app.errorhandler(GameNightException)
    def handle_gamenight_exception(error):
        """Handle custom GameNight exceptions."""
        error_logger.error(f"GameNight exception: {error.message}", exc_info=True)
        if error.status_code >= 500:
            db.session.rollback()
        return render_template('errors/500.html'), error.status_code

    from app.routes.main import main_bp
    from app.routes.auth import auth_bp
    from app.routes.admin import admin_bp

    app.register_blueprint(main_bp)
    app.register_blueprint(auth_bp, url_prefix='/auth')
    app.register_blueprint(admin_bp, url_prefix='/admin')
    
    with app.app_context():
        # Import all models BEFORE creating tables
        from app.models.admin import Admin
        from app.models.team import Team
        from app.models.participant import Participant
        from app.models.game import Game
        from app.models.score import Score
        from app.models.penalty import Penalty

        # Now create tables
        db.create_all()
        initialize_admins(app)

    # Register WebSocket event handlers
    from app.websockets import register_handlers
    register_handlers(socketio)

    return app


def initialize_admins(app):
    """Initialize admin accounts."""
    from app.models.admin import Admin

    admin = Admin.query.filter_by(username=app.config['ADMIN_USERNAME']).first()
    if not admin:
        admin = Admin(username=app.config['ADMIN_USERNAME'])
        admin.setPassword(app.config['ADMIN_DEFAULT_PASSWORD'])
        db.session.add(admin)
        db.session.commit()

    # Only create DEVADMIN in development/testing (not production)
    if app.config.get('ENV') != 'production' and not app.config.get('TESTING'):
        dev_admin = Admin.query.filter_by(username=app.config['DEVADMIN_USERNAME']).first()
        if not dev_admin:
            dev_admin = Admin(username=app.config['DEVADMIN_USERNAME'])
            dev_admin.setPassword(app.config['DEVADMIN_PASSWORD'])
            db.session.add(dev_admin)
            db.session.commit()
