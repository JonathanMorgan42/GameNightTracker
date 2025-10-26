"""Custom exception classes for GameNight application."""


class GameNightException(Exception):
    """Base exception class for all GameNight-specific exceptions."""

    def __init__(self, message, status_code=500, payload=None):
        """
        Initialize the exception.

        Args:
            message: Error message
            status_code: HTTP status code (default 500)
            payload: Additional error data (dict)
        """
        super().__init__(message)
        self.message = message
        self.status_code = status_code
        self.payload = payload

    def to_dict(self):
        """Convert exception to dictionary for JSON responses."""
        result = {'error': self.message}
        if self.payload:
            result.update(self.payload)
        return result


class ValidationError(GameNightException):
    """Raised when input validation fails."""

    def __init__(self, message, field=None):
        """
        Initialize validation error.

        Args:
            message: Validation error message
            field: Field name that failed validation
        """
        payload = {'field': field} if field else None
        super().__init__(message, status_code=400, payload=payload)


class NotFoundError(GameNightException):
    """Raised when a requested resource is not found."""

    def __init__(self, resource_type, resource_id=None):
        """
        Initialize not found error.

        Args:
            resource_type: Type of resource (e.g., 'Team', 'Game', 'Score')
            resource_id: ID of the resource that was not found
        """
        if resource_id:
            message = f"{resource_type} with ID {resource_id} not found"
        else:
            message = f"{resource_type} not found"
        super().__init__(message, status_code=404)


class PermissionDeniedError(GameNightException):
    """Raised when user lacks permission for an action."""

    def __init__(self, message="You do not have permission to perform this action"):
        """Initialize permission denied error."""
        super().__init__(message, status_code=403)


class DatabaseError(GameNightException):
    """Raised when a database operation fails."""

    def __init__(self, message, operation=None):
        """
        Initialize database error.

        Args:
            message: Error message
            operation: Type of database operation that failed
        """
        payload = {'operation': operation} if operation else None
        super().__init__(message, status_code=500, payload=payload)


class ConflictError(GameNightException):
    """Raised when an operation conflicts with existing data."""

    def __init__(self, message):
        """Initialize conflict error."""
        super().__init__(message, status_code=409)


class ScoreCalculationError(GameNightException):
    """Raised when score calculation fails."""

    def __init__(self, message, game_id=None, team_id=None):
        """
        Initialize score calculation error.

        Args:
            message: Error message
            game_id: ID of the game where calculation failed
            team_id: ID of the team where calculation failed
        """
        payload = {}
        if game_id:
            payload['game_id'] = game_id
        if team_id:
            payload['team_id'] = team_id
        super().__init__(message, status_code=500, payload=payload or None)


class TournamentError(GameNightException):
    """Raised when tournament operations fail."""

    def __init__(self, message):
        """Initialize tournament error."""
        super().__init__(message, status_code=400)


class ConfigurationError(GameNightException):
    """Raised when application configuration is invalid."""

    def __init__(self, message, config_key=None):
        """
        Initialize configuration error.

        Args:
            message: Error message
            config_key: Configuration key that is invalid
        """
        payload = {'config_key': config_key} if config_key else None
        super().__init__(message, status_code=500, payload=payload)
