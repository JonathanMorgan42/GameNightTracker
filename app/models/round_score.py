from app import db


class RoundScore(db.Model):
    """
    Represents a team's score for a specific round within a game.

    This model stores the score value and calculated points for each team
    in each round, allowing for round-by-round scoring and cumulative totals.
    """
    __tablename__ = 'round_score'
    __table_args__ = (
        db.Index('ix_round_score_round_team', 'round_id', 'team_id'),
        db.UniqueConstraint('round_id', 'team_id', name='uix_round_team'),  # One score per team per round
    )

    id = db.Column(db.Integer, primary_key=True)
    round_id = db.Column(db.Integer, db.ForeignKey('round.id'), nullable=False, index=True)
    team_id = db.Column(db.Integer, db.ForeignKey('team.id'), nullable=False, index=True)
    score_value = db.Column(db.Float, nullable=True)  # The raw score (time, points, etc.)
    points = db.Column(db.Integer, default=0)  # Calculated points based on ranking
    notes = db.Column(db.Text, nullable=True)  # Optional notes for this round score

    # Multi-timer support fields (for time-based games)
    multi_timer_avg = db.Column(db.Float, nullable=True)
    timer_count = db.Column(db.Integer, default=0)

    # Relationships
    round = db.relationship('Round', back_populates='round_scores')
    team = db.relationship('Team', back_populates='round_scores')

    def __repr__(self):
        return f'<RoundScore Round:{self.round_id} Team:{self.team_id} Points:{self.points}>'
