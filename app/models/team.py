from app import db


class Team(db.Model):
    __tablename__ = 'team'

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False, index=True)
    color = db.Column(db.String(7), nullable=False, default='#3b82f6')
    game_night_id = db.Column(db.Integer, db.ForeignKey('game_night.id'), nullable=True, index=True)

    scores = db.relationship('Score', back_populates='team', lazy='select', cascade='all, delete-orphan')
    participants = db.relationship('Participant', back_populates='team', lazy='select', cascade='all, delete-orphan')
    game_night = db.relationship('GameNight', back_populates='teams')
    round_scores = db.relationship('RoundScore', back_populates='team', lazy='select', cascade='all, delete-orphan')
    
    @property
    def totalPoints(self):
        """
        Get total points across ALL game nights.
        Note: For game-night-specific points, use get_points_for_game_night()
        """
        return sum(score.points for score in self.scores)

    def get_points_for_game_night(self, game_night_id=None):
        """
        Get total points for a specific game night.

        Args:
            game_night_id: ID of the game night to filter by.
                          If None, uses this team's game_night_id.

        Returns:
            Total points for the specified game night
        """
        if game_night_id is None:
            game_night_id = self.game_night_id

        if game_night_id is None:
            return 0

        # Import here to avoid circular imports
        from app.models.game import Game

        # Join scores with games and filter by game_night_id
        total = 0
        for score in self.scores:
            if score.game and score.game.game_night_id == game_night_id:
                total += score.points

        return total

    @property
    def abbreviation(self):
        """
        Generate a short abbreviation from the team name for mobile displays.

        Logic:
        - Multi-word names: First letter of each word (e.g., "Super Team" → "ST")
        - Single-word names: First 2-3 characters (e.g., "Titans" → "TIT")

        Returns:
            Uppercase abbreviation string
        """
        if not self.name:
            return ""

        words = self.name.strip().split()

        if len(words) >= 2:
            # Multi-word: use first letter of each word
            return ''.join(word[0].upper() for word in words if word)
        else:
            # Single word: use first 2-3 characters
            single_word = words[0]
            if len(single_word) <= 3:
                return single_word.upper()
            else:
                return single_word[:3].upper()

    @property
    def games_played(self):
        return len(self.scores)

    def __repr__(self):
        return f'<Team {self.name}>'
