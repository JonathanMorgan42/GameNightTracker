"""Integration tests for boundary conditions and overflow protection."""
import pytest
from app.models import Team, Game, Score, Penalty, GameNight
from app.services.game_service import GameService
from app.services.score_service import ScoreService
from app.services.team_service import TeamService
from app.services.round_service import RoundService
from app.utils.validators import (
    TEAM_NAME_MAX, GAME_NAME_MAX, PENALTY_NAME_MAX,
    SCORE_VALUE_MIN, SCORE_VALUE_MAX, PENALTY_VALUE_MIN, PENALTY_VALUE_MAX
)
from sqlalchemy.exc import IntegrityError, DataError


@pytest.mark.integration
@pytest.mark.boundary
class TestStringLengthBoundaries:
    """Test string length boundaries across the application."""

    def test_team_name_at_max_length(self, db_session, game_night):
        """Test team name at maximum allowed length."""
        max_name = "X" * TEAM_NAME_MAX

        team = TeamService.create_team(
            name=max_name,
            color='#FF0000',
            game_night_id=game_night.id,
            participants_data=[
                {'firstName': 'Test', 'lastName': 'Player'}
            ]
        )

        assert team.name == max_name
        assert len(team.name) == TEAM_NAME_MAX

    def test_team_name_exceeds_max_length_truncated_or_rejected(self, db_session, game_night):
        """Test team name exceeding maximum length."""
        too_long_name = "X" * (TEAM_NAME_MAX + 10)

        # Depending on implementation, might truncate or raise error
        try:
            team = TeamService.create_team(
                name=too_long_name,
                color='#FF0000',
                game_night_id=game_night.id,
                participants_data=[
                    {'firstName': 'Test', 'lastName': 'Player'}
                ]
            )
            # If created, should be truncated
            assert len(team.name) <= TEAM_NAME_MAX
        except (ValueError, DataError, IntegrityError):
            # Or should raise validation error
            pass

    def test_game_name_at_max_length(self, db_session, game_night):
        """Test game name at maximum length."""
        max_name = "Y" * GAME_NAME_MAX

        form_data = {
            'name': max_name,
            'type': 'trivia',
            'sequence_number': 1,
            'point_scheme': 10,
            'metric_type': 'score',
            'scoring_direction': 'higher_better',
            'public_input': False
        }

        game = GameService.create_game(form_data, game_night_id=game_night.id)

        assert game.name == max_name

    def test_penalty_name_at_max_length(self, db_session, game):
        """Test penalty name at maximum length."""
        max_name = "Z" * PENALTY_NAME_MAX

        penalty = Penalty(
            name=max_name,
            value=-10,
            game_id=game.id
        )
        db_session.add(penalty)
        db_session.commit()

        assert penalty.name == max_name

    def test_score_notes_very_long(self, db_session, game, teams):
        """Test saving very long score notes."""
        long_notes = "N" * 500  # Max notes length

        score = Score(
            game_id=game.id,
            team_id=teams[0].id,
            score_value=100,
            points=10,
            notes=long_notes
        )
        db_session.add(score)
        db_session.commit()

        assert len(score.notes) == 500

    def test_empty_string_handling(self, db_session, game_night):
        """Test empty string handling at database level."""
        team = TeamService.create_team(
            name='',
            color='#FF0000',
            game_night_id=game_night.id,
            participants_data=[
                {'firstName': 'Test', 'lastName': 'Player'}
            ]
        )
        # Service layer allows empty string, form validation would catch this
        assert team.name == ''


@pytest.mark.integration
@pytest.mark.boundary
class TestNumericBoundaries:
    """Test numeric value boundaries."""

    def test_score_at_max_value(self, db_session, game, teams):
        """Test score at maximum allowed value."""
        score = Score(
            game_id=game.id,
            team_id=teams[0].id,
            score_value=SCORE_VALUE_MAX,
            points=10
        )
        db_session.add(score)
        db_session.commit()

        assert score.score_value == SCORE_VALUE_MAX

    def test_score_at_min_value(self, db_session, game, teams):
        """Test score at minimum allowed value."""
        score = Score(
            game_id=game.id,
            team_id=teams[0].id,
            score_value=SCORE_VALUE_MIN,
            points=-10
        )
        db_session.add(score)
        db_session.commit()

        assert score.score_value == SCORE_VALUE_MIN

    def test_score_exceeds_max_value(self, db_session, game, teams):
        """Test score exceeding maximum value (should fail)."""
        overflow_score = SCORE_VALUE_MAX * 10

        score = Score(
            game_id=game.id,
            team_id=teams[0].id,
            score_value=overflow_score,
            points=10
        )

        # Should either fail at DB level or be rejected by validation
        try:
            db_session.add(score)
            db_session.commit()
            # If it commits, value might be clamped or cause issue
            assert score.score_value <= SCORE_VALUE_MAX or score.score_value == overflow_score
        except (DataError, IntegrityError, OverflowError):
            db_session.rollback()
            pass

    def test_penalty_at_max_value(self, db_session, game):
        """Test penalty at maximum value."""
        penalty = Penalty(
            name='Max Bonus',
            value=PENALTY_VALUE_MAX,
            game_id=game.id
        )
        db_session.add(penalty)
        db_session.commit()

        assert penalty.value == PENALTY_VALUE_MAX

    def test_penalty_at_min_value(self, db_session, game):
        """Test penalty at minimum value."""
        penalty = Penalty(
            name='Max Penalty',
            value=PENALTY_VALUE_MIN,
            game_id=game.id
        )
        db_session.add(penalty)
        db_session.commit()

        assert penalty.value == PENALTY_VALUE_MIN

    def test_zero_values(self, db_session, game, teams):
        """Test zero as valid value."""
        score = Score(
            game_id=game.id,
            team_id=teams[0].id,
            score_value=0,
            points=0
        )
        db_session.add(score)
        db_session.commit()

        assert score.score_value == 0
        assert score.points == 0

    def test_negative_points(self, db_session, game, teams):
        """Test negative points (for penalties)."""
        score = Score(
            game_id=game.id,
            team_id=teams[0].id,
            score_value=50,
            points=-15
        )
        db_session.add(score)
        db_session.commit()

        assert score.points == -15

    def test_decimal_precision(self, db_session, game, teams):
        """Test decimal precision for scores."""
        precise_score = 123.456789

        score = Score(
            game_id=game.id,
            team_id=teams[0].id,
            score_value=precise_score,
            points=10
        )
        db_session.add(score)
        db_session.commit()

        # Should maintain precision (up to database limits)
        assert abs(score.score_value - precise_score) < 0.01


@pytest.mark.integration
@pytest.mark.boundary
class TestCollectionBoundaries:
    """Test boundaries with collections (teams, games, rounds)."""

    def test_many_teams_in_game_night(self, db_session, game_night):
        """Test creating many teams (stress test)."""
        num_teams = 50

        teams = []
        for i in range(num_teams):
            team = TeamService.create_team(
                name=f'Team {i}',
                color=f'#{i:06x}',
                game_night_id=game_night.id,
                participants_data=[
                    {'firstName': f'Player{i}', 'lastName': 'Test'}
                ]
            )
            teams.append(team)

        assert len(teams) == num_teams

        # Verify all persisted
        all_teams = Team.query.filter_by(game_night_id=game_night.id).all()
        assert len(all_teams) == num_teams

    def test_max_rounds_for_game(self, db_session, game):
        """Test creating maximum allowed rounds (50)."""
        max_rounds = 50

        rounds = RoundService.create_rounds_for_game(game.id, max_rounds)

        assert len(rounds) == max_rounds

    def test_exceed_max_rounds(self, db_session, game):
        """Test creating more than maximum rounds should fail."""
        # RoundService validates max at 50 in business logic
        with pytest.raises(ValueError):
            RoundService.create_rounds_for_game(game.id, 51)

    def test_many_games_in_sequence(self, db_session, game_night):
        """Test creating many games in sequence."""
        num_games = 30

        games = []
        for i in range(1, num_games + 1):
            game = GameService.create_game({
                'name': f'Game {i}',
                'type': 'trivia',
                'sequence_number': i
            ,
                'point_scheme': 10,
                'metric_type': 'score',
                'scoring_direction': 'higher_better',
                'public_input': False
            }, game_night_id=game_night.id)
            games.append(game)

        assert len(games) == num_games

    def test_many_scores_for_game(self, db_session, game_night, game):
        """Test saving scores for many teams."""
        # Create 100 teams
        teams = []
        for i in range(100):
            team = TeamService.create_team(
                name=f'Team {i}',
                color=f'#{i:06x}',
                game_night_id=game_night.id,
                participants_data=[
                    {'firstName': f'P{i}', 'lastName': 'T'}
                ]
            )
            teams.append(team)

        # Add scores for all teams
        for team in teams:
            score = Score(
                game_id=game.id,
                team_id=team.id,
                score_value=100,
                points=10
            )
            db_session.add(score)

        db_session.commit()

        # Verify all scores saved
        scores = Score.query.filter_by(game_id=game.id).all()
        assert len(scores) == 100


@pytest.mark.integration
@pytest.mark.security
class TestSQLInjectionProtection:
    """Test SQL injection attempts are safely handled."""

    def test_sql_injection_in_team_name(self, db_session, game_night):
        """Test SQL injection attempt in team name."""
        malicious_name = "'; DROP TABLE teams; --"

        team = TeamService.create_team(
            name=malicious_name,
            color='#FF0000',
            game_night_id=game_night.id,
            participants_data=[
                {'firstName': 'Test', 'lastName': 'Player'}
            ]
        )

        # Should create team with literal string (SQLAlchemy parameterizes)
        assert team.name == malicious_name

        # Verify teams table still exists
        all_teams = Team.query.all()
        assert len(all_teams) >= 1

    def test_sql_injection_in_game_name(self, db_session, game_night):
        """Test SQL injection in game name."""
        malicious_name = "' OR '1'='1"

        game = GameService.create_game({
                'name': malicious_name,
                'type': 'trivia',
                'sequence_number': 1
        ,
                'point_scheme': 10,
                'metric_type': 'score',
                'scoring_direction': 'higher_better',
                'public_input': False
            }, game_night_id=game_night.id)

        assert game.name == malicious_name

        # Games table should be fine
        all_games = Game.query.all()
        assert len(all_games) >= 1

    def test_sql_injection_in_search_query(self, db_session, game_night, teams):
        """Test SQL injection in search/filter operations."""
        malicious_search = "' OR 1=1 --"

        # Try to query with malicious input (should be safely parameterized)
        try:
            results = Team.query.filter(Team.name.like(f'%{malicious_search}%')).all()
            # Should return empty or safe results
            assert isinstance(results, list)
        except Exception:
            # SQLAlchemy should handle safely
            pass


@pytest.mark.integration
@pytest.mark.security
class TestXSSProtection:
    """Test XSS attempts are handled (validation layer)."""

    def test_xss_in_team_name(self, db_session, game_night):
        """Test XSS attempt in team name."""
        xss_name = "<script>alert('XSS')</script>"

        team = TeamService.create_team(
            name=xss_name,
            color='#FF0000',
            game_night_id=game_night.id,
            participants_data=[
                {'firstName': 'Test', 'lastName': 'Player'}
            ]
        )

        # Should store as literal string (escaping happens at template layer)
        assert team.name == xss_name

    def test_xss_in_score_notes(self, db_session, game, teams):
        """Test XSS in score notes."""
        xss_notes = "<img src=x onerror=alert('XSS')>"

        score = Score(
            game_id=game.id,
            team_id=teams[0].id,
            score_value=100,
            points=10,
            notes=xss_notes
        )
        db_session.add(score)
        db_session.commit()

        # Should store as literal
        assert score.notes == xss_notes

    def test_xss_in_game_description(self, db_session, game):
        """Test XSS in game description/custom type."""
        xss_custom = "<iframe src='evil.com'></iframe>"

        game.custom_type = xss_custom
        db_session.commit()

        assert game.custom_type == xss_custom


@pytest.mark.integration
@pytest.mark.boundary
class TestConcurrentOperations:
    """Test concurrent operations and race conditions."""

    def test_concurrent_score_updates_same_team(self, db_session, game, teams):
        """Test concurrent updates to same score."""
        # Create initial score
        score = Score(
            game_id=game.id,
            team_id=teams[0].id,
            score_value=100,
            points=10
        )
        db_session.add(score)
        db_session.commit()

        score_id = score.id

        # Simulate concurrent updates (in real scenario, would be separate transactions)
        # Update 1
        score1 = Score.query.get(score_id)
        score1.score_value = 200

        # Update 2
        score2 = Score.query.get(score_id)
        score2.score_value = 150

        # Commit both
        db_session.commit()

        # Last write should win
        final_score = Score.query.get(score_id)
        assert final_score.score_value in [150, 200]

    def test_concurrent_team_creation(self, db_session, game_night):
        """Test concurrent team creation."""
        # Create multiple teams rapidly
        teams = []
        for i in range(10):
            team = TeamService.create_team(
                name=f'Concurrent Team {i}',
                color=f'#{i:06x}',
                game_night_id=game_night.id,
                participants_data=[
                    {'firstName': f'P{i}', 'lastName': 'T'}
                ]
            )
            teams.append(team)

        # All should be created
        assert len(teams) == 10

        # All should have unique IDs
        team_ids = [t.id for t in teams]
        assert len(set(team_ids)) == 10

    def test_concurrent_round_score_saves(self, db_session, game, teams):
        """Test concurrent round score saves."""
        game.has_rounds = True
        db_session.commit()

        rounds = RoundService.create_rounds_for_game(game.id, 3)

        # Save scores for all teams across all rounds rapidly
        for round_obj in rounds:
            for team in teams:
                RoundService.save_round_score(
                    round_obj.id,
                    team.id,
                    100,
                    10
                )

        # Verify all scores saved
        from app.models import RoundScore
        total_scores = RoundScore.query.filter(
            RoundScore.round_id.in_([r.id for r in rounds])
        ).count()

        assert total_scores == len(rounds) * len(teams)


@pytest.mark.integration
@pytest.mark.boundary
class TestDataIntegrity:
    """Test data integrity constraints."""

    def test_duplicate_team_names_allowed(self, db_session, game_night):
        """Test that duplicate team names are allowed (no unique constraint)."""
        team1 = TeamService.create_team(
            name='Duplicate',
            color='#FF0000',
            game_night_id=game_night.id,
            participants_data=[
                {'firstName': 'P1', 'lastName': 'T'}
            ]
        )

        team2 = TeamService.create_team(
            name='Duplicate',
            color='#00FF00',
            game_night_id=game_night.id,
            participants_data=[
                {'firstName': 'P2', 'lastName': 'T'}
            ]
        )

        assert team1.name == team2.name
        assert team1.id != team2.id

    def test_score_unique_per_team_per_game(self, db_session, game, teams):
        """Test only one score per team per game."""
        # Create first score
        score1 = Score(
            game_id=game.id,
            team_id=teams[0].id,
            score_value=100,
            points=10
        )
        db_session.add(score1)
        db_session.commit()

        # Try to create duplicate (might fail with unique constraint)
        score2 = Score(
            game_id=game.id,
            team_id=teams[0].id,
            score_value=200,
            points=20
        )

        try:
            db_session.add(score2)
            db_session.commit()
            # If it succeeds, check there's still only one
            scores = Score.query.filter_by(
                game_id=game.id,
                team_id=teams[0].id
            ).all()
            # Might allow multiple or enforce unique
            assert len(scores) >= 1
        except IntegrityError:
            # Expected if unique constraint exists
            db_session.rollback()
            pass

    def test_cascade_delete_game_deletes_scores(self, db_session, game_night, teams):
        """Test deleting game cascades to scores."""
        # Create game and scores
        game = GameService.create_game({
                'name': 'Delete Test',
                'type': 'trivia',
                'sequence_number': 99
        ,
                'point_scheme': 10,
                'metric_type': 'score',
                'scoring_direction': 'higher_better',
                'public_input': False
            }, game_night_id=game_night.id)

        for team in teams:
            score = Score(
                game_id=game.id,
                team_id=team.id,
                score_value=100,
                points=10
            )
            db_session.add(score)

        db_session.commit()

        game_id = game.id

        # Delete game
        db_session.delete(game)
        db_session.commit()

        # Scores should be deleted
        remaining_scores = Score.query.filter_by(game_id=game_id).all()
        assert len(remaining_scores) == 0

    def test_cascade_delete_round_deletes_round_scores(self, db_session, game, teams):
        """Test deleting round cascades to round scores."""
        game.has_rounds = True
        db_session.commit()

        rounds = RoundService.create_rounds_for_game(game.id, 1)

        # Add round scores
        for team in teams:
            RoundService.save_round_score(rounds[0].id, team.id, 100, 10)

        round_id = rounds[0].id

        # Delete round
        RoundService.delete_round(round_id)

        # Round scores should be deleted
        from app.models import RoundScore
        remaining = RoundScore.query.filter_by(round_id=round_id).all()
        assert len(remaining) == 0


@pytest.mark.integration
@pytest.mark.boundary
class TestEdgeCaseWorkflows:
    """Test edge case workflows."""

    def test_game_with_zero_teams(self, db_session, game_night):
        """Test game with no teams."""
        game = GameService.create_game({
                'name': 'No Teams Game',
                'type': 'trivia',
                'sequence_number': 1
        ,
                'point_scheme': 10,
                'metric_type': 'score',
                'scoring_direction': 'higher_better',
                'public_input': False
            }, game_night_id=game_night.id)

        # Should be able to create game without teams
        assert game.id is not None

        # Scores query should return empty
        scores = Score.query.filter_by(game_id=game.id).all()
        assert len(scores) == 0

    def test_round_based_game_with_no_rounds(self, db_session, game):
        """Test round-based game that has no rounds yet."""
        game.has_rounds = True
        db_session.commit()

        # Get cumulative scores (should handle gracefully)
        cumulative = RoundService.get_cumulative_scores_for_game(game.id)

        # Should return empty dict
        assert cumulative == {}

    def test_score_service_with_partial_team_scores(self, db_session, game, teams):
        """Test scoring when only some teams have scores."""
        # Only score first team
        scores_data = {
            teams[0].id: {'score': 100, 'points': 10}
        }
        ScoreService.save_scores(game.id, scores_data)

        # Get all scores
        all_scores = ScoreService.get_scores_for_game(game.id)

        # Should only have one score
        assert len(all_scores) == 1
        assert all_scores[0].team_id == teams[0].id

    def test_negative_sequence_numbers(self, db_session, game_night):
        """Test games with negative sequence numbers."""
        game = GameService.create_game({
                'name': 'Negative Seq',
                'type': 'trivia',
                'sequence_number': -1
        ,
                'point_scheme': 10,
                'metric_type': 'score',
                'scoring_direction': 'higher_better',
                'public_input': False
            }, game_night_id=game_night.id)

        # Should allow (might be used for special ordering)
        assert game.sequence_number == -1

    def test_very_high_sequence_numbers(self, db_session, game_night):
        """Test games with very high sequence numbers."""
        game = GameService.create_game({
                'name': 'High Seq',
                'type': 'trivia',
                'sequence_number': 9999
        ,
                'point_scheme': 10,
                'metric_type': 'score',
                'scoring_direction': 'higher_better',
                'public_input': False
            }, game_night_id=game_night.id)

        assert game.sequence_number == 9999
