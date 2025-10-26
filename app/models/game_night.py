from datetime import datetime
from sqlalchemy.orm import joinedload
from app import db


class GameNight(db.Model):
    __tablename__ = 'game_night'

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(200), nullable=False)
    date = db.Column(db.Date, nullable=False)
    is_active = db.Column(db.Boolean, default=False, index=True)
    is_working_context = db.Column(db.Boolean, default=False, index=True)
    is_completed = db.Column(db.Boolean, default=False, index=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    ended_at = db.Column(db.DateTime, nullable=True)

    # Relationships
    teams = db.relationship('Team', back_populates='game_night', lazy='dynamic', cascade='all, delete-orphan')
    games = db.relationship('Game', back_populates='game_night', lazy='dynamic', cascade='all, delete-orphan')

    @property
    def teams_count(self):
        """Get total number of teams in this game night."""
        # Use cached value if available (set by optimized query)
        if hasattr(self, '_cached_teams_count'):
            return self._cached_teams_count
        return self.teams.count()

    @property
    def total_games(self):
        """Get total number of games in this game night."""
        # Use cached value if available (set by optimized query)
        if hasattr(self, '_cached_total_games'):
            return self._cached_total_games
        return self.games.count()

    @property
    def completed_games(self):
        """Get number of completed games."""
        # Use cached value if available (set by optimized query)
        if hasattr(self, '_cached_completed_games'):
            return self._cached_completed_games
        return self.games.filter_by(isCompleted=True).count()

    def get_leaderboard(self):
        """
        Get sorted leaderboard for this game night.

        Optimized to avoid N+1 queries by eager loading teams with their scores and games.
        """
        from app.models.team import Team
        from app.models.score import Score

        # Eager load teams with their scores and the games for those scores
        # This prevents N+1 queries by loading everything in one query
        teams = db.session.query(Team).options(
            joinedload(Team.scores).joinedload(Score.game)
        ).filter(Team.game_night_id == self.id).all()

        # Calculate points in Python after loading all data
        team_points = []
        for team in teams:
            total_points = sum(
                score.points for score in team.scores
                if score.game and score.game.game_night_id == self.id
            )
            team_points.append((team, total_points))

        # Sort by points descending
        team_points.sort(key=lambda x: x[1], reverse=True)

        # Return just the teams in sorted order
        return [team for team, points in team_points]

    def get_winner(self):
        """Get the winning team (team with highest points) for this game night."""
        leaderboard = self.get_leaderboard()
        return leaderboard[0] if leaderboard else None

    def finalize(self):
        """Mark game night as completed and lock all edits."""
        self.is_completed = True
        self.is_active = False
        self.ended_at = datetime.utcnow()
        db.session.commit()

    def __repr__(self):
        return f'<GameNight {self.name} - {self.date}>'
