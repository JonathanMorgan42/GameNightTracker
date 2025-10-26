from flask_wtf import FlaskForm
from wtforms import RadioField, TextAreaField, SubmitField
from wtforms.validators import DataRequired, Optional, Length


class FeedbackForm(FlaskForm):
    """Form for collecting user feedback about the app."""

    scoring_clarity = RadioField(
        'Was it easy to understand how the scoring works?',
        choices=[
            ('1', '1 - Very Confusing'),
            ('2', '2 - A Bit Unclear'),
            ('3', '3 - Okay'),
            ('4', '4 - Pretty Clear'),
            ('5', '5 - Crystal Clear')
        ],
        validators=[DataRequired(message='Please select a rating')]
    )

    overall_clarity = RadioField(
        'How clear and simple does the app feel overall?',
        choices=[
            ('1', '1 - Very Confusing'),
            ('2', '2 - A Bit Unclear'),
            ('3', '3 - Okay'),
            ('4', '4 - Pretty Clear'),
            ('5', '5 - Love It')
        ],
        validators=[DataRequired(message='Please select a rating')]
    )

    mobile_usability = RadioField(
        'How well does everything fit on your mobile screen?',
        choices=[
            ('1', '1 - Terrible'),
            ('2', '2 - Hard to Use'),
            ('3', '3 - Okay'),
            ('4', '4 - Works Well'),
            ('5', '5 - Perfect')
        ],
        validators=[DataRequired(message='Please select a rating')]
    )

    navigation_ease = RadioField(
        'How easy was it to navigate and find what you needed?',
        choices=[
            ('1', '1 - Very Difficult'),
            ('2', '2 - Somewhat Hard'),
            ('3', '3 - Okay'),
            ('4', '4 - Easy'),
            ('5', '5 - Very Easy')
        ],
        validators=[DataRequired(message='Please select a rating')]
    )

    visual_design = RadioField(
        'How would you rate the visual design and appearance?',
        choices=[
            ('1', '1 - Poor'),
            ('2', '2 - Below Average'),
            ('3', '3 - Average'),
            ('4', '4 - Good'),
            ('5', '5 - Excellent')
        ],
        validators=[DataRequired(message='Please select a rating')]
    )

    feature_satisfaction = RadioField(
        'How satisfied are you with the available features?',
        choices=[
            ('1', '1 - Very Unsatisfied'),
            ('2', '2 - Unsatisfied'),
            ('3', '3 - Neutral'),
            ('4', '4 - Satisfied'),
            ('5', '5 - Very Satisfied')
        ],
        validators=[DataRequired(message='Please select a rating')]
    )

    suggestions = TextAreaField(
        'Any suggestions or ideas to make things better?',
        validators=[Optional(), Length(max=500, message='Please keep suggestions under 500 characters')],
        render_kw={
            'placeholder': 'Share your thoughts here (optional)...',
            'rows': 4,
            'maxlength': 500
        }
    )

    submit = SubmitField('Submit Feedback')
