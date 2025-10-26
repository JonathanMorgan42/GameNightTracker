"""Comprehensive unit tests for RoundService."""
import pytest
from sqlalchemy.exc import SQLAlchemyError
from app.services.round_service import RoundService
from app.models import Round, RoundScore, Game, Team


@pytest.mark.unit
@pytest.mark.services
class TestRoundServiceCreateRounds:
    """Test suite for creating rounds."""

    def test_create_single_round(self, db_session, game):
        """Test creating a single round."""
        rounds = RoundService.create_rounds_for_game(game.id, 1)

        assert len(rounds) == 1
        assert rounds[0].game_id == game.id
        assert rounds[0].round_number == 1
        assert rounds[0].description is None

    def test_create_multiple_rounds(self, db_session, game):
        """Test creating multiple rounds."""
        rounds = RoundService.create_rounds_for_game(game.id, 5)

        assert len(rounds) == 5
        for i, round_obj in enumerate(rounds, 1):
            assert round_obj.round_number == i
            assert round_obj.game_id == game.id

    def test_create_rounds_with_descriptions(self, db_session, game):
        """Test creating rounds with custom descriptions."""
        descriptions = ['Round 1', 'Round 2', 'Final Round']
        rounds = RoundService.create_rounds_for_game(game.id, 3, descriptions)

        assert len(rounds) == 3
        for i, round_obj in enumerate(rounds):
            assert round_obj.description == descriptions[i]

    def test_create_rounds_with_partial_descriptions(self, db_session, game):
        """Test creating more rounds than descriptions provided."""
        descriptions = ['First', 'Second']
        rounds = RoundService.create_rounds_for_game(game.id, 5, descriptions)

        assert len(rounds) == 5
        assert rounds[0].description == 'First'
        assert rounds[1].description == 'Second'
        assert rounds[2].description is None
        assert rounds[3].description is None
        assert rounds[4].description is None

    def test_create_max_rounds(self, db_session, game):
        """Test creating maximum number of rounds (50)."""
        rounds = RoundService.create_rounds_for_game(game.id, 50)

        assert len(rounds) == 50
        assert rounds[0].round_number == 1
        assert rounds[-1].round_number == 50

    def test_create_zero_rounds_fails(self, db_session, game):
        """Test that creating zero rounds raises ValueError."""
        with pytest.raises(ValueError, match="Number of rounds must be at least 1"):
            RoundService.create_rounds_for_game(game.id, 0)

    def test_create_negative_rounds_fails(self, db_session, game):
        """Test that negative number of rounds raises ValueError."""
        with pytest.raises(ValueError, match="Number of rounds must be at least 1"):
            RoundService.create_rounds_for_game(game.id, -5)

    def test_create_rounds_for_nonexistent_game(self, db_session):
        """Test creating rounds for non-existent game fails."""
        with pytest.raises(ValueError, match="Game with ID 99999 not found"):
            RoundService.create_rounds_for_game(99999, 3)

    def test_create_duplicate_rounds_fails(self, db_session, game):
        """Test that creating rounds twice for same game fails."""
        RoundService.create_rounds_for_game(game.id, 3)

        with pytest.raises(ValueError, match="already has rounds"):
            RoundService.create_rounds_for_game(game.id, 2)

    def test_create_rounds_persisted_to_db(self, db_session, game):
        """Test that rounds are properly persisted to database."""
        rounds = RoundService.create_rounds_for_game(game.id, 3)

        # Query from database independently
        db_rounds = Round.query.filter_by(game_id=game.id).order_by(Round.round_number).all()

        assert len(db_rounds) == 3
        assert db_rounds[0].id == rounds[0].id
        assert db_rounds[1].id == rounds[1].id
        assert db_rounds[2].id == rounds[2].id


@pytest.mark.unit
@pytest.mark.services
class TestRoundServiceGetRounds:
    """Test suite for retrieving rounds."""

    def test_get_rounds_for_game(self, db_session, game):
        """Test getting all rounds for a game."""
        created_rounds = RoundService.create_rounds_for_game(game.id, 3)
        retrieved_rounds = RoundService.get_rounds_for_game(game.id)

        assert len(retrieved_rounds) == 3
        assert [r.id for r in retrieved_rounds] == [r.id for r in created_rounds]

    def test_get_rounds_ordered(self, db_session, game):
        """Test that rounds are returned in order by default."""
        RoundService.create_rounds_for_game(game.id, 5)
        rounds = RoundService.get_rounds_for_game(game.id, ordered=True)

        for i, round_obj in enumerate(rounds, 1):
            assert round_obj.round_number == i

    def test_get_rounds_unordered(self, db_session, game):
        """Test getting rounds without ordering."""
        RoundService.create_rounds_for_game(game.id, 3)
        rounds = RoundService.get_rounds_for_game(game.id, ordered=False)

        assert len(rounds) == 3

    def test_get_rounds_for_game_with_no_rounds(self, db_session, game):
        """Test getting rounds for game with no rounds returns empty list."""
        rounds = RoundService.get_rounds_for_game(game.id)
        assert rounds == []

    def test_get_round_by_id(self, db_session, game):
        """Test getting a specific round by ID."""
        created_rounds = RoundService.create_rounds_for_game(game.id, 3)

        round_obj = RoundService.get_round_by_id(created_rounds[1].id)
        assert round_obj is not None
        assert round_obj.id == created_rounds[1].id
        assert round_obj.round_number == 2

    def test_get_round_by_invalid_id(self, db_session):
        """Test getting round with invalid ID returns None."""
        round_obj = RoundService.get_round_by_id(99999)
        assert round_obj is None

    def test_get_round_by_game_and_number(self, db_session, game):
        """Test getting round by game ID and round number."""
        RoundService.create_rounds_for_game(game.id, 5)

        round_obj = RoundService.get_round_by_game_and_number(game.id, 3)
        assert round_obj is not None
        assert round_obj.round_number == 3
        assert round_obj.game_id == game.id

    def test_get_round_by_game_and_invalid_number(self, db_session, game):
        """Test getting round with invalid number returns None."""
        RoundService.create_rounds_for_game(game.id, 3)

        round_obj = RoundService.get_round_by_game_and_number(game.id, 10)
        assert round_obj is None


@pytest.mark.unit
@pytest.mark.services
class TestRoundServiceSaveScores:
    """Test suite for saving round scores."""

    def test_save_round_score(self, db_session, game, teams):
        """Test saving a score for a round."""
        rounds = RoundService.create_rounds_for_game(game.id, 1)

        round_score = RoundService.save_round_score(
            rounds[0].id, teams[0].id, 100.0, 10
        )

        assert round_score.round_id == rounds[0].id
        assert round_score.team_id == teams[0].id
        assert round_score.score_value == 100.0
        assert round_score.points == 10

    def test_save_round_score_with_notes(self, db_session, game, teams):
        """Test saving a round score with notes."""
        rounds = RoundService.create_rounds_for_game(game.id, 1)

        round_score = RoundService.save_round_score(
            rounds[0].id, teams[0].id, 95.5, 8, notes="Great job!"
        )

        assert round_score.notes == "Great job!"

    def test_update_existing_round_score(self, db_session, game, teams):
        """Test updating an existing round score."""
        rounds = RoundService.create_rounds_for_game(game.id, 1)

        # Save initial score
        RoundService.save_round_score(rounds[0].id, teams[0].id, 100.0, 10)

        # Update score
        updated_score = RoundService.save_round_score(
            rounds[0].id, teams[0].id, 120.0, 12
        )

        assert updated_score.score_value == 120.0
        assert updated_score.points == 12

        # Verify only one score exists
        scores = RoundScore.query.filter_by(
            round_id=rounds[0].id, team_id=teams[0].id
        ).all()
        assert len(scores) == 1

    def test_save_score_invalid_round(self, db_session, teams):
        """Test saving score for invalid round fails."""
        with pytest.raises(ValueError, match="Round with ID 99999 not found"):
            RoundService.save_round_score(99999, teams[0].id, 100.0, 10)

    def test_save_score_invalid_team(self, db_session, game):
        """Test saving score for invalid team fails."""
        rounds = RoundService.create_rounds_for_game(game.id, 1)

        with pytest.raises(ValueError, match="Team with ID 99999 not found"):
            RoundService.save_round_score(rounds[0].id, 99999, 100.0, 10)

    def test_save_zero_score(self, db_session, game, teams):
        """Test saving zero as valid score."""
        rounds = RoundService.create_rounds_for_game(game.id, 1)

        round_score = RoundService.save_round_score(rounds[0].id, teams[0].id, 0.0, 0)

        assert round_score.score_value == 0.0
        assert round_score.points == 0

    def test_save_negative_score(self, db_session, game, teams):
        """Test saving negative score (for penalties)."""
        rounds = RoundService.create_rounds_for_game(game.id, 1)

        round_score = RoundService.save_round_score(rounds[0].id, teams[0].id, -50.0, -5)

        assert round_score.score_value == -50.0
        assert round_score.points == -5

    def test_save_decimal_score(self, db_session, game, teams):
        """Test saving decimal/float score."""
        rounds = RoundService.create_rounds_for_game(game.id, 1)

        round_score = RoundService.save_round_score(rounds[0].id, teams[0].id, 123.456, 5)

        assert round_score.score_value == 123.456

    def test_save_none_score_value(self, db_session, game, teams):
        """Test saving None as score value."""
        rounds = RoundService.create_rounds_for_game(game.id, 1)

        round_score = RoundService.save_round_score(rounds[0].id, teams[0].id, None, 0)

        assert round_score.score_value is None
        assert round_score.points == 0


@pytest.mark.unit
@pytest.mark.services
class TestRoundServiceGetScores:
    """Test suite for retrieving round scores."""

    def test_get_round_scores(self, db_session, game, teams):
        """Test getting all scores for a round."""
        rounds = RoundService.create_rounds_for_game(game.id, 1)

        # Save scores for all teams
        for i, team in enumerate(teams):
            RoundService.save_round_score(rounds[0].id, team.id, 100 - i*10, 10 - i)

        scores = RoundService.get_round_scores(rounds[0].id)

        assert len(scores) == len(teams)

    def test_get_round_scores_ordered(self, db_session, game, teams):
        """Test scores are returned ordered by points descending."""
        rounds = RoundService.create_rounds_for_game(game.id, 1)

        # Save scores in random order
        RoundService.save_round_score(rounds[0].id, teams[0].id, 80, 5)
        RoundService.save_round_score(rounds[0].id, teams[1].id, 100, 10)
        RoundService.save_round_score(rounds[0].id, teams[2].id, 90, 7)

        scores = RoundService.get_round_scores(rounds[0].id, ordered=True)

        assert scores[0].points == 10
        assert scores[1].points == 7
        assert scores[2].points == 5

    def test_get_round_scores_unordered(self, db_session, game, teams):
        """Test getting unordered scores."""
        rounds = RoundService.create_rounds_for_game(game.id, 1)

        for team in teams:
            RoundService.save_round_score(rounds[0].id, team.id, 100, 10)

        scores = RoundService.get_round_scores(rounds[0].id, ordered=False)
        assert len(scores) == len(teams)

    def test_get_round_score_for_team(self, db_session, game, teams):
        """Test getting specific team's score for a round."""
        rounds = RoundService.create_rounds_for_game(game.id, 1)
        RoundService.save_round_score(rounds[0].id, teams[0].id, 100, 10)

        score = RoundService.get_round_score_for_team(rounds[0].id, teams[0].id)

        assert score is not None
        assert score.team_id == teams[0].id
        assert score.score_value == 100

    def test_get_round_score_for_team_not_found(self, db_session, game, teams):
        """Test getting score for team that hasn't scored returns None."""
        rounds = RoundService.create_rounds_for_game(game.id, 1)

        score = RoundService.get_round_score_for_team(rounds[0].id, teams[0].id)
        assert score is None


@pytest.mark.unit
@pytest.mark.services
class TestRoundServiceCumulativeScores:
    """Test suite for cumulative score calculations."""

    def test_get_cumulative_scores_for_game(self, db_session, game, teams):
        """Test calculating cumulative scores across rounds."""
        # Mark game as having rounds
        game.has_rounds = True
        db_session.commit()

        # Create 3 rounds
        rounds = RoundService.create_rounds_for_game(game.id, 3)

        # Add scores for each team in each round
        for round_obj in rounds:
            for i, team in enumerate(teams):
                RoundService.save_round_score(
                    round_obj.id, team.id, 100 - i*10, 10 - i
                )

        cumulative = RoundService.get_cumulative_scores_for_game(game.id)

        # Each team should have cumulative data
        assert len(cumulative) == len(teams)

        # Team 0 should have 10 points per round * 3 rounds = 30
        assert cumulative[teams[0].id]['total_points'] == 30
        assert len(cumulative[teams[0].id]['rounds']) == 3

    def test_cumulative_scores_average_calculation(self, db_session, game, teams):
        """Test average score calculation in cumulative data."""
        game.has_rounds = True
        db_session.commit()

        rounds = RoundService.create_rounds_for_game(game.id, 3)

        # Add scores with varying values
        RoundService.save_round_score(rounds[0].id, teams[0].id, 100, 10)
        RoundService.save_round_score(rounds[1].id, teams[0].id, 200, 10)
        RoundService.save_round_score(rounds[2].id, teams[0].id, 300, 10)

        cumulative = RoundService.get_cumulative_scores_for_game(game.id)

        # Average should be (100 + 200 + 300) / 3 = 200
        assert cumulative[teams[0].id]['average_score'] == 200.0
        assert cumulative[teams[0].id]['rounds_played'] == 3

    def test_cumulative_scores_partial_rounds(self, db_session, game, teams):
        """Test cumulative with team missing some rounds."""
        game.has_rounds = True
        db_session.commit()

        rounds = RoundService.create_rounds_for_game(game.id, 3)

        # Team 0 plays all rounds
        for round_obj in rounds:
            RoundService.save_round_score(round_obj.id, teams[0].id, 100, 10)

        # Team 1 plays only 2 rounds
        RoundService.save_round_score(rounds[0].id, teams[1].id, 100, 10)
        RoundService.save_round_score(rounds[1].id, teams[1].id, 100, 10)

        cumulative = RoundService.get_cumulative_scores_for_game(game.id)

        # Team 0: 30 points total
        assert cumulative[teams[0].id]['total_points'] == 30
        assert cumulative[teams[0].id]['rounds_played'] == 3

        # Team 1: 20 points total, only 2 rounds played
        assert cumulative[teams[1].id]['total_points'] == 20
        assert cumulative[teams[1].id]['rounds_played'] == 2

        # Team 1 should still have 3 round entries (one with None score)
        assert len(cumulative[teams[1].id]['rounds']) == 3
        assert cumulative[teams[1].id]['rounds'][2]['score_value'] is None

    def test_cumulative_scores_no_rounds(self, db_session, game, teams):
        """Test cumulative for game without rounds returns empty dict."""
        game.has_rounds = False
        db_session.commit()

        cumulative = RoundService.get_cumulative_scores_for_game(game.id)
        assert cumulative == {}

    def test_cumulative_scores_round_details(self, db_session, game, teams):
        """Test cumulative includes round-by-round breakdown."""
        game.has_rounds = True
        db_session.commit()

        rounds = RoundService.create_rounds_for_game(
            game.id, 3, ['Round 1', 'Round 2', 'Final']
        )

        RoundService.save_round_score(rounds[0].id, teams[0].id, 100, 10, "Good!")
        RoundService.save_round_score(rounds[1].id, teams[0].id, 200, 8)
        RoundService.save_round_score(rounds[2].id, teams[0].id, 150, 9)

        cumulative = RoundService.get_cumulative_scores_for_game(game.id)

        team_rounds = cumulative[teams[0].id]['rounds']

        assert team_rounds[0]['round_number'] == 1
        assert team_rounds[0]['description'] == 'Round 1'
        assert team_rounds[0]['score_value'] == 100
        assert team_rounds[0]['points'] == 10
        assert team_rounds[0]['notes'] == "Good!"

        assert team_rounds[1]['round_number'] == 2
        assert team_rounds[2]['round_number'] == 3


@pytest.mark.unit
@pytest.mark.services
class TestRoundServiceCalculateAndSave:
    """Test suite for automatic score calculation and saving."""

    def test_calculate_and_save_higher_better(self, db_session, game, teams):
        """Test auto-calculation for higher_better scoring."""
        game.scoring_direction = 'higher_better'
        game.point_scheme = 1
        db_session.commit()

        rounds = RoundService.create_rounds_for_game(game.id, 1)

        raw_scores = {
            teams[0].id: 100,  # 1st place
            teams[1].id: 80,   # 2nd place
            teams[2].id: 90    # 3rd place (between 1st and 2nd)
        }

        saved_scores = RoundService.calculate_and_save_round_scores(rounds[0].id, raw_scores)

        # Find each team's saved score
        team0_score = next(s for s in saved_scores if s.team_id == teams[0].id)
        team1_score = next(s for s in saved_scores if s.team_id == teams[1].id)
        team2_score = next(s for s in saved_scores if s.team_id == teams[2].id)

        # 100 is highest -> rank 1 -> points = (3-0)*1 = 3
        assert team0_score.points == 3
        # 90 is 2nd -> rank 2 -> points = (3-1)*1 = 2
        assert team2_score.points == 2
        # 80 is lowest -> rank 3 -> points = (3-2)*1 = 1
        assert team1_score.points == 1

    def test_calculate_and_save_lower_better(self, db_session, game, teams):
        """Test auto-calculation for lower_better scoring (time-based)."""
        game.scoring_direction = 'lower_better'
        game.point_scheme = 2
        db_session.commit()

        rounds = RoundService.create_rounds_for_game(game.id, 1)

        raw_scores = {
            teams[0].id: 45.5,  # Fastest (best)
            teams[1].id: 52.3,  # Slowest (worst)
            teams[2].id: 48.0   # Middle
        }

        saved_scores = RoundService.calculate_and_save_round_scores(rounds[0].id, raw_scores)

        team0_score = next(s for s in saved_scores if s.team_id == teams[0].id)
        team1_score = next(s for s in saved_scores if s.team_id == teams[1].id)
        team2_score = next(s for s in saved_scores if s.team_id == teams[2].id)

        # 45.5 is lowest (best) -> rank 1 -> points = (3-0)*2 = 6
        assert team0_score.points == 6
        # 48.0 is middle -> rank 2 -> points = (3-1)*2 = 4
        assert team2_score.points == 4
        # 52.3 is highest (worst) -> rank 3 -> points = (3-2)*2 = 2
        assert team1_score.points == 2

    def test_calculate_and_save_with_none_scores(self, db_session, game, teams):
        """Test that None scores are excluded from ranking."""
        game.scoring_direction = 'higher_better'
        game.point_scheme = 1
        db_session.commit()

        rounds = RoundService.create_rounds_for_game(game.id, 1)

        raw_scores = {
            teams[0].id: 100,
            teams[1].id: None,  # Team didn't score
            teams[2].id: 90
        }

        saved_scores = RoundService.calculate_and_save_round_scores(rounds[0].id, raw_scores)

        # Only 2 teams should have saved scores
        assert len(saved_scores) == 2

    def test_calculate_and_save_invalid_round(self, db_session, teams):
        """Test calculation for invalid round fails."""
        with pytest.raises(ValueError, match="Round with ID 99999 not found"):
            RoundService.calculate_and_save_round_scores(99999, {teams[0].id: 100})

    def test_calculate_and_save_ensures_minimum_zero_points(self, db_session, game, teams):
        """Test that points are never negative (min 0)."""
        game.scoring_direction = 'higher_better'
        game.point_scheme = 1
        db_session.commit()

        rounds = RoundService.create_rounds_for_game(game.id, 1)

        raw_scores = {teams[0].id: 100}

        saved_scores = RoundService.calculate_and_save_round_scores(rounds[0].id, raw_scores)

        # Even with single team, points should be at least 0
        assert all(s.points >= 0 for s in saved_scores)


@pytest.mark.unit
@pytest.mark.services
class TestRoundServiceDelete:
    """Test suite for deleting rounds."""

    def test_delete_round(self, db_session, game):
        """Test deleting a round."""
        rounds = RoundService.create_rounds_for_game(game.id, 3)
        round_id = rounds[1].id

        RoundService.delete_round(round_id)

        # Verify round is deleted
        assert Round.query.get(round_id) is None

        # Other rounds still exist
        assert Round.query.get(rounds[0].id) is not None
        assert Round.query.get(rounds[2].id) is not None

    def test_delete_round_cascades_scores(self, db_session, game, teams):
        """Test that deleting a round deletes associated scores."""
        rounds = RoundService.create_rounds_for_game(game.id, 1)

        # Add scores
        for team in teams:
            RoundService.save_round_score(rounds[0].id, team.id, 100, 10)

        # Verify scores exist
        scores_count = RoundScore.query.filter_by(round_id=rounds[0].id).count()
        assert scores_count == len(teams)

        # Delete round
        RoundService.delete_round(rounds[0].id)

        # Verify scores are deleted
        scores_count = RoundScore.query.filter_by(round_id=rounds[0].id).count()
        assert scores_count == 0

    def test_delete_invalid_round(self, db_session):
        """Test deleting non-existent round fails."""
        with pytest.raises(ValueError, match="Round with ID 99999 not found"):
            RoundService.delete_round(99999)


@pytest.mark.unit
@pytest.mark.services
class TestRoundServiceUpdate:
    """Test suite for updating rounds."""

    def test_update_round_description(self, db_session, game):
        """Test updating round description."""
        rounds = RoundService.create_rounds_for_game(game.id, 1)

        updated = RoundService.update_round_description(rounds[0].id, "Updated Description")

        assert updated.description == "Updated Description"

        # Verify persistence
        db_round = Round.query.get(rounds[0].id)
        assert db_round.description == "Updated Description"

    def test_update_round_description_to_none(self, db_session, game):
        """Test clearing round description."""
        rounds = RoundService.create_rounds_for_game(game.id, 1, ["Initial"])

        updated = RoundService.update_round_description(rounds[0].id, None)
        assert updated.description is None

    def test_update_invalid_round_description(self, db_session):
        """Test updating description for non-existent round fails."""
        with pytest.raises(ValueError, match="Round with ID 99999 not found"):
            RoundService.update_round_description(99999, "Test")


@pytest.mark.unit
@pytest.mark.services
class TestRoundServiceBoundary:
    """Boundary and edge case tests for RoundService."""

    def test_create_exactly_50_rounds(self, db_session, game):
        """Test creating exactly 50 rounds (max boundary)."""
        rounds = RoundService.create_rounds_for_game(game.id, 50)
        assert len(rounds) == 50

    def test_save_score_with_max_value(self, db_session, game, teams):
        """Test saving maximum score value."""
        rounds = RoundService.create_rounds_for_game(game.id, 1)

        max_score = 999999.99
        round_score = RoundService.save_round_score(
            rounds[0].id, teams[0].id, max_score, 100
        )

        assert round_score.score_value == max_score

    def test_save_score_with_min_value(self, db_session, game, teams):
        """Test saving minimum score value."""
        rounds = RoundService.create_rounds_for_game(game.id, 1)

        min_score = -999999.99
        round_score = RoundService.save_round_score(
            rounds[0].id, teams[0].id, min_score, -100
        )

        assert round_score.score_value == min_score

    def test_cumulative_with_max_teams(self, db_session, game_night, game):
        """Test cumulative calculation with many teams."""
        game.has_rounds = True
        db_session.commit()

        # Create 20 teams (simulating larger tournament)
        teams = []
        for i in range(20):
            team = Team(
                name=f'Team {i}',
                color=f'#{i:06x}',
                game_night_id=game_night.id
            )
            db_session.add(team)
            teams.append(team)
        db_session.commit()

        # Create 10 rounds
        rounds = RoundService.create_rounds_for_game(game.id, 10)

        # Add scores for all teams in all rounds
        for round_obj in rounds:
            for i, team in enumerate(teams):
                RoundService.save_round_score(round_obj.id, team.id, 100-i, 20-i)

        cumulative = RoundService.get_cumulative_scores_for_game(game.id)

        # Verify all teams have data
        assert len(cumulative) == 20

        # Verify all teams have all rounds
        for team in teams:
            assert len(cumulative[team.id]['rounds']) == 10

    def test_save_very_long_notes(self, db_session, game, teams):
        """Test saving long notes string."""
        rounds = RoundService.create_rounds_for_game(game.id, 1)

        long_notes = "X" * 500  # Max notes length from validators
        round_score = RoundService.save_round_score(
            rounds[0].id, teams[0].id, 100, 10, notes=long_notes
        )

        assert round_score.notes == long_notes

    def test_description_max_length(self, db_session, game):
        """Test round description at max length."""
        long_desc = "X" * 200  # Max description length from model
        rounds = RoundService.create_rounds_for_game(game.id, 1, [long_desc])

        assert rounds[0].description == long_desc
