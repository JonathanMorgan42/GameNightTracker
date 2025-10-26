"""Unit tests for Game model."""
import pytest
from app.models import Game, Score, Penalty


@pytest.mark.unit
@pytest.mark.models
class TestGameModel:
    """Test suite for Game model."""

    def test_create_game(self, db_session, game_night):
        """Test creating a game."""
        game = Game(
            name='Chess',
            type='board',
            game_night_id=game_night.id,
            point_scheme=2,
            metric_type='time',
            scoring_direction='lower_better'
        )

        db_session.add(game)
        db_session.commit()

        assert game.id is not None
        assert game.name == 'Chess'
        assert game.type == 'board'
        assert game.game_night_id == game_night.id
        assert game.point_scheme == 2
        assert game.metric_type == 'time'
        assert game.scoring_direction == 'lower_better'

    def test_default_values(self, db_session, game_night):
        """Test default values for game."""
        game = Game(
            name='Simple Game',
            game_night_id=game_night.id
        )

        db_session.add(game)
        db_session.commit()

        assert game.isCompleted is False
        assert game.sequence_number == 0
        assert game.point_scheme == 1
        assert game.metric_type == 'score'
        assert game.scoring_direction == 'lower_better'
        assert game.public_input is False

    def test_game_scores_relationship(self, db_session, game, teams):
        """Test relationship with scores."""
        # Add scores
        score1 = Score(game_id=game.id, team_id=teams[0].id, score_value=100, points=10)
        score2 = Score(game_id=game.id, team_id=teams[1].id, score_value=90, points=8)

        db_session.add_all([score1, score2])
        db_session.commit()
        db_session.refresh(game)

        assert game.scores.count() == 2
        assert score1 in game.scores.all()
        assert score2 in game.scores.all()

    def test_game_penalties_relationship(self, db_session, game, teams):
        """Test relationship with penalties."""
        penalty1 = Penalty(game_id=game.id, name='Late', value=5)
        penalty2 = Penalty(game_id=game.id, name='Foul', value=3)

        db_session.add_all([penalty1, penalty2])
        db_session.commit()
        db_session.refresh(game)

        assert game.penalties.count() == 2

    def test_game_night_relationship(self, db_session, game_night):
        """Test relationship with game night."""
        game = Game(name='Related Game', game_night_id=game_night.id)

        db_session.add(game)
        db_session.commit()

        assert game.game_night == game_night
        assert game in game_night.games.all()

    def test_name_required(self, db_session, game_night):
        """Test that name is required."""
        game = Game(game_night_id=game_night.id)

        db_session.add(game)

        with pytest.raises(Exception):  # Should raise IntegrityError
            db_session.commit()

    def test_cascade_delete_scores(self, db_session, game, teams):
        """Test that scores are deleted when game is deleted."""
        score = Score(game_id=game.id, team_id=teams[0].id, score_value=100, points=10)
        db_session.add(score)
        db_session.commit()

        score_id = score.id

        # Delete game
        db_session.delete(game)
        db_session.commit()

        # Score should be deleted
        assert db_session.query(Score).filter_by(id=score_id).first() is None

    def test_cascade_delete_penalties(self, db_session, game, teams):
        """Test that penalties are deleted when game is deleted."""
        penalty = Penalty(game_id=game.id, name='Test', value=5)
        db_session.add(penalty)
        db_session.commit()

        penalty_id = penalty.id

        # Delete game
        db_session.delete(game)
        db_session.commit()

        # Penalty should be deleted
        assert db_session.query(Penalty).filter_by(id=penalty_id).first() is None

    def test_sequence_number(self, db_session, game_night):
        """Test sequence_number for ordering games."""
        game1 = Game(name='First Game', game_night_id=game_night.id, sequence_number=1)
        game2 = Game(name='Second Game', game_night_id=game_night.id, sequence_number=2)
        game3 = Game(name='Third Game', game_night_id=game_night.id, sequence_number=3)

        db_session.add_all([game1, game2, game3])
        db_session.commit()

        # Query games ordered by sequence_number
        games = db_session.query(Game).filter_by(game_night_id=game_night.id).order_by(Game.sequence_number).all()

        assert games[0].name == 'First Game'
        assert games[1].name == 'Second Game'
        assert games[2].name == 'Third Game'

    def test_metric_types(self, db_session, game_night):
        """Test different metric types."""
        score_game = Game(name='Score Game', game_night_id=game_night.id, metric_type='score')
        time_game = Game(name='Time Game', game_night_id=game_night.id, metric_type='time')

        db_session.add_all([score_game, time_game])
        db_session.commit()

        assert score_game.metric_type == 'score'
        assert time_game.metric_type == 'time'

    def test_scoring_direction(self, db_session, game_night):
        """Test different scoring directions."""
        lower_better = Game(name='Golf', game_night_id=game_night.id, scoring_direction='lower_better')
        higher_better = Game(name='Basketball', game_night_id=game_night.id, scoring_direction='higher_better')

        db_session.add_all([lower_better, higher_better])
        db_session.commit()

        assert lower_better.scoring_direction == 'lower_better'
        assert higher_better.scoring_direction == 'higher_better'
