"""Unit tests for GameNight model."""
import pytest
from datetime import date, datetime
from app.models import GameNight, Team, Game


@pytest.mark.unit
@pytest.mark.models
class TestGameNightModel:
    """Test suite for GameNight model."""

    def test_create_game_night(self, db_session):
        """Test creating a game night."""
        gn = GameNight(
            name='Friday Night Games',
            date=date(2024, 1, 15),
            is_active=True
        )

        db_session.add(gn)
        db_session.commit()

        assert gn.id is not None
        assert gn.name == 'Friday Night Games'
        assert gn.date == date(2024, 1, 15)
        assert gn.is_active is True
        assert gn.is_completed is False
        assert gn.created_at is not None

    def test_default_values(self, db_session):
        """Test default values for game night."""
        gn = GameNight(
            name='Test Night',
            date=date.today()
        )

        db_session.add(gn)
        db_session.commit()

        assert gn.is_active is False
        assert gn.is_completed is False
        assert gn.ended_at is None
        assert gn.created_at is not None

    def test_total_games_property(self, db_session, game_night):
        """Test total_games property."""
        assert game_night.total_games == 0

        # Add games
        game1 = Game(name='Game 1', game_night_id=game_night.id)
        game2 = Game(name='Game 2', game_night_id=game_night.id)

        db_session.add_all([game1, game2])
        db_session.commit()
        db_session.refresh(game_night)

        assert game_night.total_games == 2

    def test_completed_games_property(self, db_session, game_night):
        """Test completed_games property."""
        # Add games
        game1 = Game(name='Completed Game', game_night_id=game_night.id, isCompleted=True)
        game2 = Game(name='Incomplete Game', game_night_id=game_night.id, isCompleted=False)
        game3 = Game(name='Another Completed', game_night_id=game_night.id, isCompleted=True)

        db_session.add_all([game1, game2, game3])
        db_session.commit()
        db_session.refresh(game_night)

        assert game_night.total_games == 3
        assert game_night.completed_games == 2

    def test_get_leaderboard_no_teams(self, game_night):
        """Test get_leaderboard with no teams."""
        leaderboard = game_night.get_leaderboard()
        assert leaderboard == []

    def test_get_leaderboard_sorted(self, db_session, game_night, game):
        """Test get_leaderboard returns teams sorted by points."""
        # Create teams with different scores
        team1 = Team(name='Low Score', color='#FF0000', game_night_id=game_night.id)
        team2 = Team(name='High Score', color='#00FF00', game_night_id=game_night.id)
        team3 = Team(name='Mid Score', color='#0000FF', game_night_id=game_night.id)

        db_session.add_all([team1, team2, team3])
        db_session.commit()

        # Add scores
        from app.models import Score
        score1 = Score(game_id=game.id, team_id=team1.id, score_value=50, points=5)
        score2 = Score(game_id=game.id, team_id=team2.id, score_value=100, points=15)
        score3 = Score(game_id=game.id, team_id=team3.id, score_value=75, points=10)

        db_session.add_all([score1, score2, score3])
        db_session.commit()
        db_session.refresh(game_night)

        leaderboard = game_night.get_leaderboard()

        assert len(leaderboard) == 3
        assert leaderboard[0].name == 'High Score'
        assert leaderboard[1].name == 'Mid Score'
        assert leaderboard[2].name == 'Low Score'

    def test_get_winner(self, db_session, game_night, game):
        """Test get_winner returns team with highest points."""
        team1 = Team(name='Winner', color='#FF0000', game_night_id=game_night.id)
        team2 = Team(name='Runner Up', color='#00FF00', game_night_id=game_night.id)

        db_session.add_all([team1, team2])
        db_session.commit()

        from app.models import Score
        score1 = Score(game_id=game.id, team_id=team1.id, score_value=100, points=20)
        score2 = Score(game_id=game.id, team_id=team2.id, score_value=90, points=10)

        db_session.add_all([score1, score2])
        db_session.commit()
        db_session.refresh(game_night)

        winner = game_night.get_winner()
        assert winner.name == 'Winner'

    def test_get_winner_no_teams(self, game_night):
        """Test get_winner with no teams."""
        winner = game_night.get_winner()
        assert winner is None

    def test_finalize(self, db_session, game_night):
        """Test finalize method."""
        game_night.is_active = True
        db_session.commit()

        game_night.finalize()
        db_session.refresh(game_night)

        assert game_night.is_completed is True
        assert game_night.is_active is False
        assert game_night.ended_at is not None
        assert isinstance(game_night.ended_at, datetime)

    def test_cascade_delete_teams(self, db_session, game_night):
        """Test that teams are deleted when game night is deleted."""
        team = Team(name='Temp Team', color='#FFFFFF', game_night_id=game_night.id)
        db_session.add(team)
        db_session.commit()

        team_id = team.id
        game_night_id = game_night.id

        # Delete game night
        db_session.delete(game_night)
        db_session.commit()

        # Team should be deleted
        assert db_session.query(Team).filter_by(id=team_id).first() is None

    def test_cascade_delete_games(self, db_session, game_night):
        """Test that games are deleted when game night is deleted."""
        game = Game(name='Temp Game', game_night_id=game_night.id)
        db_session.add(game)
        db_session.commit()

        game_id = game.id

        # Delete game night
        db_session.delete(game_night)
        db_session.commit()

        # Game should be deleted
        assert db_session.query(Game).filter_by(id=game_id).first() is None

    def test_repr(self, game_night):
        """Test string representation."""
        expected = f'<GameNight {game_night.name} - {game_night.date}>'
        assert repr(game_night) == expected

    def test_name_required(self, db_session):
        """Test that name is required."""
        gn = GameNight(date=date.today())

        db_session.add(gn)

        with pytest.raises(Exception):  # Should raise IntegrityError
            db_session.commit()

    def test_date_required(self, db_session):
        """Test that date is required."""
        gn = GameNight(name='Test Night')

        db_session.add(gn)

        with pytest.raises(Exception):  # Should raise IntegrityError
            db_session.commit()
