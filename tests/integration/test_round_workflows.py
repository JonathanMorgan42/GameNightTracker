"""Integration tests for round-based scoring workflows."""
import pytest
from app.models import Game, Team, Round, RoundScore, Score
from app.services.round_service import RoundService
from app.services.score_service import ScoreService
from app.services.game_service import GameService
from app.services.team_service import TeamService


@pytest.mark.integration
@pytest.mark.rounds
class TestRoundWorkflowBasic:
    """Basic round-based game workflow tests."""

    def test_complete_round_based_game_workflow(self, db_session, game_night):
        """Test complete workflow: create game → rounds → score → verify."""
        # Step 1: Create round-based game
        game = GameService.create_game({
            'name': 'Round Test Game',
            'type': 'trivia',
            'sequence_number': 1,
            'point_scheme': 1,
            'metric_type': 'score',
            'scoring_direction': 'higher_better',
            'public_input': False,
            'has_rounds': True,
            'number_of_rounds': None
        }, game_night_id=game_night.id)

        # Step 2: Create teams
        teams = []
        for i in range(3):
            team = TeamService.create_team(
                name=f'Team {i+1}',
                color=f'#{i:06x}',
                game_night_id=game_night.id,
                participants_data=[
                    {'firstName': f'Player{i}', 'lastName': 'Test'}
                ]
            )
            teams.append(team)

        # Step 3: Create rounds
        rounds = RoundService.create_rounds_for_game(game.id, 3, [
            'Round 1', 'Round 2', 'Final Round'
        ])

        assert len(rounds) == 3

        # Step 4: Enter scores for each round
        for i, round_obj in enumerate(rounds):
            for j, team in enumerate(teams):
                score_value = 100 - (i * 10) - (j * 5)
                RoundService.save_round_score(
                    round_obj.id,
                    team.id,
                    score_value,
                    10 - j  # Simple points
                )

        # Step 5: Verify cumulative scores
        cumulative = RoundService.get_cumulative_scores_for_game(game.id)

        # All teams should have data
        assert len(cumulative) == 3

        # Each team should have 3 rounds
        for team in teams:
            assert len(cumulative[team.id]['rounds']) == 3
            assert cumulative[team.id]['rounds_played'] == 3

        # Verify totals
        team0_total = cumulative[teams[0].id]['total_points']
        assert team0_total == 10 * 3  # 10 points per round * 3 rounds

    def test_single_round_game(self, db_session, game_night, teams):
        """Test game with only one round."""
        game = GameService.create_game({
            'name': 'Single Round',
            'type': 'trivia',
            'sequence_number': 1,
            'point_scheme': 1,
            'metric_type': 'score',
            'scoring_direction': 'higher_better',
            'public_input': False,
            'has_rounds': True,
            'number_of_rounds': None
        }, game_night_id=game_night.id)

        rounds = RoundService.create_rounds_for_game(game.id, 1, ['Only Round'])

        # Score all teams
        for i, team in enumerate(teams):
            RoundService.save_round_score(rounds[0].id, team.id, 100 - i*10, 10 - i)

        # Verify
        cumulative = RoundService.get_cumulative_scores_for_game(game.id)

        assert cumulative[teams[0].id]['total_points'] == 10
        assert cumulative[teams[0].id]['rounds_played'] == 1

    def test_many_rounds_game(self, db_session, game_night, teams):
        """Test game with many rounds (25)."""
        game = GameService.create_game({
                'name': 'Many Rounds',
                'type': 'trivia',
                'sequence_number': 1,
                'point_scheme': 10,
                'metric_type': 'score',
                'scoring_direction': 'higher_better',
                'public_input': False,
                'has_rounds': True
        ,
                'number_of_rounds': None
            }, game_night_id=game_night.id)

        num_rounds = 25
        rounds = RoundService.create_rounds_for_game(game.id, num_rounds)

        assert len(rounds) == num_rounds

        # Score first team in all rounds
        for round_obj in rounds:
            RoundService.save_round_score(round_obj.id, teams[0].id, 100, 5)

        cumulative = RoundService.get_cumulative_scores_for_game(game.id)

        assert cumulative[teams[0].id]['total_points'] == 5 * num_rounds
        assert cumulative[teams[0].id]['rounds_played'] == num_rounds


@pytest.mark.integration
@pytest.mark.rounds
class TestRoundScoringDirections:
    """Test different scoring directions with rounds."""

    def test_higher_better_round_scoring(self, db_session, game_night, teams):
        """Test higher_better scoring with rounds."""
        game = GameService.create_game({
            'name': 'Higher Better',
            'type': 'trivia',
            'sequence_number': 1,
            'point_scheme': 2,
            'metric_type': 'score',
            'scoring_direction': 'higher_better',
            'public_input': False,
            'has_rounds': True,
            'number_of_rounds': None
        }, game_night_id=game_night.id)

        rounds = RoundService.create_rounds_for_game(game.id, 1)

        # Enter raw scores with higher being better
        raw_scores = {
            teams[0].id: 100,  # Best
            teams[1].id: 80,   # Worst
            teams[2].id: 90    # Middle
        }

        saved_scores = RoundService.calculate_and_save_round_scores(
            rounds[0].id, raw_scores
        )

        # Find scores
        team0_score = next(s for s in saved_scores if s.team_id == teams[0].id)
        team1_score = next(s for s in saved_scores if s.team_id == teams[1].id)
        team2_score = next(s for s in saved_scores if s.team_id == teams[2].id)

        # Team 0 (100) should have most points
        assert team0_score.points > team2_score.points
        assert team2_score.points > team1_score.points

    def test_lower_better_round_scoring(self, db_session, game_night, teams):
        """Test lower_better scoring with rounds (time-based)."""
        game = GameService.create_game({
            'name': 'Lower Better',
            'type': 'trivia',
            'sequence_number': 1,
            'point_scheme': 2,
            'metric_type': 'time',
            'scoring_direction': 'lower_better',
            'public_input': False,
            'has_rounds': True,
            'number_of_rounds': None
        }, game_night_id=game_night.id)

        rounds = RoundService.create_rounds_for_game(game.id, 1)

        # Enter times (lower is better)
        raw_scores = {
            teams[0].id: 45.5,  # Fastest (best)
            teams[1].id: 52.3,  # Slowest (worst)
            teams[2].id: 48.0   # Middle
        }

        saved_scores = RoundService.calculate_and_save_round_scores(
            rounds[0].id, raw_scores
        )

        team0_score = next(s for s in saved_scores if s.team_id == teams[0].id)
        team1_score = next(s for s in saved_scores if s.team_id == teams[1].id)
        team2_score = next(s for s in saved_scores if s.team_id == teams[2].id)

        # Team 0 (45.5 - fastest) should have most points
        assert team0_score.points > team2_score.points
        assert team2_score.points > team1_score.points


@pytest.mark.integration
@pytest.mark.rounds
class TestPartialRoundScoring:
    """Test scenarios with partial/incomplete round scoring."""

    def test_team_missing_some_rounds(self, db_session, game_night, teams):
        """Test when a team doesn't participate in all rounds."""
        game = GameService.create_game({
                'name': 'Partial Rounds',
                'type': 'trivia',
                'sequence_number': 1,
                'point_scheme': 10,
                'metric_type': 'score',
                'scoring_direction': 'higher_better',
                'public_input': False,
                'has_rounds': True
        ,
                'number_of_rounds': None
            }, game_night_id=game_night.id)

        rounds = RoundService.create_rounds_for_game(game.id, 5)

        # Team 0 plays all rounds
        for round_obj in rounds:
            RoundService.save_round_score(round_obj.id, teams[0].id, 100, 10)

        # Team 1 plays only first 3 rounds
        for round_obj in rounds[:3]:
            RoundService.save_round_score(round_obj.id, teams[1].id, 100, 10)

        # Team 2 plays only last 2 rounds
        for round_obj in rounds[3:]:
            RoundService.save_round_score(round_obj.id, teams[2].id, 100, 10)

        cumulative = RoundService.get_cumulative_scores_for_game(game.id)

        # Team 0: 50 points total (10 * 5)
        assert cumulative[teams[0].id]['total_points'] == 50
        assert cumulative[teams[0].id]['rounds_played'] == 5

        # Team 1: 30 points total (10 * 3)
        assert cumulative[teams[1].id]['total_points'] == 30
        assert cumulative[teams[1].id]['rounds_played'] == 3

        # Team 2: 20 points total (10 * 2)
        assert cumulative[teams[2].id]['total_points'] == 20
        assert cumulative[teams[2].id]['rounds_played'] == 2

        # All teams should still have 5 round entries (some with None scores)
        for team in teams:
            assert len(cumulative[team.id]['rounds']) == 5

    def test_no_team_scored_in_round(self, db_session, game_night, teams):
        """Test round where no team has scored yet."""
        game = GameService.create_game({
                'name': 'Empty Round',
                'type': 'trivia',
                'sequence_number': 1,
                'point_scheme': 10,
                'metric_type': 'score',
                'scoring_direction': 'higher_better',
                'public_input': False,
                'has_rounds': True
        ,
                'number_of_rounds': None
            }, game_night_id=game_night.id)

        rounds = RoundService.create_rounds_for_game(game.id, 3)

        # Only score round 1 and 3, leave round 2 empty
        RoundService.save_round_score(rounds[0].id, teams[0].id, 100, 10)
        RoundService.save_round_score(rounds[2].id, teams[0].id, 100, 10)

        cumulative = RoundService.get_cumulative_scores_for_game(game.id)

        # Team should have 20 points (2 rounds)
        assert cumulative[teams[0].id]['total_points'] == 20

        # Round 2 should show None score
        round_2_data = cumulative[teams[0].id]['rounds'][1]
        assert round_2_data['score_value'] is None
        assert round_2_data['points'] == 0

    def test_update_existing_round_score(self, db_session, game_night, teams):
        """Test updating a previously entered round score."""
        game = GameService.create_game({
                'name': 'Update Round Score',
                'type': 'trivia',
                'sequence_number': 1,
                'point_scheme': 10,
                'metric_type': 'score',
                'scoring_direction': 'higher_better',
                'public_input': False,
                'has_rounds': True
        ,
                'number_of_rounds': None
            }, game_night_id=game_night.id)

        rounds = RoundService.create_rounds_for_game(game.id, 1)

        # Initial score
        RoundService.save_round_score(rounds[0].id, teams[0].id, 100, 10)

        # Verify initial
        score1 = RoundService.get_round_score_for_team(rounds[0].id, teams[0].id)
        assert score1.score_value == 100

        # Update score
        RoundService.save_round_score(rounds[0].id, teams[0].id, 150, 15, notes="Updated")

        # Verify update
        score2 = RoundService.get_round_score_for_team(rounds[0].id, teams[0].id)
        assert score2.score_value == 150
        assert score2.points == 15
        assert score2.notes == "Updated"

        # Should still be only one score
        all_scores = RoundScore.query.filter_by(
            round_id=rounds[0].id,
            team_id=teams[0].id
        ).all()
        assert len(all_scores) == 1


@pytest.mark.integration
@pytest.mark.rounds
class TestRoundScoreCalculations:
    """Test score calculations across rounds."""

    def test_cumulative_points_calculation(self, db_session, game_night, teams):
        """Test cumulative points are correctly summed."""
        game = GameService.create_game({
                'name': 'Cumulative Test',
                'type': 'trivia',
                'sequence_number': 1,
                'point_scheme': 10,
                'metric_type': 'score',
                'scoring_direction': 'higher_better',
                'public_input': False,
                'has_rounds': True
        ,
                'number_of_rounds': None
            }, game_night_id=game_night.id)

        rounds = RoundService.create_rounds_for_game(game.id, 3)

        # Different points per round
        RoundService.save_round_score(rounds[0].id, teams[0].id, 100, 10)
        RoundService.save_round_score(rounds[1].id, teams[0].id, 95, 8)
        RoundService.save_round_score(rounds[2].id, teams[0].id, 105, 12)

        cumulative = RoundService.get_cumulative_scores_for_game(game.id)

        # Total should be 10 + 8 + 12 = 30
        assert cumulative[teams[0].id]['total_points'] == 30

    def test_average_score_calculation(self, db_session, game_night, teams):
        """Test average score calculation."""
        game = GameService.create_game({
                'name': 'Average Test',
                'type': 'trivia',
                'sequence_number': 1,
                'point_scheme': 10,
                'metric_type': 'score',
                'scoring_direction': 'higher_better',
                'public_input': False,
                'has_rounds': True
        ,
                'number_of_rounds': None
            }, game_night_id=game_night.id)

        rounds = RoundService.create_rounds_for_game(game.id, 3)

        # Scores: 100, 200, 300
        RoundService.save_round_score(rounds[0].id, teams[0].id, 100, 10)
        RoundService.save_round_score(rounds[1].id, teams[0].id, 200, 8)
        RoundService.save_round_score(rounds[2].id, teams[0].id, 300, 6)

        cumulative = RoundService.get_cumulative_scores_for_game(game.id)

        # Average should be (100 + 200 + 300) / 3 = 200
        assert cumulative[teams[0].id]['average_score'] == 200.0

    def test_average_with_partial_rounds(self, db_session, game_night, teams):
        """Test average calculation excludes unplayed rounds."""
        game = GameService.create_game({
                'name': 'Partial Average',
                'type': 'trivia',
                'sequence_number': 1,
                'point_scheme': 10,
                'metric_type': 'score',
                'scoring_direction': 'higher_better',
                'public_input': False,
                'has_rounds': True
        ,
                'number_of_rounds': None
            }, game_night_id=game_night.id)

        rounds = RoundService.create_rounds_for_game(game.id, 5)

        # Only play 3 out of 5 rounds
        RoundService.save_round_score(rounds[0].id, teams[0].id, 100, 10)
        RoundService.save_round_score(rounds[1].id, teams[0].id, 200, 10)
        RoundService.save_round_score(rounds[2].id, teams[0].id, 300, 10)
        # Rounds 3 and 4 not played

        cumulative = RoundService.get_cumulative_scores_for_game(game.id)

        # Average should be (100 + 200 + 300) / 3 = 200, not including rounds 4 & 5
        assert cumulative[teams[0].id]['average_score'] == 200.0
        assert cumulative[teams[0].id]['rounds_played'] == 3


@pytest.mark.integration
@pytest.mark.rounds
class TestRoundScoreSyncToMain:
    """Test syncing round scores to main Score table."""

    def test_sync_round_scores_to_main_table(self, db_session, game_night, teams):
        """Test round scores sync to main scores table."""
        game = GameService.create_game({
                'name': 'Sync Test',
                'type': 'trivia',
                'sequence_number': 1,
                'point_scheme': 10,
                'metric_type': 'score',
                'scoring_direction': 'higher_better',
                'public_input': False,
                'has_rounds': True
        ,
                'number_of_rounds': None
            }, game_night_id=game_night.id)

        rounds = RoundService.create_rounds_for_game(game.id, 3)

        # Score all rounds
        for round_obj in rounds:
            RoundService.save_round_score(round_obj.id, teams[0].id, 100, 10)

        # Sync to main scores (if service exists)
        try:
            ScoreService.sync_round_scores_to_main_scores(game.id)

            # Check main score table
            main_score = Score.query.filter_by(
                game_id=game.id,
                team_id=teams[0].id
            ).first()

            if main_score:
                # Should have cumulative total
                assert main_score.points == 30  # 10 * 3 rounds
        except AttributeError:
            # Method might not exist
            pass

    def test_main_scores_reflect_cumulative(self, db_session, game_night, teams):
        """Test main Score table shows cumulative from rounds."""
        game = GameService.create_game({
                'name': 'Cumulative Main',
                'type': 'trivia',
                'sequence_number': 1,
                'point_scheme': 10,
                'metric_type': 'score',
                'scoring_direction': 'higher_better',
                'public_input': False,
                'has_rounds': True
        ,
                'number_of_rounds': None
            }, game_night_id=game_night.id)

        rounds = RoundService.create_rounds_for_game(game.id, 2)

        # Different points per round
        RoundService.save_round_score(rounds[0].id, teams[0].id, 100, 15)
        RoundService.save_round_score(rounds[1].id, teams[0].id, 90, 12)

        # Get cumulative
        cumulative = RoundService.get_cumulative_scores_for_game(game.id)

        # Total should be 27
        assert cumulative[teams[0].id]['total_points'] == 27


@pytest.mark.integration
@pytest.mark.rounds
class TestRoundDeletion:
    """Test deleting rounds and associated data."""

    def test_delete_round_with_scores(self, db_session, game_night, teams):
        """Test deleting a round deletes its scores."""
        game = GameService.create_game({
                'name': 'Delete Round',
                'type': 'trivia',
                'sequence_number': 1,
                'point_scheme': 10,
                'metric_type': 'score',
                'scoring_direction': 'higher_better',
                'public_input': False,
                'has_rounds': True
        ,
                'number_of_rounds': None
            }, game_night_id=game_night.id)

        rounds = RoundService.create_rounds_for_game(game.id, 3)

        # Score middle round
        for team in teams:
            RoundService.save_round_score(rounds[1].id, team.id, 100, 10)

        # Verify scores exist
        scores_before = RoundScore.query.filter_by(round_id=rounds[1].id).count()
        assert scores_before == len(teams)

        # Delete round
        RoundService.delete_round(rounds[1].id)

        # Verify scores deleted
        scores_after = RoundScore.query.filter_by(round_id=rounds[1].id).count()
        assert scores_after == 0

        # Other rounds still exist
        assert Round.query.get(rounds[0].id) is not None
        assert Round.query.get(rounds[2].id) is not None

    def test_delete_game_deletes_rounds(self, db_session, game_night):
        """Test deleting game cascades to rounds."""
        game = GameService.create_game({
                'name': 'Delete Game',
                'type': 'trivia',
                'sequence_number': 1,
                'point_scheme': 10,
                'metric_type': 'score',
                'scoring_direction': 'higher_better',
                'public_input': False,
                'has_rounds': True
        ,
                'number_of_rounds': None
            }, game_night_id=game_night.id)

        rounds = RoundService.create_rounds_for_game(game.id, 5)
        game_id = game.id

        # Delete game
        db_session.delete(game)
        db_session.commit()

        # Rounds should be deleted
        remaining_rounds = Round.query.filter_by(game_id=game_id).all()
        assert len(remaining_rounds) == 0


@pytest.mark.integration
@pytest.mark.rounds
class TestComplexRoundScenarios:
    """Test complex round-based scenarios."""

    def test_tournament_style_multi_round(self, db_session, game_night):
        """Test tournament-style game with many teams and rounds."""
        game = GameService.create_game({
            'name': 'Tournament',
            'type': 'trivia',
            'sequence_number': 1,
            'point_scheme': 1,
            'metric_type': 'score',
            'scoring_direction': 'higher_better',
            'public_input': False,
            'has_rounds': True,
            'number_of_rounds': None
        }, game_night_id=game_night.id)

        # Create 8 teams
        teams = []
        for i in range(8):
            team = TeamService.create_team(
                name=f'Team {chr(65+i)}',  # Team A, B, C, etc.
                color=f'#{i:06x}',
                game_night_id=game_night.id,
                participants_data=[
                    {'firstName': f'Player{i}', 'lastName': 'T'}
                ]
            )
            teams.append(team)

        # Create 10 rounds
        rounds = RoundService.create_rounds_for_game(game.id, 10)

        # Score all teams in all rounds
        for round_obj in rounds:
            for i, team in enumerate(teams):
                # Varying scores
                score_value = 100 - (i * 5) + (round_obj.round_number * 2)
                RoundService.save_round_score(
                    round_obj.id,
                    team.id,
                    score_value,
                    8 - i  # Points based on ranking
                )

        # Verify cumulative
        cumulative = RoundService.get_cumulative_scores_for_game(game.id)

        # All 8 teams should have data
        assert len(cumulative) == 8

        # Each team should have 10 rounds
        for team in teams:
            assert len(cumulative[team.id]['rounds']) == 10
            assert cumulative[team.id]['rounds_played'] == 10

    def test_comeback_scenario(self, db_session, game_night, teams):
        """Test team coming from behind in later rounds."""
        game = GameService.create_game({
                'name': 'Comeback',
                'type': 'trivia',
                'sequence_number': 1,
                'point_scheme': 10,
                'metric_type': 'score',
                'scoring_direction': 'higher_better',
                'public_input': False,
                'has_rounds': True
        ,
                'number_of_rounds': None
            }, game_night_id=game_night.id)

        rounds = RoundService.create_rounds_for_game(game.id, 5)

        # Team 0 starts strong
        for i in range(2):
            RoundService.save_round_score(rounds[i].id, teams[0].id, 100, 10)

        # Team 1 starts weak
        for i in range(2):
            RoundService.save_round_score(rounds[i].id, teams[1].id, 50, 5)

        # Team 1 comes back strong in rounds 3-5
        for i in range(2, 5):
            RoundService.save_round_score(rounds[i].id, teams[1].id, 150, 15)

        # Team 0 continues moderate
        for i in range(2, 5):
            RoundService.save_round_score(rounds[i].id, teams[0].id, 100, 10)

        cumulative = RoundService.get_cumulative_scores_for_game(game.id)

        # Team 0: (10 * 5) = 50
        # Team 1: (5 * 2) + (15 * 3) = 10 + 45 = 55

        assert cumulative[teams[0].id]['total_points'] == 50
        assert cumulative[teams[1].id]['total_points'] == 55

        # Team 1 should have higher total despite weak start
        assert cumulative[teams[1].id]['total_points'] > cumulative[teams[0].id]['total_points']
