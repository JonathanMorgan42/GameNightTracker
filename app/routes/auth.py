"""Authentication routes."""
from flask import Blueprint, render_template, redirect, url_for, flash, request, session
from flask_login import login_user, logout_user, login_required, current_user
from urllib.parse import urlparse, urljoin

from app import limiter
from app.services import AuthService
from app.forms import LoginForm, ChangePasswordForm

auth_bp = Blueprint('auth', __name__)


def is_safe_url(target):
    """Check if redirect URL is safe (same host, relative path)."""
    if not target:
        return False

    ref_url = urlparse(request.host_url)
    test_url = urlparse(urljoin(request.host_url, target))

    return test_url.scheme in ('http', 'https') and ref_url.netloc == test_url.netloc


@auth_bp.route('/login', methods=['GET', 'POST'])
@limiter.limit("10 per minute")
def login():
    """Login page."""
    if current_user.is_authenticated:
        return redirect(url_for('main.index'))

    form = LoginForm()

    if form.validate_on_submit():
        admin = AuthService.authenticate(form.username.data, form.password.data)

        if admin:
            # Regenerate session to prevent session fixation
            session.permanent = True
            login_user(admin)

            # Redirect to next page or games (with proper validation)
            next_page = request.args.get('next')
            if next_page and is_safe_url(next_page):
                return redirect(next_page)
            else:
                return redirect(url_for('main.games'))
        else:
            flash('Invalid username or password', 'error')

    return render_template('admin/login.html', form=form)


@auth_bp.route('/logout')
@login_required
def logout():
    """Logout."""
    logout_user()
    flash('You have been logged out', 'success')
    return redirect(url_for('auth.login'))


@auth_bp.route('/change-password', methods=['GET', 'POST'])
@login_required
def change_password():
    """Change password."""
    form = ChangePasswordForm()

    if form.validate_on_submit():
        success = AuthService.change_password(
            current_user,
            form.currentPassword.data,
            form.newPassword.data
        )

        if success:
            flash('Your password has been updated.', 'success')
            return redirect(url_for('main.games'))
        else:
            flash('Current password is incorrect.', 'error')

    return render_template('admin/change_password.html', form=form)