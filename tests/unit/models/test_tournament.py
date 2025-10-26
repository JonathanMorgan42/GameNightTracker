"""Unit tests for Tournament model.

Test IDs: TOURN-M-001 through TOURN-M-011
Coverage: Tournament model creation, relationships, state transitions, constraints
"""
import pytest
from sqlalchemy.exc import IntegrityError
from app.models import Tournament, Game, Team, Match
from tests.factories import GameFactory, GameNightFactory, TeamFactory


@pytest.mark.unit
@pytest.mark.models
class TestTournamentModel:
    """Test suite for Tournament model."""

    def test_tournament_creation(self, db_session):
        """TOURN-M-001: Test creating a tournament with basic settings."""
        # Arrange
        game_night = GameNightFactory.create(db_session)
        game = GameFactory.create(db_session, game_night_id=game_night.id)

        # Act
        tournament = Tournament(
            game_id=game.id,
            pairing_type='random',
            bracket_style='standard',
            public_edit=False
        )
        db_session.add(tournament)
        db_session.commit()

        # Assert
        assert tournament.id is not None
        assert tournament.game_id == game.id
        assert tournament.pairing_type == 'random'
        assert tournament.bracket_style == 'standard'
        assert tournament.public_edit is False
        assert tournament.is_started is False
        assert tournament.is_completed is False
        assert tournament.winner_team_id is None

    def test_tournament_pairing_types(self, db_session):
        """TOURN-M-002: Test random vs manual pairing types."""
        # Arrange
        game_night = GameNightFactory.create(db_session)
        game1 = GameFactory.create(db_session, name='Game 1', game_night_id=game_night.id)
        game2 = GameFactory.create(db_session, name='Game 2', game_night_id=game_night.id, sequence_number=2)

        # Act
        tournament_random = Tournament(game_id=game1.id, pairing_type='random')
        tournament_manual = Tournament(game_id=game2.id, pairing_type='manual')
        db_session.add_all([tournament_random, tournament_manual])
        db_session.commit()

        # Assert
        assert tournament_random.pairing_type == 'random'
        assert tournament_manual.pairing_type == 'manual'

    def test_tournament_bracket_styles(self, db_session):
        """TOURN-M-003: Test standard vs play_in bracket styles."""
        # Arrange
        game_night = GameNightFactory.create(db_session)
        game1 = GameFactory.create(db_session, name='Game 1', game_night_id=game_night.id)
        game2 = GameFactory.create(db_session, name='Game 2', game_night_id=game_night.id, sequence_number=2)

        # Act
        tournament_standard = Tournament(game_id=game1.id, bracket_style='standard')
        tournament_play_in = Tournament(game_id=game2.id, bracket_style='play_in')
        db_session.add_all([tournament_standard, tournament_play_in])
        db_session.commit()

        # Assert
        assert tournament_standard.bracket_style == 'standard'
        assert tournament_play_in.bracket_style == 'play_in'

    def test_tournament_public_edit_flag(self, db_session):
        """TOURN-M-004: Test public_edit boolean flag."""
        # Arrange
        game_night = GameNightFactory.create(db_session)
        game1 = GameFactory.create(db_session, name='Game 1', game_night_id=game_night.id)
        game2 = GameFactory.create(db_session, name='Game 2', game_night_id=game_night.id, sequence_number=2)

        # Act
        tournament_public = Tournament(game_id=game1.id, public_edit=True)
        tournament_private = Tournament(game_id=game2.id, public_edit=False)
        db_session.add_all([tournament_public, tournament_private])
        db_session.commit()

        # Assert
        assert tournament_public.public_edit is True
        assert tournament_private.public_edit is False

    def test_tournament_game_relationship(self, db_session):
        """TOURN-M-005: Test one-to-one relationship with Game."""
        # Arrange
        game_night = GameNightFactory.create(db_session)
        game = GameFactory.create(db_session, game_night_id=game_night.id)

        # Act
        tournament = Tournament(game_id=game.id)
        db_session.add(tournament)
        db_session.commit()

        # Assert
        assert tournament.game is not None
        assert tournament.game.id == game.id
        assert tournament.game.name == game.name
        assert game.tournament is not None
        assert game.tournament.id == tournament.id

    def test_tournament_matches_relationship(self, db_session):
        """TOURN-M-006: Test one-to-many relationship with Match."""
        # Arrange
        game_night = GameNightFactory.create(db_session)
        game = GameFactory.create(db_session, game_night_id=game_night.id)
        tournament = Tournament(game_id=game.id)
        db_session.add(tournament)
        db_session.commit()

        # Act - Add matches
        match1 = Match(tournament_id=tournament.id, round_number=1, position_in_round=0)
        match2 = Match(tournament_id=tournament.id, round_number=1, position_in_round=1)
        match3 = Match(tournament_id=tournament.id, round_number=2, position_in_round=0)
        db_session.add_all([match1, match2, match3])
        db_session.commit()

        # Assert
        assert tournament.matches.count() == 3
        matches = tournament.matches.all()
        assert len(matches) == 3
        assert all(m.tournament_id == tournament.id for m in matches)

    def test_tournament_state_transitions(self, db_session):
        """TOURN-M-007: Test is_started and is_completed state transitions."""
        # Arrange
        game_night = GameNightFactory.create(db_session)
        game = GameFactory.create(db_session, game_night_id=game_night.id)
        tournament = Tournament(game_id=game.id)
        db_session.add(tournament)
        db_session.commit()

        # Act & Assert - Initial state
        assert tournament.is_started is False
        assert tournament.is_completed is False

        # Start tournament
        tournament.is_started = True
        db_session.commit()
        assert tournament.is_started is True
        assert tournament.is_completed is False

        # Complete tournament
        tournament.is_completed = True
        db_session.commit()
        assert tournament.is_started is True
        assert tournament.is_completed is True

    def test_tournament_winner_team_relationship(self, db_session):
        """TOURN-M-008: Test winner_team_id relationship."""
        # Arrange
        game_night = GameNightFactory.create(db_session)
        game = GameFactory.create(db_session, game_night_id=game_night.id)
        teams = TeamFactory.create_batch(db_session, count=3, game_night_id=game_night.id)

        # Act
        tournament = Tournament(game_id=game.id, winner_team_id=teams[0].id)
        db_session.add(tournament)
        db_session.commit()

        # Assert
        assert tournament.winner_team is not None
        assert tournament.winner_team.id == teams[0].id
        assert tournament.winner_team.name == teams[0].name

    def test_tournament_play_in_match_relationship(self, db_session):
        """TOURN-M-009: Test play_in_match relationship."""
        # Arrange
        game_night = GameNightFactory.create(db_session)
        game = GameFactory.create(db_session, game_night_id=game_night.id)
        tournament = Tournament(game_id=game.id, bracket_style='play_in')
        db_session.add(tournament)
        db_session.commit()

        # Create a play-in match
        play_in_match = Match(
            tournament_id=tournament.id,
            round_number=0,
            position_in_round=0,
            is_play_in=True
        )
        db_session.add(play_in_match)
        db_session.commit()

        # Act
        tournament.play_in_match_id = play_in_match.id
        db_session.commit()

        # Assert
        assert tournament.play_in_match is not None
        assert tournament.play_in_match.id == play_in_match.id
        assert tournament.play_in_match.is_play_in is True

    def test_tournament_cascade_delete_matches(self, db_session):
        """TOURN-M-010: Test that deleting tournament deletes matches."""
        # Arrange
        game_night = GameNightFactory.create(db_session)
        game = GameFactory.create(db_session, game_night_id=game_night.id)
        tournament = Tournament(game_id=game.id)
        db_session.add(tournament)
        db_session.commit()

        # Create matches
        match1 = Match(tournament_id=tournament.id, round_number=1, position_in_round=0)
        match2 = Match(tournament_id=tournament.id, round_number=1, position_in_round=1)
        db_session.add_all([match1, match2])
        db_session.commit()

        match1_id = match1.id
        match2_id = match2.id

        # Act - Delete tournament
        db_session.delete(tournament)
        db_session.commit()

        # Assert - Matches should be deleted
        assert db_session.query(Match).filter_by(id=match1_id).first() is None
        assert db_session.query(Match).filter_by(id=match2_id).first() is None

    def test_tournament_unique_per_game_constraint(self, db_session):
        """TOURN-M-011: Test that only one tournament per game is allowed."""
        # Arrange
        game_night = GameNightFactory.create(db_session)
        game = GameFactory.create(db_session, game_night_id=game_night.id)

        # Create first tournament
        tournament1 = Tournament(game_id=game.id, pairing_type='random')
        db_session.add(tournament1)
        db_session.commit()

        # Act & Assert - Try to create second tournament for same game
        tournament2 = Tournament(game_id=game.id, pairing_type='manual')
        db_session.add(tournament2)

        with pytest.raises(IntegrityError):
            db_session.commit()
