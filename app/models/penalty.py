from app import db


class Penalty(db.Model):
    __tablename__ = 'penalty'

    id = db.Column(db.Integer, primary_key=True)
    game_id = db.Column(db.Integer, db.ForeignKey('game.id'), nullable=False)
    name = db.Column(db.String(200), nullable=False)
    value = db.Column(db.Integer, nullable=False)
    stackable = db.Column(db.Boolean, default=False, nullable=False)  # Can apply multiple times

    game = db.relationship('Game', back_populates='penalties')

    @property
    def unit(self):
        """Unit is derived from the game's metric type."""
        return 'seconds' if self.game.metric_type == 'time' else 'points'
