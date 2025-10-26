from datetime import datetime
from app import db


class ActiveEdit(db.Model):
    """Track which user is editing which score field."""
    __tablename__ = 'active_edit'

    id = db.Column(db.Integer, primary_key=True)
    game_id = db.Column(db.Integer, db.ForeignKey('game.id'), nullable=False)
    team_id = db.Column(db.Integer, db.ForeignKey('team.id'), nullable=False)
    field_name = db.Column(db.String(50), nullable=False)
    user_id = db.Column(db.String(100), nullable=False)
    user_display_name = db.Column(db.String(100), nullable=True)
    locked_at = db.Column(db.DateTime, default=datetime.utcnow)

    # Relationships
    game = db.relationship('Game', backref='active_edits')
    team = db.relationship('Team', backref='active_edits')

    # Unique constraint: one lock per field per team per game
    __table_args__ = (
        db.UniqueConstraint('game_id', 'team_id', 'field_name', name='uq_game_team_field_lock'),
    )

    def __repr__(self):
        return f'<ActiveEdit game_id={self.game_id} team_id={self.team_id} field={self.field_name} user={self.user_display_name}>'
