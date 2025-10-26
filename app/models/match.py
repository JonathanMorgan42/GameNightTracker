from app import db


class Match(db.Model):
    __tablename__ = 'match'
    __table_args__ = (
        db.Index('ix_match_tournament_round', 'tournament_id', 'round_number'),  # Composite index for tournament bracket queries
    )

    id = db.Column(db.Integer, primary_key=True)
    tournament_id = db.Column(db.Integer, db.ForeignKey('tournament.id'), nullable=False)

    # Match positioning in bracket
    round_number = db.Column(db.Integer, nullable=False)  # 1 = first round, 2 = semi, 3 = final, etc.
    position_in_round = db.Column(db.Integer, nullable=False)  # Position within that round

    # Teams in this match
    team1_id = db.Column(db.Integer, db.ForeignKey('team.id'), nullable=True)
    team2_id = db.Column(db.Integer, db.ForeignKey('team.id'), nullable=True)

    # Match results
    team1_score = db.Column(db.Float, nullable=True)
    team2_score = db.Column(db.Float, nullable=True)
    winner_team_id = db.Column(db.Integer, db.ForeignKey('team.id'), nullable=True)

    # Match state
    status = db.Column(db.String(20), default='pending')  # 'pending', 'in_progress', 'completed'
    is_bye = db.Column(db.Boolean, default=False)  # True if one team advances automatically

    # Bracket structure - where does winner go?
    next_match_id = db.Column(db.Integer, db.ForeignKey('match.id'), nullable=True)
    next_match_position = db.Column(db.String(10), nullable=True)  # 'team1' or 'team2'

    # Special flags
    is_play_in = db.Column(db.Boolean, default=False)  # True if this is a play-in match for odd teams

    # Relationships
    tournament = db.relationship('Tournament', back_populates='matches', foreign_keys=[tournament_id])
    team1 = db.relationship('Team', foreign_keys=[team1_id], backref='matches_as_team1')
    team2 = db.relationship('Team', foreign_keys=[team2_id], backref='matches_as_team2')
    winner_team = db.relationship('Team', foreign_keys=[winner_team_id])
    next_match = db.relationship('Match', remote_side=[id], foreign_keys=[next_match_id],
                                backref='previous_matches', uselist=False)

    def __repr__(self):
        return f'<Match {self.id}: Round {self.round_number}, Pos {self.position_in_round}>'

    @property
    def display_name(self):
        """Human-readable match name."""
        if self.is_play_in:
            return 'Play-in Match'

        round_names = {
            1: 'Round 1',
            2: 'Quarter-final',
            3: 'Semi-final',
            4: 'Final',
            5: 'Championship'
        }
        return round_names.get(self.round_number, f'Round {self.round_number}')

    @property
    def is_ready(self):
        """Check if match is ready to be played (both teams assigned)."""
        return self.team1_id is not None and self.team2_id is not None

    def set_winner(self, winner_team_id):
        """Set the winner and advance them to the next match."""
        if winner_team_id not in [self.team1_id, self.team2_id]:
            raise ValueError("Winner must be one of the competing teams")

        self.winner_team_id = winner_team_id
        self.status = 'completed'

        # Advance winner to next match if exists
        if self.next_match_id and self.next_match_position:
            if self.next_match_position == 'team1':
                self.next_match.team1_id = winner_team_id
            else:
                self.next_match.team2_id = winner_team_id
