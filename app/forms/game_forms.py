from flask_wtf import FlaskForm
from wtforms import (
    StringField, SelectField, IntegerField,
    BooleanField, SubmitField, TextAreaField
)
from wtforms.validators import DataRequired, NumberRange, Length, Optional
from app.utils.validators import (
    GAME_NAME_MIN, GAME_NAME_MAX,
    GAME_CUSTOM_TYPE_MAX,
    POINT_MULTIPLIER_MIN, POINT_MULTIPLIER_MAX,
    SEQUENCE_NUMBER_MIN, SEQUENCE_NUMBER_MAX,
    SCORE_NOTES_MAX,
    get_length_error_message,
    get_range_error_message
)


class GameForm(FlaskForm):
    name = StringField('Game Name', validators=[
        DataRequired(message='Game name is required'),
        Length(
            min=GAME_NAME_MIN,
            max=GAME_NAME_MAX,
            message=get_length_error_message('Game name', GAME_NAME_MIN, GAME_NAME_MAX)
        )
    ], render_kw={'maxlength': GAME_NAME_MAX})
    type = SelectField(
        'Game Type',
        choices=[
            ('trivia', 'Trivia'),
            ('physical', 'Physical Challenge'),
            ('strategy', 'Strategy'),
            ('custom', 'Custom Type...')
        ],
        validators=[DataRequired()]
    )
    custom_type = StringField('Custom Game Type', validators=[
        Optional(),
        Length(
            max=GAME_CUSTOM_TYPE_MAX,
            message=f'Custom game type must not exceed {GAME_CUSTOM_TYPE_MAX} characters'
        )
    ], render_kw={'maxlength': GAME_CUSTOM_TYPE_MAX})
    sequence_number = IntegerField(
        'Game Sequence Number',
        validators=[
            DataRequired(),
            NumberRange(
                min=SEQUENCE_NUMBER_MIN,
                max=SEQUENCE_NUMBER_MAX,
                message=get_range_error_message('Sequence number', SEQUENCE_NUMBER_MIN, SEQUENCE_NUMBER_MAX)
            )
        ],
        default=0
    )
    point_scheme = IntegerField(
        'Point Multiplier',
        validators=[
            DataRequired(),
            NumberRange(
                min=POINT_MULTIPLIER_MIN,
                max=POINT_MULTIPLIER_MAX,
                message=get_range_error_message('Point multiplier', POINT_MULTIPLIER_MIN, POINT_MULTIPLIER_MAX)
            )
        ],
        default=1
    )
    metric_type = SelectField(
        'Scoring Method',
        choices=[
            ('score', 'Score Input'),
            ('time', 'Time (Stopwatch)')
        ],
        validators=[DataRequired()]
    )
    scoring_direction = SelectField(
        'Scoring Direction',
        choices=[
            ('lower_better', 'Lower is Better (e.g., time-based)'),
            ('higher_better', 'Higher is Better (e.g., points-based)')
        ],
        validators=[DataRequired()],
        default='lower_better'
    )
    public_input = BooleanField('Allow Public Score Input', default=False)
    has_rounds = BooleanField('Enable Round-by-Round Scoring', default=False)
    number_of_rounds = IntegerField(
        'Number of Rounds',
        validators=[
            Optional(),
            NumberRange(
                min=1,
                max=50,
                message='Number of rounds must be between 1 and 50'
            )
        ],
        default=1
    )
    submit = SubmitField('Save Game')


class LiveScoringForm(FlaskForm):
    game_id = StringField('Game ID', validators=[DataRequired()])
    game_notes = TextAreaField('Game Notes', validators=[
        Optional(),
        Length(
            max=SCORE_NOTES_MAX,
            message=f'Game notes must not exceed {SCORE_NOTES_MAX} characters'
        )
    ], render_kw={'maxlength': SCORE_NOTES_MAX})
    is_completed = BooleanField('Mark game as completed', default=True)
    submit = SubmitField('Save Final Scores')