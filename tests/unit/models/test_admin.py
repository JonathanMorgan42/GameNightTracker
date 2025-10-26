"""Unit tests for Admin model."""
import pytest
from app.models import Admin


@pytest.mark.unit
@pytest.mark.models
class TestAdminModel:
    """Test suite for Admin model."""

    def test_create_admin(self, db_session):
        """Test creating an admin user."""
        admin = Admin(username='newadmin')
        admin.setPassword('securepass123')

        db_session.add(admin)
        db_session.commit()

        assert admin.id is not None
        assert admin.username == 'newadmin'
        assert admin.passwordHash is not None
        assert admin.passwordHash != 'securepass123'  # Password should be hashed

    def test_set_password(self, db_session):
        """Test password hashing."""
        admin = Admin(username='testuser')
        admin.setPassword('mypassword')

        db_session.add(admin)
        db_session.commit()

        # Password should be hashed
        assert admin.passwordHash != 'mypassword'
        assert len(admin.passwordHash) > 20  # Hash should be long

    def test_check_password_correct(self, admin_user):
        """Test password verification with correct password."""
        assert admin_user.checkPassword('testpassword123') is True

    def test_check_password_incorrect(self, admin_user):
        """Test password verification with incorrect password."""
        assert admin_user.checkPassword('wrongpassword') is False

    def test_check_password_empty(self, admin_user):
        """Test password verification with empty password."""
        assert admin_user.checkPassword('') is False

    def test_unique_username(self, db_session, admin_user):
        """Test that usernames must be unique."""
        duplicate_admin = Admin(username=admin_user.username)
        duplicate_admin.setPassword('anotherpass')

        db_session.add(duplicate_admin)

        with pytest.raises(Exception):  # Should raise IntegrityError
            db_session.commit()

    def test_flask_login_properties(self, admin_user):
        """Test Flask-Login required properties."""
        assert admin_user.is_authenticated is True
        assert admin_user.is_active is True
        assert admin_user.is_anonymous is False
        assert admin_user.get_id() == str(admin_user.id)

    def test_password_change(self, db_session):
        """Test changing password."""
        admin = Admin(username='changepassuser')
        admin.setPassword('oldpassword')

        db_session.add(admin)
        db_session.commit()

        old_hash = admin.passwordHash

        # Change password
        admin.setPassword('newpassword')
        db_session.commit()

        # Hash should be different
        assert admin.passwordHash != old_hash
        assert admin.checkPassword('newpassword') is True
        assert admin.checkPassword('oldpassword') is False

    def test_username_required(self, db_session):
        """Test that username is required."""
        admin = Admin()
        admin.setPassword('password')

        db_session.add(admin)

        with pytest.raises(Exception):  # Should raise IntegrityError
            db_session.commit()
