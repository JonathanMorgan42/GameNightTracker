from app import db
from app.models import Admin


class AuthService:

    @staticmethod
    def authenticate(username, password):
        """
        Authenticate a user.

        Args:
            username: Username
            password: Plain text password

        Returns:
            Admin object if authenticated, None otherwise
        """
        admin = Admin.query.filter_by(username=username).first()
        if admin and admin.checkPassword(password):
            return admin
        return None

    @staticmethod
    def change_password(admin, current_password, new_password):
        """
        Change admin password.

        Args:
            admin: Admin object
            current_password: Current password (for verification)
            new_password: New password to set

        Returns:
            True if successful, False if current password incorrect
        """
        if not admin.checkPassword(current_password):
            return False

        admin.setPassword(new_password)
        db.session.commit()
        return True

    @staticmethod
    def get_admin_by_username(username):
        """Get admin by username."""
        return Admin.query.filter_by(username=username).first()