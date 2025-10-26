from flask_wtf import FlaskForm
from wtforms import StringField, DateField
from wtforms.validators import DataRequired, Length
from datetime import date
from app.utils.validators import (
    GAME_NIGHT_NAME_MIN, GAME_NIGHT_NAME_MAX,
    get_length_error_message
)


class GameNightForm(FlaskForm):

    name = StringField(
        'Game Night Name',
        validators=[
            DataRequired(message='Name is required'),
            Length(
                min=GAME_NIGHT_NAME_MIN,
                max=GAME_NIGHT_NAME_MAX,
                message=get_length_error_message('Game Night Name', GAME_NIGHT_NAME_MIN, GAME_NIGHT_NAME_MAX)
            )
        ],
        render_kw={
            'placeholder': 'e.g., Epic Game Night, Summer Championship',
            'maxlength': GAME_NIGHT_NAME_MAX
        }
    )

    date = DateField(
        'Date',
        validators=[DataRequired(message='Date is required')],
        default=date.today,
        format='%Y-%m-%d',
        render_kw={'type': 'date'}
    )
