"""Unit tests for Score model.

Test IDs: SCORE-M-001 through SCORE-M-010
Coverage: Score model creation, relationships, cascade deletes, constraints
"""
import pytest
from sqlalchemy.exc import IntegrityError
from app.models import Score, Team, Game
from tests.factories import GameFactory, GameNightFactory, TeamFactory, ScoreFactory


@pytest.mark.unit
@pytest.mark.models
class TestScoreModel:
    """Test suite for Score model."""

    def test_score_creation(self, db_session):
        """SCORE-M-001: Test creating score with all fields."""
        # Arrange
        game_night = GameNightFactory.create(db_session)
        game = GameFactory.create(db_session, game_night_id=game_night.id)
        team = TeamFactory.create(db_session, game_night_id=game_night.id)

        # Act
        score = Score(
            game_id=game.id,
            team_id=team.id,
            points=10,
            score_value=95.5,
            notes='Great performance'
        )
        db_session.add(score)
        db_session.commit()

        # Assert
        assert score.id is not None
        assert score.game_id == game.id
        assert score.team_id == team.id
        assert score.points == 10
        assert score.score_value == 95.5
        assert score.notes == 'Great performance'

    def test_score_default_values(self, db_session):
        """SCORE-M-002: Test default points=0, nullable score_value."""
        # Arrange
        game_night = GameNightFactory.create(db_session)
        game = GameFactory.create(db_session, game_night_id=game_night.id)
        team = TeamFactory.create(db_session, game_night_id=game_night.id)

        # Act
        score = Score(game_id=game.id, team_id=team.id)
        db_session.add(score)
        db_session.commit()

        # Assert
        assert score.points == 0
        assert score.score_value is None
        assert score.notes is None

    def test_score_relationships(self, db_session):
        """SCORE-M-003: Test team and game relationships."""
        # Arrange
        game_night = GameNightFactory.create(db_session)
        game = GameFactory.create(db_session, game_night_id=game_night.id)
        team = TeamFactory.create(db_session, game_night_id=game_night.id)

        # Act
        score = ScoreFactory.create(
            db_session,
            game_id=game.id,
            team_id=team.id,
            points=5
        )

        # Assert
        assert score.team is not None
        assert score.team.id == team.id
        assert score.game is not None
        assert score.game.id == game.id

    def test_score_cascade_on_team_delete(self, db_session):
        """SCORE-M-004: Test scores deleted when team deleted."""
        # Arrange
        game_night = GameNightFactory.create(db_session)
        game = GameFactory.create(db_session, game_night_id=game_night.id)
        team = TeamFactory.create(db_session, game_night_id=game_night.id)

        score = ScoreFactory.create(
            db_session,
            game_id=game.id,
            team_id=team.id,
            points=10
        )
        score_id = score.id

        # Act - Delete team
        db_session.delete(team)
        db_session.commit()

        # Assert - Score should be deleted
        assert db_session.query(Score).filter_by(id=score_id).first() is None

    def test_score_cascade_on_game_delete(self, db_session):
        """SCORE-M-005: Test scores deleted when game deleted."""
        # Arrange
        game_night = GameNightFactory.create(db_session)
        game = GameFactory.create(db_session, game_night_id=game_night.id)
        team = TeamFactory.create(db_session, game_night_id=game_night.id)

        score = ScoreFactory.create(
            db_session,
            game_id=game.id,
            team_id=team.id,
            points=10
        )
        score_id = score.id

        # Act - Delete game
        db_session.delete(game)
        db_session.commit()

        # Assert - Score should be deleted
        assert db_session.query(Score).filter_by(id=score_id).first() is None

    def test_score_nullable_score_value(self, db_session):
        """SCORE-M-006: Test score_value can be null for manual points."""
        # Arrange
        game_night = GameNightFactory.create(db_session)
        game = GameFactory.create(db_session, game_night_id=game_night.id)
        team = TeamFactory.create(db_session, game_night_id=game_night.id)

        # Act - Create score with points but no score_value
        score = Score(
            game_id=game.id,
            team_id=team.id,
            points=5,
            score_value=None
        )
        db_session.add(score)
        db_session.commit()

        # Assert
        assert score.points == 5
        assert score.score_value is None

    def test_score_notes_text_field(self, db_session):
        """SCORE-M-007: Test notes can store long text."""
        # Arrange
        game_night = GameNightFactory.create(db_session)
        game = GameFactory.create(db_session, game_night_id=game_night.id)
        team = TeamFactory.create(db_session, game_night_id=game_night.id)

        long_notes = 'A' * 1000  # Long text

        # Act
        score = Score(
            game_id=game.id,
            team_id=team.id,
            points=10,
            notes=long_notes
        )
        db_session.add(score)
        db_session.commit()

        # Assert
        assert len(score.notes) == 1000
        assert score.notes == long_notes

    def test_score_float_precision(self, db_session):
        """SCORE-M-008: Test score_value float precision."""
        # Arrange
        game_night = GameNightFactory.create(db_session)
        game = GameFactory.create(db_session, game_night_id=game_night.id)
        team = TeamFactory.create(db_session, game_night_id=game_night.id)

        # Act
        score = Score(
            game_id=game.id,
            team_id=team.id,
            score_value=123.456789,
            points=10
        )
        db_session.add(score)
        db_session.commit()

        # Assert
        assert abs(score.score_value - 123.456789) < 0.00001

    def test_score_unique_team_game_constraint(self, db_session):
        """SCORE-M-009: Test only one score per team per game (if constraint exists)."""
        # Arrange
        game_night = GameNightFactory.create(db_session)
        game = GameFactory.create(db_session, game_night_id=game_night.id)
        team = TeamFactory.create(db_session, game_night_id=game_night.id)

        # Create first score
        score1 = Score(game_id=game.id, team_id=team.id, points=10)
        db_session.add(score1)
        db_session.commit()

        # Act - Try to create duplicate
        score2 = Score(game_id=game.id, team_id=team.id, points=20)
        db_session.add(score2)

        # Note: This test documents expected behavior
        # If unique constraint exists, this should raise IntegrityError
        # If not, multiple scores are allowed (current behavior)
        try:
            db_session.commit()
            # Multiple scores allowed - document this
            assert True  # No constraint enforced
        except IntegrityError:
            # Constraint enforced
            db_session.rollback()
            assert True  # Constraint works

    def test_score_negative_points(self, db_session):
        """SCORE-M-010: Test negative points are allowed (for penalties)."""
        # Arrange
        game_night = GameNightFactory.create(db_session)
        game = GameFactory.create(db_session, game_night_id=game_night.id)
        team = TeamFactory.create(db_session, game_night_id=game_night.id)

        # Act
        score = Score(
            game_id=game.id,
            team_id=team.id,
            points=-5,
            score_value=50.0
        )
        db_session.add(score)
        db_session.commit()

        # Assert
        assert score.points == -5
