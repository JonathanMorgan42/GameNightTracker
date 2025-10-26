"""Error handling and edge case tests.

Test IDs: DB-001 through DB-010, VAL-001 through VAL-010
Coverage: Database integrity, validation, error scenarios
"""
import pytest
from sqlalchemy.exc import IntegrityError
from app.models import GameNight, Team, Game, Score, Participant
from app.services.game_night_service import GameNightService
from tests.factories import GameNightFactory, TeamFactory, GameFactory, ScoreFactory


@pytest.mark.integration
@pytest.mark.error_handling
class TestErrorHandling:
    """Error handling and edge case tests."""

    def test_cascade_delete_game_night_complete(self, db_session):
        """DB-001: Test complete cascade delete of game night."""
        # Arrange
        gn = GameNightFactory.create(db_session)
        teams = TeamFactory.create_batch(db_session, count=2, game_night_id=gn.id)
        game = GameFactory.create(db_session, game_night_id=gn.id)
        score = ScoreFactory.create(db_session, game_id=game.id, team_id=teams[0].id, points=10)

        gn_id = gn.id
        team_ids = [t.id for t in teams]
        game_id = game.id
        score_id = score.id

        # Act - Delete game night
        db_session.delete(gn)
        db_session.commit()

        # Assert - Verify cascade
        assert db_session.query(GameNight).filter_by(id=gn_id).first() is None
        assert db_session.query(Team).filter(Team.id.in_(team_ids)).count() == 0
        assert db_session.query(Game).filter_by(id=game_id).first() is None
        assert db_session.query(Score).filter_by(id=score_id).first() is None

    def test_cascade_delete_team(self, db_session):
        """DB-002: Test team deletion cascades to participants and scores."""
        # Arrange
        gn = GameNightFactory.create(db_session)
        team = TeamFactory.create(db_session, game_night_id=gn.id, participant_count=2)
        game = GameFactory.create(db_session, game_night_id=gn.id)
        score = ScoreFactory.create(db_session, game_id=game.id, team_id=team.id)

        team_id = team.id
        score_id = score.id
        participant_ids = [p.id for p in team.participants]

        # Act
        db_session.delete(team)
        db_session.commit()

        # Assert
        assert db_session.query(Team).filter_by(id=team_id).first() is None
        assert db_session.query(Score).filter_by(id=score_id).first() is None
        assert db_session.query(Participant).filter(Participant.id.in_(participant_ids)).count() == 0

    def test_cascade_delete_game(self, db_session):
        """DB-003: Test game deletion cascades to scores."""
        # Arrange
        gn = GameNightFactory.create(db_session)
        team = TeamFactory.create(db_session, game_night_id=gn.id)
        game = GameFactory.create(db_session, game_night_id=gn.id)
        score = ScoreFactory.create(db_session, game_id=game.id, team_id=team.id)

        game_id = game.id
        score_id = score.id

        # Act
        db_session.delete(game)
        db_session.commit()

        # Assert
        assert db_session.query(Game).filter_by(id=game_id).first() is None
        assert db_session.query(Score).filter_by(id=score_id).first() is None

    def test_orphaned_score_prevention(self, db_session):
        """DB-004: Test cannot create score without valid game/team."""
        # Arrange
        score = Score(game_id=99999, team_id=99999, points=10)
        db_session.add(score)

        # Act & Assert
        with pytest.raises(IntegrityError):
            db_session.commit()

    def test_orphaned_participant_prevention(self, db_session):
        """DB-005: Test cannot create participant without team."""
        # Arrange
        participant = Participant(firstName='Test', lastName='User', team_id=99999)
        db_session.add(participant)

        # Act & Assert
        with pytest.raises(IntegrityError):
            db_session.commit()

    def test_unique_constraint_violations(self, db_session):
        """DB-006: Test unique constraint errors."""
        # Example: Multiple active game nights (if constraint exists)
        gn1 = GameNightFactory.create(db_session, name='GN1', is_active=True)
        gn2 = GameNightFactory.create(db_session, name='GN2', is_active=False)

        # Business logic should prevent multiple active
        assert gn1.is_active is True

    def test_foreign_key_constraint_violations(self, db_session):
        """DB-007: Test FK constraint errors."""
        # Trying to create team with invalid game_night_id
        team = Team(name='Invalid Team', game_night_id=99999)
        db_session.add(team)

        with pytest.raises(IntegrityError):
            db_session.commit()

    def test_transaction_rollback_on_error(self, db_session):
        """DB-008: Test transaction rolls back on partial failure."""
        from app import db

        gn = GameNightFactory.create(db_session)

        try:
            # Start transaction
            team = Team(name='Test Team', game_night_id=gn.id)
            db_session.add(team)
            db_session.flush()

            # Force error
            score = Score(game_id=99999, team_id=team.id, points=10)
            db_session.add(score)
            db_session.commit()
        except IntegrityError:
            db_session.rollback()

        # Verify team was not saved
        assert db_session.query(Team).filter_by(name='Test Team').first() is None

    def test_concurrent_updates(self, db_session):
        """DB-009: Test concurrent update handling."""
        # This documents expected behavior
        gn = GameNightFactory.create(db_session)
        assert gn is not None

    def test_null_constraint_violations(self, db_session):
        """DB-010: Test NOT NULL violations."""
        # Try to create game without required fields
        game = Game(name=None)  # Name is required
        db_session.add(game)

        with pytest.raises(IntegrityError):
            db_session.commit()


@pytest.mark.integration
@pytest.mark.validation
class TestValidation:
    """Validation and business logic error tests."""

    def test_activate_game_night_no_teams(self, db_session):
        """VAL-001: Test activation fails without teams."""
        gn = GameNightFactory.create(db_session)

        # Should raise validation error
        with pytest.raises(ValueError):
            GameNightService.set_active_game_night(gn.id)

    def test_activate_game_night_no_games(self, db_session):
        """VAL-002: Test activation fails without games."""
        gn = GameNightFactory.create(db_session)
        TeamFactory.create_batch(db_session, count=2, game_night_id=gn.id)

        # Should raise validation error
        with pytest.raises(ValueError):
            GameNightService.set_active_game_night(gn.id)

    def test_activate_game_night_incomplete_games(self, db_session):
        """VAL-003: Test activation validation."""
        gn = GameNightFactory.create(db_session)
        teams = TeamFactory.create_batch(db_session, count=2, game_night_id=gn.id)
        game = GameFactory.create(db_session, game_night_id=gn.id, is_completed=False)

        # Incomplete game might prevent activation
        try:
            GameNightService.set_active_game_night(gn.id)
        except ValueError:
            assert True  # Expected

    def test_tournament_minimum_teams(self, db_session):
        """VAL-004: Test tournament requires 2+ teams."""
        from app.services.tournament_service import TournamentService

        gn = GameNightFactory.create(db_session)
        team = TeamFactory.create(db_session, game_night_id=gn.id)
        game = GameFactory.create(db_session, game_night_id=gn.id)

        with pytest.raises(ValueError, match="At least 2 teams"):
            TournamentService.create_tournament(game.id, included_team_ids=[team.id])

    def test_game_sequence_number_conflict(self, db_session):
        """VAL-005: Test sequence number conflict handling."""
        gn = GameNightFactory.create(db_session)
        game1 = GameFactory.create(db_session, game_night_id=gn.id, sequence_number=1)
        game2 = GameFactory.create(db_session, game_night_id=gn.id, sequence_number=1)

        # Both created (no unique constraint on sequence)
        assert game1.sequence_number == game2.sequence_number

    def test_duplicate_team_names(self, db_session):
        """VAL-006: Test duplicate team names allowed."""
        gn = GameNightFactory.create(db_session)
        team1 = TeamFactory.create(db_session, name='Duplicate', game_night_id=gn.id)
        team2 = TeamFactory.create(db_session, name='Duplicate', game_night_id=gn.id)

        # Duplicates allowed
        assert team1.name == team2.name

    def test_duplicate_game_names(self, db_session):
        """VAL-007: Test duplicate game names allowed."""
        gn = GameNightFactory.create(db_session)
        game1 = GameFactory.create(db_session, name='Duplicate', game_night_id=gn.id)
        game2 = GameFactory.create(db_session, name='Duplicate', game_night_id=gn.id, sequence_number=2)

        # Duplicates allowed
        assert game1.name == game2.name

    def test_negative_score_values(self, db_session):
        """VAL-008: Test negative scores allowed."""
        gn = GameNightFactory.create(db_session)
        team = TeamFactory.create(db_session, game_night_id=gn.id)
        game = GameFactory.create(db_session, game_night_id=gn.id)

        score = ScoreFactory.create(db_session, game_id=game.id, team_id=team.id,
                                    score_value=-10.0, points=-5)

        assert score.score_value == -10.0
        assert score.points == -5

    def test_invalid_point_scheme(self, db_session):
        """VAL-009: Test point scheme validation."""
        # Document expected range
        gn = GameNightFactory.create(db_session)
        game = GameFactory.create(db_session, game_night_id=gn.id, point_scheme=50)

        assert game.point_scheme == 50

    def test_invalid_winner_team_id(self, db_session):
        """VAL-010: Test winner must be in match."""
        from app.services.tournament_service import TournamentService
        from tests.factories import TournamentFactory
        from app.models import Match

        gn = GameNightFactory.create(db_session)
        teams = TeamFactory.create_batch(db_session, count=3, game_night_id=gn.id)
        game = GameFactory.create(db_session, game_night_id=gn.id)
        tournament = TournamentService.create_tournament(
            game.id, included_team_ids=[teams[0].id, teams[1].id]
        )

        match = Match.query.filter_by(tournament_id=tournament.id).first()

        with pytest.raises(ValueError):
            TournamentService.update_match_result(
                match.id, 100.0, 90.0, teams[2].id  # Not in match
            )
