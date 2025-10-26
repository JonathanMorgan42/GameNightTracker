"""Unit tests for Round model."""
import pytest
from app.models import Round


@pytest.mark.unit
@pytest.mark.models
class TestRoundModel:
    """Test suite for Round model."""

    def test_create_round(self, db_session, game):
        """Test creating a round."""
        round_obj = Round(
            game_id=game.id,
            round_number=1,
            description='First Round'
        )

        db_session.add(round_obj)
        db_session.commit()

        assert round_obj.id is not None
        assert round_obj.game_id == game.id
        assert round_obj.round_number == 1
        assert round_obj.description == 'First Round'

    def test_round_without_description(self, db_session, game):
        """Test creating a round without description."""
        round_obj = Round(
            game_id=game.id,
            round_number=2
        )

        db_session.add(round_obj)
        db_session.commit()

        assert round_obj.id is not None
        assert round_obj.description is None

    def test_round_game_relationship(self, db_session, game):
        """Test relationship between round and game."""
        round_obj = Round(
            game_id=game.id,
            round_number=1,
            description='Test Round'
        )

        db_session.add(round_obj)
        db_session.commit()

        # Test forward relationship
        assert round_obj.game is not None
        assert round_obj.game.id == game.id
        assert round_obj.game.name == game.name

        # Test back relationship
        assert len(game.rounds.all()) > 0
        assert game.rounds.first().id == round_obj.id

    def test_multiple_rounds_for_game(self, db_session, game):
        """Test creating multiple rounds for a single game."""
        rounds = []
        for i in range(1, 4):
            round_obj = Round(
                game_id=game.id,
                round_number=i,
                description=f'Round {i}'
            )
            db_session.add(round_obj)
            rounds.append(round_obj)

        db_session.commit()

        # Verify all rounds created
        assert all(r.id is not None for r in rounds)

        # Verify game has all rounds
        game_rounds = game.rounds.order_by(Round.round_number).all()
        assert len(game_rounds) == 3
        assert [r.round_number for r in game_rounds] == [1, 2, 3]

    def test_round_name_property(self, db_session, game):
        """Test the name property of round."""
        # Round with description
        round1 = Round(
            game_id=game.id,
            round_number=1,
            description='Opening Round'
        )
        db_session.add(round1)

        # Round without description
        round2 = Round(
            game_id=game.id,
            round_number=2
        )
        db_session.add(round2)
        db_session.commit()

        assert round1.name == 'Round 1: Opening Round'
        assert round2.name == 'Round 2'

    def test_round_repr(self, db_session, game):
        """Test string representation of round."""
        round_obj = Round(
            game_id=game.id,
            round_number=1
        )
        db_session.add(round_obj)
        db_session.commit()

        repr_str = repr(round_obj)
        assert 'Round' in repr_str
        assert str(round_obj.round_number) in repr_str
        assert str(game.id) in repr_str

    def test_round_cascade_delete(self, db_session, game):
        """Test that deleting a game cascades to rounds."""
        round_obj = Round(
            game_id=game.id,
            round_number=1
        )
        db_session.add(round_obj)
        db_session.commit()

        round_id = round_obj.id

        # Delete the game
        db_session.delete(game)
        db_session.commit()

        # Verify round is also deleted
        assert Round.query.get(round_id) is None

    def test_round_index(self, db_session, game):
        """Test that composite index works for game_id and round_number."""
        # Create multiple rounds
        for i in range(1, 6):
            round_obj = Round(
                game_id=game.id,
                round_number=i
            )
            db_session.add(round_obj)

        db_session.commit()

        # Query using the indexed fields
        round_3 = Round.query.filter_by(
            game_id=game.id,
            round_number=3
        ).first()

        assert round_3 is not None
        assert round_3.round_number == 3
