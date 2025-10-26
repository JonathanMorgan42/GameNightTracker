"""Unit tests for Team model."""
import pytest
from app.models import Team, Score, Participant


@pytest.mark.unit
@pytest.mark.models
class TestTeamModel:
    """Test suite for Team model."""

    def test_create_team(self, db_session, game_night):
        """Test creating a team."""
        team = Team(
            name='Test Team',
            color='#FF0000',
            game_night_id=game_night.id
        )

        db_session.add(team)
        db_session.commit()

        assert team.id is not None
        assert team.name == 'Test Team'
        assert team.color == '#FF0000'
        assert team.game_night_id == game_night.id

    def test_default_color(self, db_session, game_night):
        """Test default color is set."""
        team = Team(name='Blue Team', game_night_id=game_night.id)

        db_session.add(team)
        db_session.commit()

        assert team.color == '#3b82f6'  # Default blue color

    def test_total_points_no_scores(self, teams):
        """Test totalPoints when team has no scores."""
        team = teams[0]
        assert team.totalPoints == 0

    def test_total_points_with_scores(self, db_session, teams, game):
        """Test totalPoints calculation with multiple scores."""
        team = teams[0]

        # Add multiple scores
        score1 = Score(game_id=game.id, team_id=team.id, score_value=100, points=10)
        score2 = Score(game_id=game.id, team_id=team.id, score_value=90, points=8)
        score3 = Score(game_id=game.id, team_id=team.id, score_value=80, points=6)

        db_session.add_all([score1, score2, score3])
        db_session.commit()

        # Refresh to get updated relationships
        db_session.refresh(team)

        assert team.totalPoints == 24  # 10 + 8 + 6

    def test_games_played(self, db_session, teams, game):
        """Test games_played property."""
        team = teams[0]

        # Initially no games played
        assert team.games_played == 0

        # Add scores for 3 games
        for i in range(3):
            score = Score(game_id=game.id, team_id=team.id, score_value=100, points=10)
            db_session.add(score)

        db_session.commit()
        db_session.refresh(team)

        assert team.games_played == 3

    def test_team_game_night_relationship(self, db_session, game_night):
        """Test relationship with game night."""
        team = Team(name='Related Team', color='#00FF00', game_night_id=game_night.id)

        db_session.add(team)
        db_session.commit()

        assert team.game_night == game_night
        assert team in game_night.teams.all()

    def test_team_participants_relationship(self, teams, participants):
        """Test relationship with participants."""
        team = teams[0]

        team_participants = list(team.participants)
        assert len(team_participants) == 2  # From fixture
        assert all(p.team_id == team.id for p in team_participants)

    def test_name_required(self, db_session, game_night):
        """Test that name is required."""
        team = Team(color='#FF0000', game_night_id=game_night.id)

        db_session.add(team)

        with pytest.raises(Exception):  # Should raise IntegrityError
            db_session.commit()

    def test_repr(self, teams):
        """Test string representation."""
        team = teams[0]
        assert repr(team) == '<Team Team Alpha>'

    def test_cascade_delete_scores(self, db_session, teams, game):
        """Test that scores are deleted when team is deleted."""
        team = teams[0]

        # Add score
        score = Score(game_id=game.id, team_id=team.id, score_value=100, points=10)
        db_session.add(score)
        db_session.commit()

        score_id = score.id

        # Delete team
        db_session.delete(team)
        db_session.commit()

        # Score should be deleted
        assert db_session.query(Score).filter_by(id=score_id).first() is None
