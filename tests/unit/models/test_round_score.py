"""Unit tests for RoundScore model."""
import pytest
from app.models import Round, RoundScore


@pytest.mark.unit
@pytest.mark.models
class TestRoundScoreModel:
    """Test suite for RoundScore model."""

    def test_create_round_score(self, db_session, game, teams):
        """Test creating a round score."""
        # Create a round first
        round_obj = Round(
            game_id=game.id,
            round_number=1
        )
        db_session.add(round_obj)
        db_session.commit()

        # Create round score
        round_score = RoundScore(
            round_id=round_obj.id,
            team_id=teams[0].id,
            score_value=42.5,
            points=10,
            notes='Great performance'
        )
        db_session.add(round_score)
        db_session.commit()

        assert round_score.id is not None
        assert round_score.round_id == round_obj.id
        assert round_score.team_id == teams[0].id
        assert round_score.score_value == 42.5
        assert round_score.points == 10
        assert round_score.notes == 'Great performance'

    def test_round_score_default_values(self, db_session, game, teams):
        """Test default values for round score."""
        round_obj = Round(game_id=game.id, round_number=1)
        db_session.add(round_obj)
        db_session.commit()

        round_score = RoundScore(
            round_id=round_obj.id,
            team_id=teams[0].id
        )
        db_session.add(round_score)
        db_session.commit()

        assert round_score.score_value is None
        assert round_score.points == 0
        assert round_score.notes is None
        assert round_score.multi_timer_avg is None
        assert round_score.timer_count == 0

    def test_round_score_round_relationship(self, db_session, game, teams):
        """Test relationship between round score and round."""
        round_obj = Round(game_id=game.id, round_number=1)
        db_session.add(round_obj)
        db_session.commit()

        round_score = RoundScore(
            round_id=round_obj.id,
            team_id=teams[0].id,
            points=5
        )
        db_session.add(round_score)
        db_session.commit()

        # Test forward relationship
        assert round_score.round is not None
        assert round_score.round.id == round_obj.id

        # Test back relationship
        db_session.refresh(round_obj)
        round_scores_list = list(round_obj.round_scores)
        assert len(round_scores_list) > 0
        assert round_scores_list[0].id == round_score.id

    def test_round_score_team_relationship(self, db_session, game, teams):
        """Test relationship between round score and team."""
        round_obj = Round(game_id=game.id, round_number=1)
        db_session.add(round_obj)
        db_session.commit()

        round_score = RoundScore(
            round_id=round_obj.id,
            team_id=teams[0].id,
            points=5
        )
        db_session.add(round_score)
        db_session.commit()

        # Test forward relationship
        assert round_score.team is not None
        assert round_score.team.id == teams[0].id

        # Test back relationship
        assert len(teams[0].round_scores) > 0
        assert teams[0].round_scores[0].id == round_score.id

    def test_unique_constraint_round_team(self, db_session, game, teams):
        """Test unique constraint on round_id and team_id."""
        round_obj = Round(game_id=game.id, round_number=1)
        db_session.add(round_obj)
        db_session.commit()

        # First round score
        round_score1 = RoundScore(
            round_id=round_obj.id,
            team_id=teams[0].id,
            points=5
        )
        db_session.add(round_score1)
        db_session.commit()

        # Try to create duplicate
        round_score2 = RoundScore(
            round_id=round_obj.id,
            team_id=teams[0].id,
            points=10
        )
        db_session.add(round_score2)

        # Should raise IntegrityError
        with pytest.raises(Exception):  # SQLAlchemy will raise IntegrityError
            db_session.commit()

        db_session.rollback()

    def test_multiple_teams_same_round(self, db_session, game, teams):
        """Test multiple teams can have scores in the same round."""
        round_obj = Round(game_id=game.id, round_number=1)
        db_session.add(round_obj)
        db_session.commit()

        # Create scores for multiple teams
        scores = []
        for i, team in enumerate(teams[:3]):
            score = RoundScore(
                round_id=round_obj.id,
                team_id=team.id,
                points=10 - i
            )
            db_session.add(score)
            scores.append(score)

        db_session.commit()

        # Verify all scores created
        assert all(s.id is not None for s in scores)
        assert len(round_obj.round_scores.all()) == 3

    def test_round_score_repr(self, db_session, game, teams):
        """Test string representation of round score."""
        round_obj = Round(game_id=game.id, round_number=1)
        db_session.add(round_obj)
        db_session.commit()

        round_score = RoundScore(
            round_id=round_obj.id,
            team_id=teams[0].id,
            points=8
        )
        db_session.add(round_score)
        db_session.commit()

        repr_str = repr(round_score)
        assert 'RoundScore' in repr_str
        assert str(round_obj.id) in repr_str
        assert str(teams[0].id) in repr_str
        assert '8' in repr_str

    def test_round_score_cascade_delete_from_round(self, db_session, game, teams):
        """Test that deleting a round cascades to round scores."""
        round_obj = Round(game_id=game.id, round_number=1)
        db_session.add(round_obj)
        db_session.commit()

        round_score = RoundScore(
            round_id=round_obj.id,
            team_id=teams[0].id,
            points=5
        )
        db_session.add(round_score)
        db_session.commit()

        score_id = round_score.id

        # Delete the round
        db_session.delete(round_obj)
        db_session.commit()

        # Verify round score is also deleted
        assert RoundScore.query.get(score_id) is None

    def test_multi_timer_fields(self, db_session, game, teams):
        """Test multi-timer support fields."""
        round_obj = Round(game_id=game.id, round_number=1)
        db_session.add(round_obj)
        db_session.commit()

        round_score = RoundScore(
            round_id=round_obj.id,
            team_id=teams[0].id,
            score_value=120.5,
            points=10,
            multi_timer_avg=121.3,
            timer_count=3
        )
        db_session.add(round_score)
        db_session.commit()

        assert round_score.multi_timer_avg == 121.3
        assert round_score.timer_count == 3

    def test_round_score_index(self, db_session, game, teams):
        """Test that composite index works for round_id and team_id."""
        round_obj = Round(game_id=game.id, round_number=1)
        db_session.add(round_obj)
        db_session.commit()

        # Create multiple round scores
        for team in teams[:3]:
            score = RoundScore(
                round_id=round_obj.id,
                team_id=team.id,
                points=5
            )
            db_session.add(score)

        db_session.commit()

        # Query using the indexed fields
        team_score = RoundScore.query.filter_by(
            round_id=round_obj.id,
            team_id=teams[1].id
        ).first()

        assert team_score is not None
        assert team_score.team_id == teams[1].id
