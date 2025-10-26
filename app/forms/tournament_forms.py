from flask_wtf import FlaskForm
from wtforms import (
    SelectField,
    BooleanField, SubmitField, HiddenField,
    FloatField
)
from wtforms.validators import DataRequired, Optional, NumberRange
from app.utils.validators import (
    MATCH_SCORE_MIN, MATCH_SCORE_MAX,
    get_range_error_message
)


class TournamentSetupForm(FlaskForm):
    game_id = HiddenField('Game ID', validators=[DataRequired()])

    pairing_type = SelectField(
        'Team Pairing',
        choices=[
            ('random', 'Random Pairing'),
            ('manual', 'Manual Pairing')
        ],
        validators=[DataRequired()],
        default='random'
    )

    bracket_style = SelectField(
        'Bracket Style',
        choices=[
            ('standard', 'Standard (Auto-Bye for odd teams)'),
            ('play_in', 'Play-in Match (All teams compete first)')
        ],
        validators=[DataRequired()],
        default='standard'
    )

    public_edit = BooleanField(
        'Allow Public Editing',
        default=False
    )

    submit = SubmitField('Create Tournament Bracket')


class MatchScoreForm(FlaskForm):
    match_id = HiddenField('Match ID', validators=[DataRequired()])
    team1_score = FloatField('Team 1 Score', validators=[
        Optional(),
        NumberRange(
            min=MATCH_SCORE_MIN,
            max=MATCH_SCORE_MAX,
            message=get_range_error_message('Match score', MATCH_SCORE_MIN, MATCH_SCORE_MAX)
        )
    ])
    team2_score = FloatField('Team 2 Score', validators=[
        Optional(),
        NumberRange(
            min=MATCH_SCORE_MIN,
            max=MATCH_SCORE_MAX,
            message=get_range_error_message('Match score', MATCH_SCORE_MIN, MATCH_SCORE_MAX)
        )
    ])
    winner_team_id = HiddenField('Winner Team ID', validators=[DataRequired()])
    submit = SubmitField('Save Match Result')
