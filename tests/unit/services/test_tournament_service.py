"""Unit tests for TournamentService.

Test IDs: TOURN-S-001 through TOURN-S-025
Coverage: Tournament creation, bracket generation, match updates, winner advancement
"""
import pytest
from app.services.tournament_service import TournamentService
from app.models import Tournament, Match, Game, Team
from tests.factories import GameFactory, GameNightFactory, TeamFactory


@pytest.mark.unit
@pytest.mark.services
class TestTournamentService:
    """Test suite for TournamentService."""

    def test_create_tournament_basic(self, db_session):
        """TOURN-S-001: Test creating a basic tournament with random pairing."""
        # Arrange
        game_night = GameNightFactory.create(db_session)
        game = GameFactory.create(db_session, game_night_id=game_night.id)
        teams = TeamFactory.create_batch(db_session, count=4, game_night_id=game_night.id)

        # Act
        tournament = TournamentService.create_tournament(
            game_id=game.id,
            pairing_type='random'
        )

        # Assert
        assert tournament.id is not None
        assert tournament.game_id == game.id
        assert tournament.pairing_type == 'random'
        assert tournament.matches.count() > 0
        assert tournament.is_started is False
        assert tournament.is_completed is False

    def test_create_tournament_manual_pairing(self, db_session):
        """TOURN-S-002: Test creating tournament with manual team pairings."""
        # Arrange
        game_night = GameNightFactory.create(db_session)
        game = GameFactory.create(db_session, game_night_id=game_night.id)
        teams = TeamFactory.create_batch(db_session, count=4, game_night_id=game_night.id)

        manual_pairings = [
            (teams[0].id, teams[1].id),
            (teams[2].id, teams[3].id)
        ]

        # Act
        tournament = TournamentService.create_tournament(
            game_id=game.id,
            pairing_type='manual',
            manual_pairings=manual_pairings
        )

        # Assert
        assert tournament.pairing_type == 'manual'
        first_round_matches = Match.query.filter_by(
            tournament_id=tournament.id,
            round_number=1
        ).all()

        # Verify manual pairings were used
        match1 = first_round_matches[0]
        assert {match1.team1_id, match1.team2_id} == {teams[0].id, teams[1].id}

    def test_create_tournament_included_teams(self, db_session):
        """TOURN-S-003: Test creating tournament with subset of teams."""
        # Arrange
        game_night = GameNightFactory.create(db_session)
        game = GameFactory.create(db_session, game_night_id=game_night.id)
        teams = TeamFactory.create_batch(db_session, count=6, game_night_id=game_night.id)

        # Use only first 4 teams
        included_ids = [teams[i].id for i in range(4)]

        # Act
        tournament = TournamentService.create_tournament(
            game_id=game.id,
            included_team_ids=included_ids
        )

        # Assert
        matches = tournament.matches.all()
        all_team_ids = set()
        for match in matches:
            if match.team1_id:
                all_team_ids.add(match.team1_id)
            if match.team2_id:
                all_team_ids.add(match.team2_id)

        # Only included teams should appear
        assert all_team_ids.issubset(set(included_ids))

    def test_create_tournament_odd_teams_creates_bye(self, db_session):
        """TOURN-S-004: Test tournament with odd number of teams creates bye match."""
        # Arrange
        game_night = GameNightFactory.create(db_session)
        game = GameFactory.create(db_session, game_night_id=game_night.id)
        teams = TeamFactory.create_batch(db_session, count=5, game_night_id=game_night.id)

        # Act
        tournament = TournamentService.create_tournament(game_id=game.id)

        # Assert
        bye_matches = Match.query.filter_by(
            tournament_id=tournament.id,
            is_bye=True
        ).all()

        assert len(bye_matches) == 1
        bye_match = bye_matches[0]
        assert bye_match.status == 'completed'
        assert bye_match.winner_team_id is not None
        assert bye_match.team2_id is None

    def test_create_tournament_even_teams_no_bye(self, db_session):
        """TOURN-S-005: Test tournament with even number of teams has no bye."""
        # Arrange
        game_night = GameNightFactory.create(db_session)
        game = GameFactory.create(db_session, game_night_id=game_night.id)
        teams = TeamFactory.create_batch(db_session, count=4, game_night_id=game_night.id)

        # Act
        tournament = TournamentService.create_tournament(game_id=game.id)

        # Assert
        bye_matches = Match.query.filter_by(
            tournament_id=tournament.id,
            is_bye=True
        ).all()

        assert len(bye_matches) == 0

    def test_create_tournament_two_teams_minimum(self, db_session):
        """TOURN-S-006: Test tournament with exactly 2 teams (minimum)."""
        # Arrange
        game_night = GameNightFactory.create(db_session)
        game = GameFactory.create(db_session, game_night_id=game_night.id)
        teams = TeamFactory.create_batch(db_session, count=2, game_night_id=game_night.id)

        # Act
        tournament = TournamentService.create_tournament(game_id=game.id)

        # Assert
        matches = tournament.matches.all()
        assert len(matches) == 1  # Only final match
        assert matches[0].round_number == 1
        # Both teams should be assigned (order may vary)
        team_ids = {teams[0].id, teams[1].id}
        match_team_ids = {matches[0].team1_id, matches[0].team2_id}
        assert match_team_ids == team_ids

    def test_create_tournament_one_team_fails(self, db_session):
        """TOURN-S-007: Test that tournament requires at least 2 teams."""
        # Arrange
        game_night = GameNightFactory.create(db_session)
        game = GameFactory.create(db_session, game_night_id=game_night.id)
        team = TeamFactory.create(db_session, game_night_id=game_night.id)

        # Act & Assert
        with pytest.raises(ValueError, match="At least 2 teams"):
            TournamentService.create_tournament(
                game_id=game.id,
                included_team_ids=[team.id]
            )

    def test_create_tournament_zero_teams_fails(self, db_session):
        """TOURN-S-008: Test that tournament with no teams fails."""
        # Arrange
        game_night = GameNightFactory.create(db_session)
        game = GameFactory.create(db_session, game_night_id=game_night.id)

        # Act & Assert
        with pytest.raises(ValueError, match="At least 2 teams"):
            TournamentService.create_tournament(
                game_id=game.id,
                included_team_ids=[]
            )

    def test_create_tournament_bracket_structure_correct(self, db_session):
        """TOURN-S-009: Test bracket rounds calculated correctly."""
        # Arrange
        game_night = GameNightFactory.create(db_session)
        game = GameFactory.create(db_session, game_night_id=game_night.id)
        teams = TeamFactory.create_batch(db_session, count=8, game_night_id=game_night.id)

        # Act
        tournament = TournamentService.create_tournament(game_id=game.id)

        # Assert - 8 teams should have 3 rounds (4 -> 2 -> 1)
        matches = tournament.matches.all()
        round_numbers = {m.round_number for m in matches}
        assert round_numbers == {1, 2, 3}

        # Round 1: 4 matches, Round 2: 2 matches, Round 3: 1 match
        assert len([m for m in matches if m.round_number == 1]) == 4
        assert len([m for m in matches if m.round_number == 2]) == 2
        assert len([m for m in matches if m.round_number == 3]) == 1

    def test_create_tournament_match_linkage_correct(self, db_session):
        """TOURN-S-010: Test all matches linked correctly to next round."""
        # Arrange
        game_night = GameNightFactory.create(db_session)
        game = GameFactory.create(db_session, game_night_id=game_night.id)
        teams = TeamFactory.create_batch(db_session, count=4, game_night_id=game_night.id)

        # Act
        tournament = TournamentService.create_tournament(game_id=game.id)

        # Assert
        round1_matches = Match.query.filter_by(
            tournament_id=tournament.id,
            round_number=1
        ).all()

        # All round 1 matches should have next_match_id
        for match in round1_matches:
            assert match.next_match_id is not None
            assert match.next_match_position in ['team1', 'team2']

        # Final match should have no next_match_id
        final = Match.query.filter_by(
            tournament_id=tournament.id,
            round_number=2
        ).first()
        assert final.next_match_id is None

    def test_get_tournament_by_game(self, db_session):
        """TOURN-S-011: Test retrieving tournament by game_id."""
        # Arrange
        game_night = GameNightFactory.create(db_session)
        game = GameFactory.create(db_session, game_night_id=game_night.id)
        teams = TeamFactory.create_batch(db_session, count=2, game_night_id=game_night.id)

        tournament = TournamentService.create_tournament(game_id=game.id)

        # Act
        retrieved = TournamentService.get_tournament_by_game(game.id)

        # Assert
        assert retrieved is not None
        assert retrieved.id == tournament.id
        assert retrieved.game_id == game.id

    def test_get_bracket_structure(self, db_session):
        """TOURN-S-012: Test getting bracket organized by rounds."""
        # Arrange
        game_night = GameNightFactory.create(db_session)
        game = GameFactory.create(db_session, game_night_id=game_night.id)
        teams = TeamFactory.create_batch(db_session, count=4, game_night_id=game_night.id)

        tournament = TournamentService.create_tournament(game_id=game.id)

        # Act
        bracket_data = TournamentService.get_bracket_structure(tournament.id)

        # Assert
        assert 'tournament' in bracket_data
        assert 'bracket' in bracket_data
        assert 'rounds' in bracket_data
        assert bracket_data['tournament'].id == tournament.id

        # Should have rounds
        assert len(bracket_data['rounds']) > 0
        for round_num in bracket_data['rounds']:
            assert round_num in bracket_data['bracket']
            assert len(bracket_data['bracket'][round_num]) > 0

    def test_update_match_result(self, db_session):
        """TOURN-S-013: Test updating match scores and advancing winner."""
        # Arrange
        game_night = GameNightFactory.create(db_session)
        game = GameFactory.create(db_session, game_night_id=game_night.id)
        teams = TeamFactory.create_batch(db_session, count=2, game_night_id=game_night.id)

        tournament = TournamentService.create_tournament(game_id=game.id)
        match = tournament.matches.first()

        # Act
        TournamentService.update_match_result(
            match_id=match.id,
            team1_score=100.0,
            team2_score=90.0,
            winner_team_id=teams[0].id
        )

        # Assert
        db_session.refresh(match)
        assert match.team1_score == 100.0
        assert match.team2_score == 90.0
        assert match.winner_team_id == teams[0].id
        assert match.status == 'completed'

    def test_update_match_result_validation(self, db_session):
        """TOURN-S-014: Test that winner must be a competing team."""
        # Arrange
        game_night = GameNightFactory.create(db_session)
        game = GameFactory.create(db_session, game_night_id=game_night.id)
        teams = TeamFactory.create_batch(db_session, count=3, game_night_id=game_night.id)

        tournament = TournamentService.create_tournament(
            game_id=game.id,
            included_team_ids=[teams[0].id, teams[1].id]
        )
        match = tournament.matches.first()

        # Act & Assert
        with pytest.raises(ValueError, match="Winner must be one of the two teams"):
            TournamentService.update_match_result(
                match_id=match.id,
                team1_score=100.0,
                team2_score=90.0,
                winner_team_id=teams[2].id  # Not in this match
            )

    def test_update_match_result_advances_winner(self, db_session):
        """TOURN-S-015: Test winner moves to next match."""
        # Arrange
        game_night = GameNightFactory.create(db_session)
        game = GameFactory.create(db_session, game_night_id=game_night.id)
        teams = TeamFactory.create_batch(db_session, count=4, game_night_id=game_night.id)

        tournament = TournamentService.create_tournament(game_id=game.id)

        # Get first round matches
        round1_matches = Match.query.filter_by(
            tournament_id=tournament.id,
            round_number=1
        ).order_by(Match.position_in_round).all()

        match1 = round1_matches[0]
        match2 = round1_matches[1]

        # Act - Complete both first round matches
        TournamentService.update_match_result(
            match_id=match1.id,
            team1_score=100.0,
            team2_score=90.0,
            winner_team_id=match1.team1_id
        )

        TournamentService.update_match_result(
            match_id=match2.id,
            team1_score=85.0,
            team2_score=95.0,
            winner_team_id=match2.team2_id
        )

        # Assert - Winners should be in final
        final = Match.query.filter_by(
            tournament_id=tournament.id,
            round_number=2
        ).first()

        assert final.team1_id == match1.team1_id
        assert final.team2_id == match2.team2_id

    def test_update_final_match_completes_tournament(self, db_session):
        """TOURN-S-016: Test completing final match completes tournament."""
        # Arrange
        game_night = GameNightFactory.create(db_session)
        game = GameFactory.create(db_session, game_night_id=game_night.id)
        teams = TeamFactory.create_batch(db_session, count=2, game_night_id=game_night.id)

        tournament = TournamentService.create_tournament(game_id=game.id)
        final_match = tournament.matches.first()

        # Act
        TournamentService.update_match_result(
            match_id=final_match.id,
            team1_score=100.0,
            team2_score=90.0,
            winner_team_id=teams[0].id
        )

        # Assert
        db_session.refresh(tournament)
        assert tournament.is_completed is True
        assert tournament.winner_team_id == teams[0].id

    def test_reset_tournament(self, db_session):
        """TOURN-S-017: Test resetting tournament clears all results."""
        # Arrange
        game_night = GameNightFactory.create(db_session)
        game = GameFactory.create(db_session, game_night_id=game_night.id)
        teams = TeamFactory.create_batch(db_session, count=2, game_night_id=game_night.id)

        tournament = TournamentService.create_tournament(game_id=game.id)
        match = tournament.matches.first()

        # Complete the tournament
        TournamentService.update_match_result(
            match_id=match.id,
            team1_score=100.0,
            team2_score=90.0,
            winner_team_id=teams[0].id
        )

        # Act - Reset
        TournamentService.reset_tournament(tournament.id)

        # Assert
        db_session.refresh(tournament)
        db_session.refresh(match)

        assert tournament.is_completed is False
        assert tournament.winner_team_id is None
        assert match.status == 'pending'
        assert match.team1_score is None
        assert match.team2_score is None
        assert match.winner_team_id is None

    def test_reset_tournament_preserves_bracket(self, db_session):
        """TOURN-S-018: Test reset keeps bracket structure intact."""
        # Arrange
        game_night = GameNightFactory.create(db_session)
        game = GameFactory.create(db_session, game_night_id=game_night.id)
        teams = TeamFactory.create_batch(db_session, count=4, game_night_id=game_night.id)

        tournament = TournamentService.create_tournament(game_id=game.id)

        original_match_count = tournament.matches.count()
        round1_matches_original = Match.query.filter_by(
            tournament_id=tournament.id,
            round_number=1
        ).all()

        # Complete all matches
        for match in round1_matches_original:
            if not match.is_bye:
                TournamentService.update_match_result(
                    match_id=match.id,
                    team1_score=100.0,
                    team2_score=90.0,
                    winner_team_id=match.team1_id
                )

        # Act - Reset
        TournamentService.reset_tournament(tournament.id)

        # Assert
        assert tournament.matches.count() == original_match_count

        # Round 1 teams should still be assigned
        round1_matches_after = Match.query.filter_by(
            tournament_id=tournament.id,
            round_number=1
        ).all()

        for match in round1_matches_after:
            if not match.is_bye:
                assert match.team1_id is not None
                assert match.team2_id is not None

    def test_tournament_with_3_teams(self, db_session):
        """TOURN-S-019: Test bracket generation for 3 teams."""
        # Arrange
        game_night = GameNightFactory.create(db_session)
        game = GameFactory.create(db_session, game_night_id=game_night.id)
        teams = TeamFactory.create_batch(db_session, count=3, game_night_id=game_night.id)

        # Act
        tournament = TournamentService.create_tournament(game_id=game.id)

        # Assert - Should have 4-team bracket with one bye
        matches = tournament.matches.all()
        assert len(matches) == 3  # 2 first round + 1 final

        bye_matches = [m for m in matches if m.is_bye]
        assert len(bye_matches) == 1

    def test_tournament_with_5_teams(self, db_session):
        """TOURN-S-020: Test bracket generation for 5 teams."""
        # Arrange
        game_night = GameNightFactory.create(db_session)
        game = GameFactory.create(db_session, game_night_id=game_night.id)
        teams = TeamFactory.create_batch(db_session, count=5, game_night_id=game_night.id)

        # Act
        tournament = TournamentService.create_tournament(game_id=game.id)

        # Assert - Should have 8-team bracket structure
        matches = tournament.matches.all()
        round_numbers = {m.round_number for m in matches}
        assert 3 in round_numbers  # Should have 3 rounds for 8-team bracket

        bye_matches = [m for m in matches if m.is_bye]
        assert len(bye_matches) > 0

    def test_tournament_with_8_teams_perfect_bracket(self, db_session):
        """TOURN-S-021: Test perfect power-of-2 bracket (8 teams)."""
        # Arrange
        game_night = GameNightFactory.create(db_session)
        game = GameFactory.create(db_session, game_night_id=game_night.id)
        teams = TeamFactory.create_batch(db_session, count=8, game_night_id=game_night.id)

        # Act
        tournament = TournamentService.create_tournament(game_id=game.id)

        # Assert
        matches = tournament.matches.all()
        bye_matches = [m for m in matches if m.is_bye]
        assert len(bye_matches) == 0  # Perfect bracket, no byes

        # Should have 7 total matches (4 + 2 + 1)
        assert len(matches) == 7

    def test_tournament_with_16_teams(self, db_session):
        """TOURN-S-022: Test large tournament (16 teams)."""
        # Arrange
        game_night = GameNightFactory.create(db_session)
        game = GameFactory.create(db_session, game_night_id=game_night.id)
        teams = TeamFactory.create_batch(db_session, count=16, game_night_id=game_night.id)

        # Act
        tournament = TournamentService.create_tournament(game_id=game.id)

        # Assert
        matches = tournament.matches.all()
        assert len(matches) == 15  # 8 + 4 + 2 + 1

        round_numbers = {m.round_number for m in matches}
        assert round_numbers == {1, 2, 3, 4}

    def test_generate_simple_bracket_internal(self, db_session):
        """TOURN-S-023: Test bracket generation algorithm."""
        # Arrange
        game_night = GameNightFactory.create(db_session)
        game = GameFactory.create(db_session, game_night_id=game_night.id)
        teams = TeamFactory.create_batch(db_session, count=4, game_night_id=game_night.id)

        # Act
        tournament = TournamentService.create_tournament(game_id=game.id)

        # Assert - Verify bracket structure
        matches = Match.query.filter_by(tournament_id=tournament.id).all()

        # All non-final matches should have next_match_id
        for match in matches:
            if match.round_number < 2:  # Not the final
                assert match.next_match_id is not None

    def test_bye_team_advances_automatically(self, db_session):
        """TOURN-S-024: Test bye match auto-completes and advances team."""
        # Arrange
        game_night = GameNightFactory.create(db_session)
        game = GameFactory.create(db_session, game_night_id=game_night.id)
        teams = TeamFactory.create_batch(db_session, count=3, game_night_id=game_night.id)

        # Act
        tournament = TournamentService.create_tournament(game_id=game.id)

        # Assert
        bye_match = Match.query.filter_by(
            tournament_id=tournament.id,
            is_bye=True
        ).first()

        assert bye_match is not None
        assert bye_match.status == 'completed'
        assert bye_match.winner_team_id == bye_match.team1_id

        # Check team advanced to next round
        next_match = bye_match.next_match
        if bye_match.next_match_position == 'team1':
            assert next_match.team1_id == bye_match.winner_team_id
        else:
            assert next_match.team2_id == bye_match.winner_team_id

    def test_tournament_winner_set_correctly(self, db_session):
        """TOURN-S-025: Test winner is set when final match completes."""
        # Arrange
        game_night = GameNightFactory.create(db_session)
        game = GameFactory.create(db_session, game_night_id=game_night.id)
        teams = TeamFactory.create_batch(db_session, count=4, game_night_id=game_night.id)

        tournament = TournamentService.create_tournament(game_id=game.id)

        # Complete all matches
        round1_matches = Match.query.filter_by(
            tournament_id=tournament.id,
            round_number=1
        ).all()

        for match in round1_matches:
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

        expected_winner_id = final.team1_id

        # Act
        TournamentService.update_match_result(
            match_id=final.id,
            team1_score=100.0,
            team2_score=90.0,
            winner_team_id=expected_winner_id
        )

        # Assert
        db_session.refresh(tournament)
        assert tournament.winner_team_id == expected_winner_id
        assert tournament.is_completed is True
