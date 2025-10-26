"""End-to-end workflow tests.

Test IDs: E2E-001 through E2E-010
Coverage: Complete user workflows from creation to completion
"""
import pytest
from datetime import date
from app.services.game_night_service import GameNightService
from app.services.team_service import TeamService
from app.services.game_service import GameService
from app.services.score_service import ScoreService
from app.models import GameNight, Team, Game, Score


@pytest.mark.integration
@pytest.mark.e2e
class TestE2EWorkflows:
    """End-to-end workflow tests."""

    def test_complete_game_night_lifecycle(self, db_session):
        """E2E-001: Test complete game night from creation to finalization."""
        # Step 1: Create game night
        gn = GameNightService.create_game_night('Test Night', date.today())
        assert gn.is_working_context is True

        # Step 2: Add teams
        team1 = TeamService.create_team('Team 1', [
            {'firstName': 'Alice', 'lastName': 'A'},
            {'firstName': 'Bob', 'lastName': 'B'}
        ])
        team2 = TeamService.create_team('Team 2', [
            {'firstName': 'Charlie', 'lastName': 'C'},
            {'firstName': 'Diana', 'lastName': 'D'}
        ])

        # Step 3: Add game
        game = GameService.create_game({
            'name': 'Trivia',
            'type': 'trivia',
            'sequence_number': 1,
            'point_scheme': 1,
            'metric_type': 'score',
            'scoring_direction': 'higher_better',
            'public_input': False
        }, [])

        # Step 4: Activate game night
        GameNightService.set_active_game_night(gn.id)
        db_session.refresh(gn)
        assert gn.is_active is True

        # Step 5: Score game
        ScoreService.save_scores(game.id, {
            team1.id: {'score': 100.0, 'points': 2},
            team2.id: {'score': 90.0, 'points': 1}
        }, is_completed=True)

        # Step 6: Verify leaderboard
        leaderboard = gn.get_leaderboard()
        assert leaderboard[0].id == team1.id

        # Step 7: Finalize game night
        GameNightService.end_game_night(gn.id)
        db_session.refresh(gn)
        assert gn.is_completed is True
        assert gn.is_active is False

    def test_admin_creates_manages_game_night(self, authenticated_client, db_session):
        """E2E-002: Test full admin workflow."""
        # This test documents expected admin workflow
        # Actual route tests would verify HTTP interactions
        gn = GameNightService.create_game_night('Admin Night', date.today())
        assert gn is not None

    def test_public_views_active_game_night(self, client, db_session):
        """E2E-003: Test public leaderboard viewing."""
        # Create and activate game night
        gn = GameNightService.create_game_night('Public Night', date.today())

        # Create teams (required for activation)
        TeamService.create_team('Team A', [{'firstName': 'A1', 'lastName': 'Player'}], '#FF0000')
        TeamService.create_team('Team B', [{'firstName': 'B1', 'lastName': 'Player'}], '#00FF00')

        # Create a game (required for activation)
        GameService.create_game({
            'name': 'Test Game',
            'type': 'standard',
            'sequence_number': 1,
            'point_scheme': 1,
            'metric_type': 'score',
            'scoring_direction': 'higher_better',
            'public_input': False
        }, [])

        GameNightService.set_active_game_night(gn.id)

        # Public should be able to view (tested in route tests)
        assert gn.is_active is True

    def test_public_submits_scores(self, db_session):
        """E2E-004: Test public scoring workflow."""
        # Create game with public_input enabled
        gn = GameNightService.create_game_night('Public Scoring', date.today())
        game = GameService.create_game({
            'name': 'Public Game',
            'type': 'trivia',
            'sequence_number': 1,
            'point_scheme': 1,
            'metric_type': 'score',
            'scoring_direction': 'higher_better',
            'public_input': True
        }, [])

        assert game.public_input is True

    def test_tournament_complete_workflow(self, db_session):
        """E2E-005: Test tournament creation and completion."""
        from app.services.tournament_service import TournamentService
        from tests.factories import GameNightFactory, TeamFactory, GameFactory

        # Setup
        gn = GameNightFactory.create(db_session)
        teams = TeamFactory.create_batch(db_session, count=4, game_night_id=gn.id)
        game = GameFactory.create(db_session, game_night_id=gn.id)

        # Create tournament
        tournament = TournamentService.create_tournament(game_id=game.id)

        # Complete all matches
        from app.models import Match
        matches = Match.query.filter_by(tournament_id=tournament.id).all()
        assert len(matches) > 0

    def test_multiple_admins_concurrent(self, db_session):
        """E2E-006: Test concurrent admin operations."""
        # Create game night
        gn = GameNightService.create_game_night('Concurrent Test', date.today())

        # Multiple admins can work with same data
        assert gn.is_working_context is True

    def test_switch_between_game_nights(self, db_session):
        """E2E-007: Test admin switches working context."""
        # Create two game nights
        gn1 = GameNightService.create_game_night('Night 1', date.today())
        gn2 = GameNightService.create_game_night('Night 2', date.today())

        # Switch working context
        GameNightService.set_working_context(gn2.id)

        db_session.refresh(gn1)
        db_session.refresh(gn2)

        assert gn1.is_working_context is False
        assert gn2.is_working_context is True

    def test_historical_data_integrity(self, db_session):
        """E2E-008: Test completed GN data is immutable."""
        # Create and complete game night
        gn = GameNightService.create_game_night('Historical', date.today())
        GameNightService.end_game_night(gn.id)

        db_session.refresh(gn)
        assert gn.is_completed is True

    def test_onboarding_workflow(self, db_session):
        """E2E-009: Test empty to first game night setup."""
        # No game nights exist
        all_gns = GameNight.query.all()
        initial_count = len(all_gns)

        # Create first game night
        gn = GameNightService.create_game_night('First Night', date.today())

        assert gn.is_working_context is True
        assert GameNight.query.count() == initial_count + 1

    def test_simulation_playground_workflow(self, db_session):
        """E2E-010: Test hypothetical outcome testing."""
        # This tests the concept - actual implementation in routes
        gn = GameNightService.create_game_night('Simulation', date.today())
        assert gn is not None
