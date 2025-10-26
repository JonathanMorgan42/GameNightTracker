"""
Unit tests for AuthService.
Tests isolated business logic for authentication operations.
"""
import pytest
from app.services import AuthService
from app.models import Admin


@pytest.mark.unit
@pytest.mark.services
class TestAuthService:
    """Test suite for AuthService."""

    def test_authenticate_valid_credentials(self, db_session, admin_user):
        """Test authentication with valid credentials."""
        result = AuthService.authenticate(admin_user.username, 'testpassword123')

        assert result is not None
        assert result.id == admin_user.id
        assert result.username == admin_user.username

    def test_authenticate_invalid_password(self, db_session, admin_user):
        """Test authentication with invalid password."""
        result = AuthService.authenticate(admin_user.username, 'wrongpassword')

        assert result is None

    def test_authenticate_nonexistent_user(self, db_session):
        """Test authentication with nonexistent username."""
        result = AuthService.authenticate('nonexistent', 'password123')

        assert result is None

    def test_authenticate_empty_username(self, db_session):
        """Test authentication with empty username."""
        result = AuthService.authenticate('', 'password123')

        assert result is None

    def test_authenticate_empty_password(self, db_session, admin_user):
        """Test authentication with empty password."""
        result = AuthService.authenticate(admin_user.username, '')

        assert result is None

    def test_authenticate_both_empty(self, db_session):
        """Test authentication with both fields empty."""
        result = AuthService.authenticate('', '')

        assert result is None

    def test_authenticate_case_sensitive_username(self, db_session, admin_user):
        """Test that username is case-sensitive."""
        # Try with different case
        result = AuthService.authenticate(admin_user.username.upper(), 'testpassword123')

        # Should fail if username case doesn't match exactly
        assert result is None

    def test_change_password_valid(self, db_session, admin_user):
        """Test changing password with valid current password."""
        result = AuthService.change_password(admin_user, 'testpassword123', 'newpassword456')

        assert result is True

        # Verify new password works
        auth_result = AuthService.authenticate(admin_user.username, 'newpassword456')
        assert auth_result is not None

        # Verify old password doesn't work
        auth_result = AuthService.authenticate(admin_user.username, 'testpassword123')
        assert auth_result is None

    def test_change_password_invalid_current(self, db_session, admin_user):
        """Test changing password with invalid current password."""
        result = AuthService.change_password(admin_user, 'wrongpassword', 'newpassword456')

        assert result is False

        # Verify original password still works
        auth_result = AuthService.authenticate(admin_user.username, 'testpassword123')
        assert auth_result is not None

    def test_change_password_empty_current(self, db_session, admin_user):
        """Test changing password with empty current password."""
        result = AuthService.change_password(admin_user, '', 'newpassword456')

        assert result is False

    def test_change_password_same_password(self, db_session, admin_user):
        """Test changing password to the same password."""
        result = AuthService.change_password(admin_user, 'testpassword123', 'testpassword123')

        assert result is True

        # Verify password still works
        auth_result = AuthService.authenticate(admin_user.username, 'testpassword123')
        assert auth_result is not None

    def test_get_admin_by_username_exists(self, db_session, admin_user):
        """Test getting admin by username when it exists."""
        result = AuthService.get_admin_by_username(admin_user.username)

        assert result is not None
        assert result.id == admin_user.id
        assert result.username == admin_user.username

    def test_get_admin_by_username_not_exists(self, db_session):
        """Test getting admin by username when it doesn't exist."""
        result = AuthService.get_admin_by_username('nonexistent')

        assert result is None

    def test_get_admin_by_username_empty(self, db_session):
        """Test getting admin with empty username."""
        result = AuthService.get_admin_by_username('')

        assert result is None

    def test_password_hash_security(self, db_session):
        """Test that passwords are properly hashed and not stored in plain text."""
        admin = Admin(username='securitytest')
        admin.setPassword('mypassword')

        db_session.add(admin)
        db_session.commit()

        # Hash should not equal plain password
        assert admin.passwordHash != 'mypassword'

        # Hash should be long (bcrypt hashes are ~60 chars)
        assert len(admin.passwordHash) > 50

        # Same password should produce different hashes (due to salt)
        admin2 = Admin(username='securitytest2')
        admin2.setPassword('mypassword')
        db_session.add(admin2)
        db_session.commit()

        assert admin.passwordHash != admin2.passwordHash

    def test_multiple_failed_authentications(self, db_session, admin_user):
        """Test multiple failed authentication attempts."""
        # Simulate brute force attempts
        for _ in range(5):
            result = AuthService.authenticate(admin_user.username, 'wrongpassword')
            assert result is None

        # Account should still work with correct password
        result = AuthService.authenticate(admin_user.username, 'testpassword123')
        assert result is not None
