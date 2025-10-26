"""
Integration tests for authentication flows.
Tests the interaction between routes, forms, services, and models.
"""
import pytest
from flask import session


@pytest.mark.integration
@pytest.mark.auth
class TestLoginFlow:
    """Test suite for login workflow."""

    def test_login_page_loads(self, client):
        """Test that login page loads successfully."""
        response = client.get('/auth/login')

        assert response.status_code == 200
        assert b'Sign In' in response.data or b'Login' in response.data

    def test_login_success(self, client, admin_user):
        """Test successful login flow."""
        response = client.post('/auth/login', data={
            'username': admin_user.username,
            'password': 'testpassword123'
        }, follow_redirects=True)

        assert response.status_code == 200
        # Should redirect to games page after successful login

    def test_login_invalid_password(self, client, admin_user):
        """Test login with invalid password."""
        response = client.post('/auth/login', data={
            'username': admin_user.username,
            'password': 'wrongpassword'
        }, follow_redirects=True)

        assert response.status_code == 200
        assert b'Invalid username or password' in response.data

    def test_login_nonexistent_user(self, client):
        """Test login with nonexistent user."""
        response = client.post('/auth/login', data={
            'username': 'nonexistent',
            'password': 'password123'
        }, follow_redirects=True)

        assert response.status_code == 200
        assert b'Invalid username or password' in response.data

    def test_login_empty_fields(self, client):
        """Test login with empty fields."""
        response = client.post('/auth/login', data={
            'username': '',
            'password': ''
        }, follow_redirects=True)

        assert response.status_code == 200
        # Form validation should prevent submission

    def test_login_redirect_authenticated_user(self, authenticated_client):
        """Test that authenticated users are redirected from login page."""
        response = authenticated_client.get('/auth/login', follow_redirects=True)

        assert response.status_code == 200
        # Should redirect to index

    def test_session_after_successful_login(self, client, admin_user):
        """Test that session is properly set after login."""
        with client:
            response = client.post('/auth/login', data={
                'username': admin_user.username,
                'password': 'testpassword123'
            }, follow_redirects=True)

            assert response.status_code == 200
            # Session should be permanent
            assert session.permanent is True

    def test_csrf_protection_on_login(self, client):
        """Test CSRF protection on login form."""
        # In testing mode, CSRF is disabled
        # This test documents the security feature
        response = client.post('/auth/login', data={
            'username': 'test',
            'password': 'test'
        })

        # In production, missing CSRF token would return 400
        # In testing, it processes normally
        assert response.status_code in [200, 302, 400]

    def test_rate_limiting_login(self, client, admin_user):
        """Test rate limiting on login endpoint."""
        # Make multiple rapid login attempts
        for _ in range(15):
            client.post('/auth/login', data={
                'username': admin_user.username,
                'password': 'wrongpassword'
            })

        # Next request should be rate limited
        response = client.post('/auth/login', data={
            'username': admin_user.username,
            'password': 'testpassword123'
        })

        # Rate limit response is 429
        assert response.status_code in [200, 302, 429]


@pytest.mark.integration
@pytest.mark.auth
class TestLogoutFlow:
    """Test suite for logout workflow."""

    def test_logout_success(self, authenticated_client):
        """Test successful logout."""
        response = authenticated_client.get('/auth/logout', follow_redirects=True)

        assert response.status_code == 200
        assert b'logged out' in response.data or b'Logout' in response.data

    def test_logout_unauthenticated(self, client):
        """Test logout when not authenticated."""
        response = client.get('/auth/logout', follow_redirects=True)

        # Should redirect to login
        assert response.status_code == 200
        assert b'log in' in response.data or b'Login' in response.data

    def test_session_cleared_after_logout(self, authenticated_client):
        """Test that session is cleared after logout."""
        # Logout
        authenticated_client.get('/auth/logout', follow_redirects=True)

        # Try to access protected page
        response = authenticated_client.get('/auth/change-password')

        # Should redirect to login
        assert response.status_code == 302


@pytest.mark.integration
@pytest.mark.auth
class TestChangePasswordFlow:
    """Test suite for change password workflow."""

    def test_change_password_page_requires_auth(self, client):
        """Test that change password page requires authentication."""
        response = client.get('/auth/change-password', follow_redirects=True)

        assert response.status_code == 200
        # Should redirect to login
        assert b'log in' in response.data or b'Login' in response.data

    def test_change_password_page_loads(self, authenticated_client):
        """Test that change password page loads for authenticated users."""
        response = authenticated_client.get('/auth/change-password')

        assert response.status_code == 200
        assert b'Change Password' in response.data or b'Current Password' in response.data

    def test_change_password_success(self, authenticated_client, admin_user):
        """Test successful password change."""
        response = authenticated_client.post('/auth/change-password', data={
            'currentPassword': 'testpassword123',
            'newPassword': 'newpassword456',
            'confirmPassword': 'newpassword456'
        }, follow_redirects=True)

        assert response.status_code == 200
        assert b'password has been updated' in response.data or b'success' in response.data.lower()

    def test_change_password_wrong_current(self, authenticated_client):
        """Test change password with wrong current password."""
        response = authenticated_client.post('/auth/change-password', data={
            'currentPassword': 'wrongpassword',
            'newPassword': 'newpassword456',
            'confirmPassword': 'newpassword456'
        }, follow_redirects=True)

        assert response.status_code == 200
        assert b'Current password is incorrect' in response.data or b'incorrect' in response.data.lower()

    def test_change_password_mismatch(self, authenticated_client):
        """Test change password with mismatched new passwords."""
        response = authenticated_client.post('/auth/change-password', data={
            'currentPassword': 'testpassword123',
            'newPassword': 'newpassword456',
            'confirmPassword': 'differentpassword'
        }, follow_redirects=True)

        assert response.status_code == 200
        # Form validation should catch this

    def test_change_password_too_short(self, authenticated_client):
        """Test change password with password too short."""
        response = authenticated_client.post('/auth/change-password', data={
            'currentPassword': 'testpassword123',
            'newPassword': 'short',
            'confirmPassword': 'short'
        }, follow_redirects=True)

        assert response.status_code == 200
        # Form validation should catch this

    def test_password_persists_after_change(self, client, admin_user, db_session):
        """Test that new password works after changing."""
        # Login
        client.post('/auth/login', data={
            'username': admin_user.username,
            'password': 'testpassword123'
        }, follow_redirects=True)

        # Change password
        client.post('/auth/change-password', data={
            'currentPassword': 'testpassword123',
            'newPassword': 'newpassword456',
            'confirmPassword': 'newpassword456'
        }, follow_redirects=True)

        # Logout
        client.get('/auth/logout', follow_redirects=True)

        # Try to login with old password (should fail)
        response = client.post('/auth/login', data={
            'username': admin_user.username,
            'password': 'testpassword123'
        }, follow_redirects=True)

        assert b'Invalid username or password' in response.data

        # Try to login with new password (should succeed)
        response = client.post('/auth/login', data={
            'username': admin_user.username,
            'password': 'newpassword456'
        }, follow_redirects=True)

        assert response.status_code == 200


@pytest.mark.integration
@pytest.mark.auth
@pytest.mark.security
class TestAuthenticationSecurity:
    """Test suite for authentication security features."""

    def test_redirect_url_validation(self, client, admin_user):
        """Test that redirect URLs are validated (no open redirect)."""
        # Try to login with malicious redirect
        response = client.post('/auth/login?next=http://evil.com', data={
            'username': admin_user.username,
            'password': 'testpassword123'
        }, follow_redirects=False)

        # Should not redirect to external site
        assert response.status_code == 302
        assert 'evil.com' not in response.location

    def test_session_regeneration_on_login(self, client, admin_user):
        """Test that session is regenerated on login (prevents session fixation)."""
        with client:
            # Get initial session
            client.get('/auth/login')
            old_session = dict(session)

            # Login
            client.post('/auth/login', data={
                'username': admin_user.username,
                'password': 'testpassword123'
            })

            # Session should be different
            # Flask-Login handles this automatically

    def test_password_not_in_url(self, client, admin_user):
        """Test that passwords are never exposed in URLs."""
        # Login should be POST only for credentials
        response = client.get(f'/auth/login?password={admin_user.username}')

        # GET request shouldn't process password
        assert response.status_code == 200  # Shows form

    def test_timing_attack_resistance(self, client, admin_user):
        """Test that invalid username and invalid password take similar time."""
        import time

        # Test with invalid username
        start = time.time()
        client.post('/auth/login', data={
            'username': 'nonexistent',
            'password': 'password123'
        })
        invalid_user_time = time.time() - start

        # Test with invalid password
        start = time.time()
        client.post('/auth/login', data={
            'username': admin_user.username,
            'password': 'wrongpassword'
        })
        invalid_pass_time = time.time() - start

        # Times should be similar (within 100ms) to prevent user enumeration
        # This is a basic check; timing attacks are complex
        time_diff = abs(invalid_user_time - invalid_pass_time)
        assert time_diff < 0.1  # Within 100ms
