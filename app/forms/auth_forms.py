from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, SubmitField
from wtforms.validators import DataRequired, Length, EqualTo


class LoginForm(FlaskForm):
    username = StringField('Username', validators=[DataRequired()])
    password = PasswordField('Password', validators=[DataRequired()])
    submit = SubmitField('Sign In')


class ChangePasswordForm(FlaskForm):
    currentPassword = PasswordField('Current Password', validators=[DataRequired()])
    newPassword = PasswordField(
        'New Password',
        validators=[
            DataRequired(),
            Length(min=8, message='Password must be at least 8 characters long.')
        ]
    )
    confirmPassword = PasswordField(
        'Confirm New Password',
        validators=[
            DataRequired(),
            EqualTo('newPassword', message='Passwords must match.')
        ]
    )
    submit = SubmitField('Update Password')