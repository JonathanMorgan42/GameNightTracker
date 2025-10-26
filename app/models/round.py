from app import db


class Round(db.Model):
    """
    Represents a single round within a multi-round game.

    A round is a subdivision of a game where teams compete separately
    and scores are tracked independently for each round.
    """
    __tablename__ = 'round'
    __table_args__ = (
        db.Index('ix_round_game_number', 'game_id', 'round_number'),
    )

    id = db.Column(db.Integer, primary_key=True)
    game_id = db.Column(db.Integer, db.ForeignKey('game.id'), nullable=False, index=True)
    round_number = db.Column(db.Integer, nullable=False)  # 1-indexed (1, 2, 3...)
    description = db.Column(db.String(200), nullable=True)  # Optional description (e.g., "First Half", "Sudden Death")

    # Relationships
    game = db.relationship('Game', back_populates='rounds')
    round_scores = db.relationship('RoundScore', back_populates='round', lazy='dynamic', cascade='all, delete-orphan')

    def __repr__(self):
        return f'<Round {self.round_number} for Game {self.game_id}>'

    @property
    def name(self):
        """Generate a display name for the round."""
        if self.description:
            return f"Round {self.round_number}: {self.description}"
        return f"Round {self.round_number}"
