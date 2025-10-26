"""Unit tests for Penalty model.

Test IDs: PEN-M-001 through PEN-M-010
Coverage: Penalty model creation, unit property, stackable flag, relationships
"""
import pytest
from app.models import Penalty, Game
from tests.factories import GameFactory, GameNightFactory, PenaltyFactory


@pytest.mark.unit
@pytest.mark.models
class TestPenaltyModel:
    """Test suite for Penalty model."""

    def test_penalty_creation(self, db_session):
        """PEN-M-001: Test creating penalty with all fields."""
        # Arrange
        game_night = GameNightFactory.create(db_session)
        game = GameFactory.create(db_session, game_night_id=game_night.id)

        # Act
        penalty = Penalty(
            game_id=game.id,
            name='Late Arrival',
            value=5,
            stackable=True
        )
        db_session.add(penalty)
        db_session.commit()

        # Assert
        assert penalty.id is not None
        assert penalty.game_id == game.id
        assert penalty.name == 'Late Arrival'
        assert penalty.value == 5
        assert penalty.stackable is True

    def test_penalty_unit_property_score(self, db_session):
        """PEN-M-002: Test unit='points' for score games."""
        # Arrange
        game_night = GameNightFactory.create(db_session)
        game = GameFactory.create(
            db_session,
            game_night_id=game_night.id,
            metric_type='score'
        )

        # Act
        penalty = PenaltyFactory.create(
            db_session,
            game_id=game.id,
            name='Point Penalty',
            value=10
        )

        # Assert
        assert penalty.unit == 'points'

    def test_penalty_unit_property_time(self, db_session):
        """PEN-M-003: Test unit='seconds' for time games."""
        # Arrange
        game_night = GameNightFactory.create(db_session)
        game = GameFactory.create(
            db_session,
            game_night_id=game_night.id,
            metric_type='time'
        )

        # Act
        penalty = PenaltyFactory.create(
            db_session,
            game_id=game.id,
            name='Time Penalty',
            value=30
        )

        # Assert
        assert penalty.unit == 'seconds'

    def test_penalty_stackable_true(self, db_session):
        """PEN-M-004: Test stackable penalty can be applied multiple times."""
        # Arrange
        game_night = GameNightFactory.create(db_session)
        game = GameFactory.create(db_session, game_night_id=game_night.id)

        # Act
        penalty = Penalty(
            game_id=game.id,
            name='Multiple Infractions',
            value=3,
            stackable=True
        )
        db_session.add(penalty)
        db_session.commit()

        # Assert
        assert penalty.stackable is True

    def test_penalty_stackable_false(self, db_session):
        """PEN-M-005: Test non-stackable penalty."""
        # Arrange
        game_night = GameNightFactory.create(db_session)
        game = GameFactory.create(db_session, game_night_id=game_night.id)

        # Act
        penalty = Penalty(
            game_id=game.id,
            name='One-time Penalty',
            value=10,
            stackable=False
        )
        db_session.add(penalty)
        db_session.commit()

        # Assert
        assert penalty.stackable is False

    def test_penalty_game_relationship(self, db_session):
        """PEN-M-006: Test penalty belongs to game."""
        # Arrange
        game_night = GameNightFactory.create(db_session)
        game = GameFactory.create(db_session, game_night_id=game_night.id)

        # Act
        penalty = PenaltyFactory.create(
            db_session,
            game_id=game.id,
            name='Test Penalty'
        )

        # Assert
        assert penalty.game is not None
        assert penalty.game.id == game.id
        assert penalty.game.name == game.name

    def test_penalty_cascade_delete(self, db_session):
        """PEN-M-007: Test penalty deleted when game deleted."""
        # Arrange
        game_night = GameNightFactory.create(db_session)
        game = GameFactory.create(db_session, game_night_id=game_night.id)

        penalty = PenaltyFactory.create(
            db_session,
            game_id=game.id,
            name='Test Penalty'
        )
        penalty_id = penalty.id

        # Act - Delete game
        db_session.delete(game)
        db_session.commit()

        # Assert - Penalty should be deleted
        assert db_session.query(Penalty).filter_by(id=penalty_id).first() is None

    def test_penalty_negative_value(self, db_session):
        """PEN-M-008: Test negative penalty values (bonuses)."""
        # Arrange
        game_night = GameNightFactory.create(db_session)
        game = GameFactory.create(db_session, game_night_id=game_night.id)

        # Act
        penalty = Penalty(
            game_id=game.id,
            name='Bonus Points',
            value=-10,  # Negative value
            stackable=False
        )
        db_session.add(penalty)
        db_session.commit()

        # Assert
        assert penalty.value == -10

    def test_penalty_zero_value(self, db_session):
        """PEN-M-009: Test zero value penalty (edge case)."""
        # Arrange
        game_night = GameNightFactory.create(db_session)
        game = GameFactory.create(db_session, game_night_id=game_night.id)

        # Act
        penalty = Penalty(
            game_id=game.id,
            name='Warning Only',
            value=0,
            stackable=False
        )
        db_session.add(penalty)
        db_session.commit()

        # Assert
        assert penalty.value == 0

    def test_penalty_large_value(self, db_session):
        """PEN-M-010: Test large penalty values."""
        # Arrange
        game_night = GameNightFactory.create(db_session)
        game = GameFactory.create(db_session, game_night_id=game_night.id)

        # Act
        penalty = Penalty(
            game_id=game.id,
            name='Major Violation',
            value=1000,
            stackable=False
        )
        db_session.add(penalty)
        db_session.commit()

        # Assert
        assert penalty.value == 1000
