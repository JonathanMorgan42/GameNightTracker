from app import db


class Tournament(db.Model):
    __tablename__ = 'tournament'

    id = db.Column(db.Integer, primary_key=True)
    game_id = db.Column(db.Integer, db.ForeignKey('game.id'), nullable=False, unique=True)

    # Tournament settings
    pairing_type = db.Column(db.String(20), default='random')  # 'random' or 'manual'
    public_edit = db.Column(db.Boolean, default=False)
    bracket_style = db.Column(db.String(20), default='standard')  # 'standard', 'play_in', 'auto_bye'

    # Play-in match settings (for odd team counts)
    play_in_match_id = db.Column(db.Integer, db.ForeignKey('match.id'), nullable=True)

    # Tournament state
    is_started = db.Column(db.Boolean, default=False)
    is_completed = db.Column(db.Boolean, default=False)
    winner_team_id = db.Column(db.Integer, db.ForeignKey('team.id'), nullable=True)

    # Relationships
    game = db.relationship('Game', backref=db.backref('tournament', uselist=False, cascade='all, delete-orphan'))
    matches = db.relationship('Match', back_populates='tournament',
                            foreign_keys='Match.tournament_id',
                            lazy='dynamic', cascade='all, delete-orphan')
    play_in_match = db.relationship('Match', foreign_keys=[play_in_match_id],
                                   post_update=True, uselist=False)
    winner_team = db.relationship('Team', foreign_keys=[winner_team_id])

    def __repr__(self):
        return f'<Tournament for Game: {self.game_id}>'
