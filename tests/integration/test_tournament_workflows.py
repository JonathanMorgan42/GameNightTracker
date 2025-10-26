"""Integration tests for complete tournament workflows.

Test IDs: TOURN-I-001 through TOURN-I-009
Coverage: End-to-end tournament scenarios from creation to completion
"""
import pytest
from app.services.tournament_service import TournamentService
from app.models import Match, Tournament
from tests.factories import GameFactory, GameNightFactory, TeamFactory


@pytest.mark.integration
@pytest.mark.tournament
class TestTournamentWorkflows:
    """Integration tests for tournament workflows."""

    def test_tournament_3_teams_complete(self, db_session):
        """TOURN-I-001: Complete tournament workflow with 3 teams."""
        # Arrange
        game_night = GameNightFactory.create(db_session)
        teams = TeamFactory.create_batch(db_session, count=3, game_night_id=game_night.id)
        game = GameFactory.create(db_session, game_night_id=game_night.id)

        # Act - Create tournament
        tournament = TournamentService.create_tournament(game_id=game.id)

        # Get matches
        round1_matches = Match.query.filter_by(
            tournament_id=tournament.id,
            round_number=1
        ).all()

        # Complete non-bye matches
        for match in round1_matches:
            if not match.is_bye:
                TournamentService.update_match_result(
                    match_id=match.id,
                    team1_score=100.0,
                    team2_score=90.0,
                    winner_team_id=match.team1_id
                )

        # Complete final
        final = Match.query.filter_by(
            tournament_id=tournament.id,
            round_number=2
        ).first()

        TournamentService.update_match_result(
            match_id=final.id,
            team1_score=100.0,
            team2_score=85.0,
            winner_team_id=final.team1_id
        )

        # Assert
        db_session.refresh(tournament)
        assert tournament.is_completed is True
        assert tournament.winner_team_id is not None

    def test_tournament_4_teams_complete(self, db_session):
        """TOURN-I-002: Complete tournament workflow with 4 teams."""
        # Arrange
        game_night = GameNightFactory.create(db_session)
        teams = TeamFactory.create_batch(db_session, count=4, game_night_id=game_night.id)
        game = GameFactory.create(db_session, game_night_id=game_night.id)

        # Act
        tournament = TournamentService.create_tournament(game_id=game.id)

        # Play first round
        r1_matches = Match.query.filter_by(
            tournament_id=tournament.id,
            round_number=1
        ).order_by(Match.position_in_round).all()

        assert len(r1_matches) == 2

        for i, match in enumerate(r1_matches):
            TournamentService.update_match_result(
                match_id=match.id,
                team1_score=100.0 + i,
                team2_score=90.0 + i,
                winner_team_id=match.team1_id
            )

        # Play final
        final = Match.query.filter_by(
            tournament_id=tournament.id,
            round_number=2
        ).first()

        assert final.is_ready is True

        TournamentService.update_match_result(
            match_id=final.id,
            team1_score=105.0,
            team2_score=95.0,
            winner_team_id=final.team1_id
        )

        # Assert
        db_session.refresh(tournament)
        assert tournament.is_completed is True
        assert tournament.winner_team_id == final.team1_id

    def test_tournament_5_teams_with_bye(self, db_session):
        """TOURN-I-003: Complete tournament with 5 teams (includes bye)."""
        # Arrange
        game_night = GameNightFactory.create(db_session)
        teams = TeamFactory.create_batch(db_session, count=5, game_night_id=game_night.id)
        game = GameFactory.create(db_session, game_night_id=game_night.id)

        # Act
        tournament = TournamentService.create_tournament(game_id=game.id)

        # Verify bye exists and team advanced
        bye_match = Match.query.filter_by(
            tournament_id=tournament.id,
            is_bye=True
        ).first()

        assert bye_match is not None
        assert bye_match.status == 'completed'
        bye_team_id = bye_match.winner_team_id

        # Play all non-bye round 1 matches
        r1_matches = Match.query.filter_by(
            tournament_id=tournament.id,
            round_number=1,
            is_bye=False
        ).all()

        for match in r1_matches:
            TournamentService.update_match_result(
                match_id=match.id,
                team1_score=100.0,
                team2_score=90.0,
                winner_team_id=match.team1_id
            )

        # Play semifinals
        r2_matches = Match.query.filter_by(
            tournament_id=tournament.id,
            round_number=2
        ).all()

        for match in r2_matches:
            TournamentService.update_match_result(
                match_id=match.id,
                team1_score=100.0,
                team2_score=90.0,
                winner_team_id=match.team1_id
            )

        # Play final
        final = Match.query.filter_by(
            tournament_id=tournament.id,
            round_number=3
        ).first()

        TournamentService.update_match_result(
            match_id=final.id,
            team1_score=100.0,
            team2_score=90.0,
            winner_team_id=final.team1_id
        )

        # Assert
        db_session.refresh(tournament)
        assert tournament.is_completed is True

    def test_tournament_8_teams_complete(self, db_session):
        """TOURN-I-004: Complete tournament with 8 teams (perfect bracket)."""
        # Arrange
        game_night = GameNightFactory.create(db_session)
        teams = TeamFactory.create_batch(db_session, count=8, game_night_id=game_night.id)
        game = GameFactory.create(db_session, game_night_id=game_night.id)

        # Act
        tournament = TournamentService.create_tournament(game_id=game.id)

        # Play all rounds
        for round_num in [1, 2, 3]:
            matches = Match.query.filter_by(
                tournament_id=tournament.id,
                round_number=round_num
            ).all()

            for match in matches:
                TournamentService.update_match_result(
                    match_id=match.id,
                    team1_score=100.0,
                    team2_score=90.0,
                    winner_team_id=match.team1_id
                )

        # Assert
        db_session.refresh(tournament)
        assert tournament.is_completed is True
        assert tournament.winner_team_id is not None
