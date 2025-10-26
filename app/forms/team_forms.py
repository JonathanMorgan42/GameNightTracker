from flask_wtf import FlaskForm
from wtforms import StringField, SubmitField
from wtforms.validators import DataRequired, Regexp, Optional, Length
from app.utils.validators import (
    TEAM_NAME_MIN, TEAM_NAME_MAX,
    PARTICIPANT_NAME_MIN, PARTICIPANT_NAME_MAX,
    get_length_error_message
)


class ParticipantForm(FlaskForm):
    firstName = StringField('First Name')
    lastName = StringField('Last Name')


class TeamForm(FlaskForm):
    name = StringField('Team Name', validators=[
        DataRequired(message='Team name is required'),
        Length(
            min=TEAM_NAME_MIN,
            max=TEAM_NAME_MAX,
            message=get_length_error_message('Team name', TEAM_NAME_MIN, TEAM_NAME_MAX)
        )
    ], render_kw={'maxlength': TEAM_NAME_MAX})
    color = StringField('Team Color', validators=[
        DataRequired(),
        Regexp(r'^#[0-9A-Fa-f]{6}$', message='Must be a valid hex color code')
    ], default='#3b82f6', render_kw={'maxlength': 7})

    # Keep individual fields for easier validation and backwards compatibility
    participant1FirstName = StringField('First Name', validators=[
        DataRequired(message='First name is required'),
        Length(
            min=PARTICIPANT_NAME_MIN,
            max=PARTICIPANT_NAME_MAX,
            message=get_length_error_message('First name', PARTICIPANT_NAME_MIN, PARTICIPANT_NAME_MAX)
        )
    ], render_kw={'maxlength': PARTICIPANT_NAME_MAX})
    participant1LastName = StringField('Last Name', validators=[
        DataRequired(message='Last name is required'),
        Length(
            min=PARTICIPANT_NAME_MIN,
            max=PARTICIPANT_NAME_MAX,
            message=get_length_error_message('Last name', PARTICIPANT_NAME_MIN, PARTICIPANT_NAME_MAX)
        )
    ], render_kw={'maxlength': PARTICIPANT_NAME_MAX})
    participant2FirstName = StringField('First Name', validators=[
        DataRequired(message='First name is required'),
        Length(
            min=PARTICIPANT_NAME_MIN,
            max=PARTICIPANT_NAME_MAX,
            message=get_length_error_message('First name', PARTICIPANT_NAME_MIN, PARTICIPANT_NAME_MAX)
        )
    ], render_kw={'maxlength': PARTICIPANT_NAME_MAX})
    participant2LastName = StringField('Last Name', validators=[
        DataRequired(message='Last name is required'),
        Length(
            min=PARTICIPANT_NAME_MIN,
            max=PARTICIPANT_NAME_MAX,
            message=get_length_error_message('Last name', PARTICIPANT_NAME_MIN, PARTICIPANT_NAME_MAX)
        )
    ], render_kw={'maxlength': PARTICIPANT_NAME_MAX})

    # Additional participants (optional)
    participant3FirstName = StringField('First Name', validators=[
        Optional(),
        Length(
            max=PARTICIPANT_NAME_MAX,
            message=get_length_error_message('First name', PARTICIPANT_NAME_MIN, PARTICIPANT_NAME_MAX)
        )
    ], render_kw={'maxlength': PARTICIPANT_NAME_MAX})
    participant3LastName = StringField('Last Name', validators=[
        Optional(),
        Length(
            max=PARTICIPANT_NAME_MAX,
            message=get_length_error_message('Last name', PARTICIPANT_NAME_MIN, PARTICIPANT_NAME_MAX)
        )
    ], render_kw={'maxlength': PARTICIPANT_NAME_MAX})
    participant4FirstName = StringField('First Name', validators=[
        Optional(),
        Length(
            max=PARTICIPANT_NAME_MAX,
            message=get_length_error_message('First name', PARTICIPANT_NAME_MIN, PARTICIPANT_NAME_MAX)
        )
    ], render_kw={'maxlength': PARTICIPANT_NAME_MAX})
    participant4LastName = StringField('Last Name', validators=[
        Optional(),
        Length(
            max=PARTICIPANT_NAME_MAX,
            message=get_length_error_message('Last name', PARTICIPANT_NAME_MIN, PARTICIPANT_NAME_MAX)
        )
    ], render_kw={'maxlength': PARTICIPANT_NAME_MAX})
    participant5FirstName = StringField('First Name', validators=[
        Optional(),
        Length(
            max=PARTICIPANT_NAME_MAX,
            message=get_length_error_message('First name', PARTICIPANT_NAME_MIN, PARTICIPANT_NAME_MAX)
        )
    ], render_kw={'maxlength': PARTICIPANT_NAME_MAX})
    participant5LastName = StringField('Last Name', validators=[
        Optional(),
        Length(
            max=PARTICIPANT_NAME_MAX,
            message=get_length_error_message('Last name', PARTICIPANT_NAME_MIN, PARTICIPANT_NAME_MAX)
        )
    ], render_kw={'maxlength': PARTICIPANT_NAME_MAX})
    participant6FirstName = StringField('First Name', validators=[
        Optional(),
        Length(
            max=PARTICIPANT_NAME_MAX,
            message=get_length_error_message('First name', PARTICIPANT_NAME_MIN, PARTICIPANT_NAME_MAX)
        )
    ], render_kw={'maxlength': PARTICIPANT_NAME_MAX})
    participant6LastName = StringField('Last Name', validators=[
        Optional(),
        Length(
            max=PARTICIPANT_NAME_MAX,
            message=get_length_error_message('Last name', PARTICIPANT_NAME_MIN, PARTICIPANT_NAME_MAX)
        )
    ], render_kw={'maxlength': PARTICIPANT_NAME_MAX})

    submit = SubmitField('Save Team')
