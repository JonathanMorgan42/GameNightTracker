"""Unit tests for Match model.

Test IDs: MATCH-M-001 through MATCH-M-015
Coverage: Match model creation, relationships, set_winner logic, properties
"""
import pytest
from app.models import Match, Tournament, Team
from tests.factories import GameFactory, GameNightFactory, TeamFactory, TournamentFactory


@pytest.mark.unit
@pytest.mark.models
class TestMatchModel:
    """Test suite for Match model."""

    def test_match_creation(self, db_session):
        """MATCH-M-001: Test creating a match with teams and round info."""
        # Arrange
        game_night = GameNightFactory.create(db_session)
        game = GameFactory.create(db_session, game_night_id=game_night.id)
        tournament = TournamentFactory.create(db_session, game_id=game.id)
        teams = TeamFactory.create_batch(db_session, count=2, game_night_id=game_night.id)

        # Act
        match = Match(
            tournament_id=tournament.id,
            round_number=1,
            position_in_round=0,
            team1_id=teams[0].id,
            team2_id=teams[1].id
        )
        db_session.add(match)
        db_session.commit()

        # Assert
        assert match.id is not None
        assert match.tournament_id == tournament.id
        assert match.round_number == 1
        assert match.position_in_round == 0
        assert match.team1_id == teams[0].id
        assert match.team2_id == teams[1].id
        assert match.status == 'pending'
        assert match.is_bye is False

    def test_match_round_and_position(self, db_session):
        """MATCH-M-002: Test round_number and position_in_round tracking."""
        # Arrange
        game_night = GameNightFactory.create(db_session)
        game = GameFactory.create(db_session, game_night_id=game_night.id)
        tournament = TournamentFactory.create(db_session, game_id=game.id)

        # Act - Create matches in different rounds and positions
        match_r1_p0 = Match(tournament_id=tournament.id, round_number=1, position_in_round=0)
        match_r1_p1 = Match(tournament_id=tournament.id, round_number=1, position_in_round=1)
        match_r2_p0 = Match(tournament_id=tournament.id, round_number=2, position_in_round=0)
        db_session.add_all([match_r1_p0, match_r1_p1, match_r2_p0])
        db_session.commit()

        # Assert
        assert match_r1_p0.round_number == 1 and match_r1_p0.position_in_round == 0
        assert match_r1_p1.round_number == 1 and match_r1_p1.position_in_round == 1
        assert match_r2_p0.round_number == 2 and match_r2_p0.position_in_round == 0

    def test_match_teams_relationships(self, db_session):
        """MATCH-M-003: Test team1 and team2 relationships."""
        # Arrange
        game_night = GameNightFactory.create(db_session)
        game = GameFactory.create(db_session, game_night_id=game_night.id)
        tournament = TournamentFactory.create(db_session, game_id=game.id)
        teams = TeamFactory.create_batch(db_session, count=2, game_night_id=game_night.id)

        # Act
        match = Match(
            tournament_id=tournament.id,
            round_number=1,
            position_in_round=0,
            team1_id=teams[0].id,
            team2_id=teams[1].id
        )
        db_session.add(match)
        db_session.commit()

        # Assert
        assert match.team1 is not None
        assert match.team1.id == teams[0].id
        assert match.team2 is not None
        assert match.team2.id == teams[1].id

    def test_match_scores_fields(self, db_session):
        """MATCH-M-004: Test team1_score and team2_score fields."""
        # Arrange
        game_night = GameNightFactory.create(db_session)
        game = GameFactory.create(db_session, game_night_id=game_night.id)
        tournament = TournamentFactory.create(db_session, game_id=game.id)
        teams = TeamFactory.create_batch(db_session, count=2, game_night_id=game_night.id)

        # Act
        match = Match(
            tournament_id=tournament.id,
            round_number=1,
            position_in_round=0,
            team1_id=teams[0].id,
            team2_id=teams[1].id,
            team1_score=100.5,
            team2_score=95.0
        )
        db_session.add(match)
        db_session.commit()

        # Assert
        assert match.team1_score == 100.5
        assert match.team2_score == 95.0

    def test_match_winner_relationship(self, db_session):
        """MATCH-M-005: Test winner_team_id relationship."""
        # Arrange
        game_night = GameNightFactory.create(db_session)
        game = GameFactory.create(db_session, game_night_id=game_night.id)
        tournament = TournamentFactory.create(db_session, game_id=game.id)
        teams = TeamFactory.create_batch(db_session, count=2, game_night_id=game_night.id)

        # Act
        match = Match(
            tournament_id=tournament.id,
            round_number=1,
            position_in_round=0,
            team1_id=teams[0].id,
            team2_id=teams[1].id,
            winner_team_id=teams[0].id
        )
        db_session.add(match)
        db_session.commit()

        # Assert
        assert match.winner_team is not None
        assert match.winner_team.id == teams[0].id

    def test_match_status_transitions(self, db_session):
        """MATCH-M-006: Test status transitions: pending -> in_progress -> completed."""
        # Arrange
        game_night = GameNightFactory.create(db_session)
        game = GameFactory.create(db_session, game_night_id=game_night.id)
        tournament = TournamentFactory.create(db_session, game_id=game.id)

        match = Match(tournament_id=tournament.id, round_number=1, position_in_round=0)
        db_session.add(match)
        db_session.commit()

        # Assert initial state
        assert match.status == 'pending'

        # Act - Transition to in_progress
        match.status = 'in_progress'
        db_session.commit()
        assert match.status == 'in_progress'

        # Act - Transition to completed
        match.status = 'completed'
        db_session.commit()
        assert match.status == 'completed'

    def test_match_is_bye_flag(self, db_session):
        """MATCH-M-007: Test bye match where one team advances automatically."""
        # Arrange
        game_night = GameNightFactory.create(db_session)
        game = GameFactory.create(db_session, game_night_id=game_night.id)
        tournament = TournamentFactory.create(db_session, game_id=game.id)
        team = TeamFactory.create(db_session, game_night_id=game_night.id)

        # Act
        bye_match = Match(
            tournament_id=tournament.id,
            round_number=1,
            position_in_round=0,
            team1_id=team.id,
            team2_id=None,
            is_bye=True,
            status='completed',
            winner_team_id=team.id
        )
        db_session.add(bye_match)
        db_session.commit()

        # Assert
        assert bye_match.is_bye is True
        assert bye_match.team2_id is None
        assert bye_match.winner_team_id == team.id
        assert bye_match.status == 'completed'

    def test_match_is_play_in_flag(self, db_session):
        """MATCH-M-008: Test play_in match flag."""
        # Arrange
        game_night = GameNightFactory.create(db_session)
        game = GameFactory.create(db_session, game_night_id=game_night.id)
        tournament = TournamentFactory.create(db_session, game_id=game.id)

        # Act
        play_in_match = Match(
            tournament_id=tournament.id,
            round_number=0,
            position_in_round=0,
            is_play_in=True
        )
        db_session.add(play_in_match)
        db_session.commit()

        # Assert
        assert play_in_match.is_play_in is True
        assert play_in_match.round_number == 0

    def test_match_next_match_linkage(self, db_session):
        """MATCH-M-009: Test next_match_id and next_match_position linking."""
        # Arrange
        game_night = GameNightFactory.create(db_session)
        game = GameFactory.create(db_session, game_night_id=game_night.id)
        tournament = TournamentFactory.create(db_session, game_id=game.id)

        # Act - Create two rounds of matches
        match_r1 = Match(tournament_id=tournament.id, round_number=1, position_in_round=0)
        db_session.add(match_r1)
        db_session.flush()

        match_r2 = Match(tournament_id=tournament.id, round_number=2, position_in_round=0)
        db_session.add(match_r2)
        db_session.flush()

        # Link them
        match_r1.next_match_id = match_r2.id
        match_r1.next_match_position = 'team1'
        db_session.commit()

        # Assert
        assert match_r1.next_match_id == match_r2.id
        assert match_r1.next_match_position == 'team1'
        assert match_r1.next_match is not None
        assert match_r1.next_match.id == match_r2.id

    def test_match_set_winner_method(self, db_session):
        """MATCH-M-010: Test set_winner method advances team to next match."""
        # Arrange
        game_night = GameNightFactory.create(db_session)
        game = GameFactory.create(db_session, game_night_id=game_night.id)
        tournament = TournamentFactory.create(db_session, game_id=game.id)
        teams = TeamFactory.create_batch(db_session, count=2, game_night_id=game_night.id)

        # Create match chain
        match1 = Match(
            tournament_id=tournament.id,
            round_number=1,
            position_in_round=0,
            team1_id=teams[0].id,
            team2_id=teams[1].id
        )
        db_session.add(match1)
        db_session.flush()

        match2 = Match(tournament_id=tournament.id, round_number=2, position_in_round=0)
        db_session.add(match2)
        db_session.flush()

        match1.next_match_id = match2.id
        match1.next_match_position = 'team1'
        db_session.commit()

        # Act
        match1.set_winner(teams[0].id)
        db_session.commit()
        db_session.refresh(match2)

        # Assert
        assert match1.winner_team_id == teams[0].id
        assert match1.status == 'completed'
        assert match2.team1_id == teams[0].id

    def test_match_set_winner_validation(self, db_session):
        """MATCH-M-011: Test that winner must be a competing team."""
        # Arrange
        game_night = GameNightFactory.create(db_session)
        game = GameFactory.create(db_session, game_night_id=game_night.id)
        tournament = TournamentFactory.create(db_session, game_id=game.id)
        teams = TeamFactory.create_batch(db_session, count=3, game_night_id=game_night.id)

        match = Match(
            tournament_id=tournament.id,
            round_number=1,
            position_in_round=0,
            team1_id=teams[0].id,
            team2_id=teams[1].id
        )
        db_session.add(match)
        db_session.commit()

        # Act & Assert - Try to set non-competing team as winner
        with pytest.raises(ValueError, match="Winner must be one of the competing teams"):
            match.set_winner(teams[2].id)

    def test_match_display_name_property(self, db_session):
        """MATCH-M-012: Test human-readable match display names."""
        # Arrange
        game_night = GameNightFactory.create(db_session)
        game = GameFactory.create(db_session, game_night_id=game_night.id)
        tournament = TournamentFactory.create(db_session, game_id=game.id)

        # Act
        match_r1 = Match(tournament_id=tournament.id, round_number=1, position_in_round=0)
        match_r2 = Match(tournament_id=tournament.id, round_number=2, position_in_round=0)
        match_r3 = Match(tournament_id=tournament.id, round_number=3, position_in_round=0)
        match_r4 = Match(tournament_id=tournament.id, round_number=4, position_in_round=0)
        play_in = Match(tournament_id=tournament.id, round_number=0, position_in_round=0, is_play_in=True)

        db_session.add_all([match_r1, match_r2, match_r3, match_r4, play_in])
        db_session.commit()

        # Assert
        assert match_r1.display_name == 'Round 1'
        assert match_r2.display_name == 'Quarter-final'
        assert match_r3.display_name == 'Semi-final'
        assert match_r4.display_name == 'Final'
        assert play_in.display_name == 'Play-in Match'

    def test_match_is_ready_property(self, db_session):
        """MATCH-M-013: Test is_ready property (both teams assigned)."""
        # Arrange
        game_night = GameNightFactory.create(db_session)
        game = GameFactory.create(db_session, game_night_id=game_night.id)
        tournament = TournamentFactory.create(db_session, game_id=game.id)
        teams = TeamFactory.create_batch(db_session, count=2, game_night_id=game_night.id)

        # Act
        match = Match(tournament_id=tournament.id, round_number=1, position_in_round=0)
        db_session.add(match)
        db_session.commit()

        # Assert - Not ready without teams
        assert match.is_ready is False

        # Add one team
        match.team1_id = teams[0].id
        db_session.commit()
        assert match.is_ready is False

        # Add second team
        match.team2_id = teams[1].id
        db_session.commit()
        assert match.is_ready is True

    def test_match_set_winner_team2_advances(self, db_session):
        """MATCH-M-014: Test winner advancing to next match as team2."""
        # Arrange
        game_night = GameNightFactory.create(db_session)
        game = GameFactory.create(db_session, game_night_id=game_night.id)
        tournament = TournamentFactory.create(db_session, game_id=game.id)
        teams = TeamFactory.create_batch(db_session, count=2, game_night_id=game_night.id)

        # Create match chain
        match1 = Match(
            tournament_id=tournament.id,
            round_number=1,
            position_in_round=0,
            team1_id=teams[0].id,
            team2_id=teams[1].id
        )
        db_session.add(match1)
        db_session.flush()

        match2 = Match(tournament_id=tournament.id, round_number=2, position_in_round=0)
        db_session.add(match2)
        db_session.flush()

        # Link to team2 position
        match1.next_match_id = match2.id
        match1.next_match_position = 'team2'
        db_session.commit()

        # Act
        match1.set_winner(teams[1].id)
        db_session.commit()
        db_session.refresh(match2)

        # Assert
        assert match1.winner_team_id == teams[1].id
        assert match2.team2_id == teams[1].id

    def test_match_nullable_teams(self, db_session):
        """MATCH-M-015: Test that matches can have null teams initially."""
        # Arrange
        game_night = GameNightFactory.create(db_session)
        game = GameFactory.create(db_session, game_night_id=game_night.id)
        tournament = TournamentFactory.create(db_session, game_id=game.id)

        # Act
        match = Match(
            tournament_id=tournament.id,
            round_number=2,
            position_in_round=0,
            team1_id=None,
            team2_id=None
        )
        db_session.add(match)
        db_session.commit()

        # Assert
        assert match.team1_id is None
        assert match.team2_id is None
        assert match.team1 is None
        assert match.team2 is None
        assert match.is_ready is False
