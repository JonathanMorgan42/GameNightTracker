from app import db


class Score(db.Model):
    __tablename__ = 'score'
    __table_args__ = (
        db.Index('ix_score_game_team', 'game_id', 'team_id'),  # Composite index for game+team lookups
    )

    id = db.Column(db.Integer, primary_key=True)
    points = db.Column(db.Integer, default=0)
    score_value = db.Column(db.Float, nullable=True)
    notes = db.Column(db.Text, nullable=True)
    team_id = db.Column(db.Integer, db.ForeignKey('team.id'), nullable=False)
    game_id = db.Column(db.Integer, db.ForeignKey('game.id'), nullable=False)

    # Multi-timer support fields
    multi_timer_avg = db.Column(db.Float, nullable=True)
    timer_count = db.Column(db.Integer, default=0)

    team = db.relationship('Team', back_populates='scores')
    game = db.relationship('Game', back_populates='scores')
