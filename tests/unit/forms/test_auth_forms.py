"""
Unit tests for authentication forms.
Implements Black-Box Testing: Equivalence Partitioning and Boundary Value Analysis (BVA).
"""
import pytest
from app.forms import LoginForm, ChangePasswordForm


@pytest.mark.unit
@pytest.mark.forms
@pytest.mark.blackbox
class TestLoginForm:
    """
    Test suite for LoginForm.
    Uses equivalence partitioning for username and password fields.
    """

    def test_valid_login_form(self, app):
        """Test form with valid inputs - valid partition."""
        with app.test_request_context():
            form = LoginForm(data={
                'username': 'testuser',
                'password': 'password123'
            })
            assert form.validate() is True

    # Equivalence Partitioning: Empty username
    def test_empty_username(self, app):
        """Test form with empty username - invalid partition."""
        with app.test_request_context():
            form = LoginForm(data={
                'username': '',
                'password': 'password123'
            })
            assert form.validate() is False
            assert 'username' in form.errors

    # Equivalence Partitioning: Empty password
    def test_empty_password(self, app):
        """Test form with empty password - invalid partition."""
        with app.test_request_context():
            form = LoginForm(data={
                'username': 'testuser',
                'password': ''
            })
            assert form.validate() is False
            assert 'password' in form.errors

    # Equivalence Partitioning: Both empty
    def test_both_fields_empty(self, app):
        """Test form with both fields empty - invalid partition."""
        with app.test_request_context():
            form = LoginForm(data={
                'username': '',
                'password': ''
            })
            assert form.validate() is False
            assert 'username' in form.errors
            assert 'password' in form.errors

    # Equivalence Partitioning: None values
    def test_none_values(self, app):
        """Test form with None values - invalid partition."""
        with app.test_request_context():
            form = LoginForm(data={
                'username': None,
                'password': None
            })
            assert form.validate() is False

    # Equivalence Partitioning: Whitespace only
    def test_whitespace_only(self, app):
        """Test form with whitespace only - invalid partition."""
        with app.test_request_context():
            form = LoginForm(data={
                'username': '   ',
                'password': '   '
            })
            # WTForms DataRequired fails on whitespace-only strings
            # This tests that the form rejects whitespace-only input
            assert form.validate() is False  # Form validation should fail

    # BVA: Very long username
    def test_very_long_username(self, app):
        """Test form with very long username - boundary test."""
        with app.test_request_context():
            long_username = 'a' * 1000
            form = LoginForm(data={
                'username': long_username,
                'password': 'password123'
            })
            # Form should accept it, but database constraint would fail
            assert form.validate() is True

    # BVA: Very long password
    def test_very_long_password(self, app):
        """Test form with very long password - boundary test."""
        with app.test_request_context():
            long_password = 'p' * 1000
            form = LoginForm(data={
                'username': 'testuser',
                'password': long_password
            })
            # Form should accept it for login attempts
            assert form.validate() is True

    # Special characters
    def test_special_characters_in_username(self, app):
        """Test username with special characters."""
        with app.test_request_context():
            form = LoginForm(data={
                'username': 'test@user!#$',
                'password': 'password123'
            })
            assert form.validate() is True

    def test_special_characters_in_password(self, app):
        """Test password with special characters."""
        with app.test_request_context():
            form = LoginForm(data={
                'username': 'testuser',
                'password': 'P@ssw0rd!#$%^&*()'
            })
            assert form.validate() is True


@pytest.mark.unit
@pytest.mark.forms
@pytest.mark.blackbox
class TestChangePasswordForm:
    """
    Test suite for ChangePasswordForm.
    Uses equivalence partitioning and BVA for password validation.
    """

    # Valid partition
    def test_valid_password_change(self, app):
        """Test form with valid passwords - valid partition."""
        with app.test_request_context():
            form = ChangePasswordForm(data={
                'currentPassword': 'oldpassword',
                'newPassword': 'newpassword123',
                'confirmPassword': 'newpassword123'
            })
            assert form.validate() is True

    # BVA: Minimum password length (8 characters - boundary)
    def test_minimum_valid_password_length(self, app):
        """Test minimum valid password length (exactly 8) - BVA."""
        with app.test_request_context():
            form = ChangePasswordForm(data={
                'currentPassword': 'oldpassword',
                'newPassword': '12345678',  # Exactly 8 chars
                'confirmPassword': '12345678'
            })
            assert form.validate() is True

    # BVA: Below minimum password length (7 characters)
    def test_below_minimum_password_length(self, app):
        """Test below minimum password length (7 chars) - BVA."""
        with app.test_request_context():
            form = ChangePasswordForm(data={
                'currentPassword': 'oldpassword',
                'newPassword': '1234567',  # 7 chars - too short
                'confirmPassword': '1234567'
            })
            assert form.validate() is False
            assert 'newPassword' in form.errors

    # BVA: Empty password - boundary case
    def test_empty_new_password(self, app):
        """Test empty new password - BVA."""
        with app.test_request_context():
            form = ChangePasswordForm(data={
                'currentPassword': 'oldpassword',
                'newPassword': '',
                'confirmPassword': ''
            })
            assert form.validate() is False
            assert 'newPassword' in form.errors

    # BVA: Single character password
    def test_single_character_password(self, app):
        """Test single character password - BVA."""
        with app.test_request_context():
            form = ChangePasswordForm(data={
                'currentPassword': 'oldpassword',
                'newPassword': 'a',
                'confirmPassword': 'a'
            })
            assert form.validate() is False

    # BVA: Very long password
    def test_very_long_password(self, app):
        """Test very long password (200 chars) - BVA."""
        with app.test_request_context():
            long_password = 'a' * 200
            form = ChangePasswordForm(data={
                'currentPassword': 'oldpassword',
                'newPassword': long_password,
                'confirmPassword': long_password
            })
            assert form.validate() is True

    # Equivalence Partitioning: Mismatched passwords
    def test_password_mismatch(self, app):
        """Test mismatched new and confirm passwords - invalid partition."""
        with app.test_request_context():
            form = ChangePasswordForm(data={
                'currentPassword': 'oldpassword',
                'newPassword': 'newpassword123',
                'confirmPassword': 'differentpassword'
            })
            assert form.validate() is False
            assert 'confirmPassword' in form.errors

    # Equivalence Partitioning: Missing current password
    def test_missing_current_password(self, app):
        """Test missing current password - invalid partition."""
        with app.test_request_context():
            form = ChangePasswordForm(data={
                'currentPassword': '',
                'newPassword': 'newpassword123',
                'confirmPassword': 'newpassword123'
            })
            assert form.validate() is False
            assert 'currentPassword' in form.errors

    # Equivalence Partitioning: Missing confirm password
    def test_missing_confirm_password(self, app):
        """Test missing confirm password - invalid partition."""
        with app.test_request_context():
            form = ChangePasswordForm(data={
                'currentPassword': 'oldpassword',
                'newPassword': 'newpassword123',
                'confirmPassword': ''
            })
            assert form.validate() is False
            assert 'confirmPassword' in form.errors

    # Equivalence Partitioning: All fields empty
    def test_all_fields_empty(self, app):
        """Test all fields empty - invalid partition."""
        with app.test_request_context():
            form = ChangePasswordForm(data={
                'currentPassword': '',
                'newPassword': '',
                'confirmPassword': ''
            })
            assert form.validate() is False
            assert 'currentPassword' in form.errors
            assert 'newPassword' in form.errors
            assert 'confirmPassword' in form.errors

    # Edge case: Whitespace passwords
    def test_whitespace_in_passwords(self, app):
        """Test passwords with whitespace."""
        with app.test_request_context():
            form = ChangePasswordForm(data={
                'currentPassword': 'old password',
                'newPassword': 'new password 123',
                'confirmPassword': 'new password 123'
            })
            assert form.validate() is True  # Whitespace is valid

    # Edge case: Special characters
    def test_special_characters_in_passwords(self, app):
        """Test passwords with special characters."""
        with app.test_request_context():
            password = 'P@ssw0rd!#$%^&*()_+'
            form = ChangePasswordForm(data={
                'currentPassword': 'oldpassword',
                'newPassword': password,
                'confirmPassword': password
            })
            assert form.validate() is True

    # Edge case: Unicode characters
    def test_unicode_characters_in_passwords(self, app):
        """Test passwords with unicode characters."""
        with app.test_request_context():
            password = 'пароль密码🔒'
            form = ChangePasswordForm(data={
                'currentPassword': 'oldpassword',
                'newPassword': password,
                'confirmPassword': password
            })
            # Should be valid if length >= 8
            if len(password) >= 8:
                assert form.validate() is True
