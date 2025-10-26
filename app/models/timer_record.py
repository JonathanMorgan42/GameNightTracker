from datetime import datetime
from app import db


class TimerRecord(db.Model):
    """Store multiple timer recordings for multi-user timing."""
    __tablename__ = 'timer_record'

    id = db.Column(db.Integer, primary_key=True)
    game_id = db.Column(db.Integer, db.ForeignKey('game.id'), nullable=False)
    team_id = db.Column(db.Integer, db.ForeignKey('team.id'), nullable=False)
    user_id = db.Column(db.String(100), nullable=False)
    user_display_name = db.Column(db.String(100), nullable=True)
    time_value = db.Column(db.Float, nullable=False)
    recorded_at = db.Column(db.DateTime, default=datetime.utcnow)
    is_active = db.Column(db.Boolean, default=True)

    # Relationships
    game = db.relationship('Game', backref='timer_records')
    team = db.relationship('Team', backref='timer_records')

    # Index for efficient querying
    __table_args__ = (
        db.Index('idx_timer_game_team', 'game_id', 'team_id', 'is_active'),
    )

    def __repr__(self):
        return f'<TimerRecord game_id={self.game_id} team_id={self.team_id} time={self.time_value} user={self.user_display_name}>'
