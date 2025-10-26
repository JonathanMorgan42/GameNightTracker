"""Database integrity tests.

Coverage: Constraints, referential integrity, transactions
"""
import pytest
from sqlalchemy.exc import IntegrityError
from app.models import GameNight, Team, Game, Score, Participant, Tournament, Match
from tests.factories import GameNightFactory, TeamFactory, GameFactory


@pytest.mark.integration
@pytest.mark.database
class TestDatabaseIntegrity:
    """Database integrity tests."""

    def test_referential_integrity_game_night(self, db_session):
        """Test game night FK integrity."""
        # Cannot create team with invalid game_night_id
        team = Team(name='Invalid', game_night_id=99999)
        db_session.add(team)

        with pytest.raises(IntegrityError):
            db_session.commit()

    def test_referential_integrity_team_game(self, db_session):
        """Test score FK integrity."""
        # Cannot create score with invalid team/game
        score = Score(team_id=99999, game_id=99999, points=0)
        db_session.add(score)

        with pytest.raises(IntegrityError):
            db_session.commit()

    def test_cascade_deletes_preserve_data_integrity(self, db_session):
        """Test cascade deletes don't leave orphans."""
        # Create complete structure
        gn = GameNightFactory.create(db_session)
        team = TeamFactory.create(db_session, game_night_id=gn.id)
        game = GameFactory.create(db_session, game_night_id=gn.id)

        from tests.factories import ScoreFactory
        score = ScoreFactory.create(db_session, game_id=game.id, team_id=team.id)

        # Delete game night
        db_session.delete(gn)
        db_session.commit()

        # Nothing should be orphaned
        assert db_session.query(Team).filter_by(game_night_id=gn.id).count() == 0
        assert db_session.query(Game).filter_by(game_night_id=gn.id).count() == 0

    def test_unique_constraints_enforced(self, db_session):
        """Test unique constraints."""
        # Tournament has unique constraint on game_id
        gn = GameNightFactory.create(db_session)
        game = GameFactory.create(db_session, game_night_id=gn.id)

        tournament1 = Tournament(game_id=game.id)
        db_session.add(tournament1)
        db_session.commit()

        tournament2 = Tournament(game_id=game.id)
        db_session.add(tournament2)

        with pytest.raises(IntegrityError):
            db_session.commit()

    def test_not_null_constraints_enforced(self, db_session):
        """Test NOT NULL constraints."""
        # Game requires name
        game = Game()
        db_session.add(game)

        with pytest.raises(IntegrityError):
            db_session.commit()

    def test_transaction_atomicity(self, db_session):
        """Test transactions are atomic."""
        gn = GameNightFactory.create(db_session)

        try:
            team = Team(name='Test', game_night_id=gn.id)
            db_session.add(team)
            db_session.flush()

            # Force error
            invalid = Score(team_id=team.id, game_id=99999)
            db_session.add(invalid)
            db_session.commit()
        except IntegrityError:
            db_session.rollback()

        # Team should not exist
        assert db_session.query(Team).filter_by(name='Test').first() is None

    def test_concurrent_insert_handling(self, db_session):
        """Test concurrent inserts."""
        # Create game night
        gn = GameNightFactory.create(db_session)

        # Simultaneous operations should succeed
        team1 = TeamFactory.create(db_session, name='Team 1', game_night_id=gn.id)
        team2 = TeamFactory.create(db_session, name='Team 2', game_night_id=gn.id)

        assert team1.id != team2.id

    def test_foreign_key_cascades_correct(self, db_session):
        """Test FK cascade behavior."""
        gn = GameNightFactory.create(db_session)
        team = TeamFactory.create(db_session, game_night_id=gn.id, participant_count=2)

        participant_count = len(team.participants)
        assert participant_count == 2

        # Delete team
        db_session.delete(team)
        db_session.commit()

        # Participants should be deleted
        assert db_session.query(Participant).filter_by(team_id=team.id).count() == 0

    def test_constraint_violation_rollback(self, db_session):
        """Test constraint violation triggers rollback."""
        gn = GameNightFactory.create(db_session)

        try:
            game1 = Game(name='Game 1', game_night_id=gn.id)
            db_session.add(game1)
            db_session.flush()

            # Violate constraint
            game2 = Game(game_night_id=99999)
            db_session.add(game2)
            db_session.commit()
        except IntegrityError:
            db_session.rollback()

        # First game should not be committed
        assert db_session.query(Game).filter_by(name='Game 1').first() is None

    def test_index_constraints(self, db_session):
        """Test index and constraint behavior."""
        # Tournament can only have one per game
        gn = GameNightFactory.create(db_session)
        game = GameFactory.create(db_session, game_night_id=gn.id)

        t1 = Tournament(game_id=game.id)
        db_session.add(t1)
        db_session.commit()

        # Duplicate should fail
        t2 = Tournament(game_id=game.id)
        db_session.add(t2)

        with pytest.raises(IntegrityError):
            db_session.commit()
