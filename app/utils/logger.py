"""Structured logging configuration for GameNight application."""
import logging
import sys
from logging.handlers import RotatingFileHandler
from pathlib import Path
from typing import Optional


class GameNightLogger:
    """Centralized logging configuration for the application."""

    _loggers = {}
    _initialized = False

    @classmethod
    def setup(cls, app=None, config_name='development'):
        """
        Initialize logging configuration for the application.

        Args:
            app: Flask application instance (optional)
            config_name: Configuration name (development, production, testing)
        """
        if cls._initialized:
            return

        # Determine log level based on environment
        log_levels = {
            'development': logging.DEBUG,
            'testing': logging.WARNING,
            'production': logging.INFO
        }
        log_level = log_levels.get(config_name, logging.INFO)

        # Create logs directory if it doesn't exist
        log_dir = Path('logs')
        log_dir.mkdir(exist_ok=True)

        # Configure root logger
        root_logger = logging.getLogger()
        root_logger.setLevel(log_level)

        # Remove existing handlers to avoid duplicates
        root_logger.handlers = []

        # Create formatters
        detailed_formatter = logging.Formatter(
            '[%(asctime)s] %(levelname)s in %(name)s (%(filename)s:%(lineno)d): %(message)s'
        )
        simple_formatter = logging.Formatter(
            '%(levelname)s: %(message)s'
        )

        # Console handler (stdout)
        console_handler = logging.StreamHandler(sys.stdout)
        console_handler.setLevel(log_level)
        console_handler.setFormatter(
            simple_formatter if config_name == 'development' else detailed_formatter
        )
        root_logger.addHandler(console_handler)

        # File handler with rotation (only in production and development)
        if config_name in ['production', 'development']:
            file_handler = RotatingFileHandler(
                log_dir / 'gamenight.log',
                maxBytes=10 * 1024 * 1024,  # 10MB
                backupCount=10
            )
            file_handler.setLevel(log_level)
            file_handler.setFormatter(detailed_formatter)
            root_logger.addHandler(file_handler)

            # Separate error log file
            error_handler = RotatingFileHandler(
                log_dir / 'gamenight_errors.log',
                maxBytes=10 * 1024 * 1024,  # 10MB
                backupCount=10
            )
            error_handler.setLevel(logging.ERROR)
            error_handler.setFormatter(detailed_formatter)
            root_logger.addHandler(error_handler)

        # Configure Flask app logger if provided
        if app:
            app.logger.setLevel(log_level)
            # Flask's logger will inherit handlers from root logger

        # Suppress overly verbose third-party loggers
        logging.getLogger('werkzeug').setLevel(logging.WARNING)
        logging.getLogger('socketio').setLevel(logging.WARNING)
        logging.getLogger('engineio').setLevel(logging.WARNING)

        cls._initialized = True

    @classmethod
    def get_logger(cls, name: str) -> logging.Logger:
        """
        Get or create a logger for a specific module.

        Args:
            name: Logger name (typically __name__ of the module)

        Returns:
            Configured logger instance
        """
        if name not in cls._loggers:
            cls._loggers[name] = logging.getLogger(name)
        return cls._loggers[name]


def get_logger(name: Optional[str] = None) -> logging.Logger:
    """
    Convenience function to get a logger instance.

    Args:
        name: Logger name (defaults to caller's module if not provided)

    Returns:
        Configured logger instance

    Example:
        from app.utils.logger import get_logger
        logger = get_logger(__name__)
        logger.info("Processing game scores")
    """
    if name is None:
        # Get caller's module name
        import inspect
        frame = inspect.currentframe().f_back
        name = frame.f_globals.get('__name__', 'gamenight')

    return GameNightLogger.get_logger(name)
