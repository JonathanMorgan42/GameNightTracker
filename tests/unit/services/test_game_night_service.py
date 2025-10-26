"""Unit tests for GameNightService."""
import pytest
from datetime import date, timedelta
from app.services.game_night_service import GameNightService
from app.models import GameNight, Team, Game, Participant


class TestGameNightService:
    """Test game night service operations."""

    def test_create_game_night(self, db_session):
        """Test creating a new game night."""
        game_night = GameNightService.create_game_night(
            name='Test Night',
            game_date=date.today()
        )

        assert game_night.id is not None
        assert game_night.name == 'Test Night'
        assert game_night.date == date.today()
        assert game_night.is_active is False
        assert game_night.is_completed is False

    def test_create_game_night_default_date(self, db_session):
        """Test creating game night with default date."""
        game_night = GameNightService.create_game_night(name='Default Date Night')

        assert game_night.date == date.today()

    def test_create_game_night_string_date(self, db_session):
        """Test creating game night with string date."""
        test_date = '2024-12-25'
        game_night = GameNightService.create_game_night(
            name='String Date Night',
            game_date=test_date
        )

        assert game_night.date == date(2024, 12, 25)

    def test_set_active_game_night(self, db_session):
        """Test setting a game night as active."""
        from app.services.team_service import TeamService
        from app.services.game_service import GameService

        # Create multiple game nights
        gn1 = GameNightService.create_game_night('Night 1', date.today())
        gn2 = GameNightService.create_game_night('Night 2', date.today())
        gn3 = GameNightService.create_game_night('Night 3', date.today())

        # Set gn2 as working context and add required teams and games
        GameNightService.set_working_context(gn2.id)
        TeamService.create_team('Team A', [{'firstName': 'A', 'lastName': 'Player'}], '#FF0000')
        TeamService.create_team('Team B', [{'firstName': 'B', 'lastName': 'Player'}], '#00FF00')
        GameService.create_game({
            'name': 'Test Game',
            'type': 'trivia',
            'sequence_number': 1,
            'point_scheme': 1,
            'metric_type': 'score',
            'scoring_direction': 'higher_better',
            'public_input': False
        }, [])

        # Activate gn2
        active_gn = GameNightService.set_active_game_night(gn2.id)

        assert active_gn.id == gn2.id
        assert active_gn.is_active is True

        # Verify others are inactive
        db_session.refresh(gn1)
        db_session.refresh(gn3)
        assert gn1.is_active is False
        assert gn3.is_active is False

    def test_set_active_game_night_deactivates_previous(self, db_session):
        """Test that setting active deactivates previous active."""
        from app.services.team_service import TeamService
        from app.services.game_service import GameService

        gn1 = GameNightService.create_game_night('Night 1', date.today())
        gn2 = GameNightService.create_game_night('Night 2', date.today())

        # Setup gn1 with teams and games
        GameNightService.set_working_context(gn1.id)
        TeamService.create_team('Team A', [{'firstName': 'A', 'lastName': 'Player'}], '#FF0000')
        TeamService.create_team('Team B', [{'firstName': 'B', 'lastName': 'Player'}], '#00FF00')
        GameService.create_game({
            'name': 'Test Game',
            'type': 'trivia',
            'sequence_number': 1,
            'point_scheme': 1,
            'metric_type': 'score',
            'scoring_direction': 'higher_better',
            'public_input': False
        }, [])

        # Activate gn1
        GameNightService.set_active_game_night(gn1.id)
        assert gn1.is_active is True

        # Mark gn1's game as complete before switching
        from app.models import Game
        game1 = Game.query.filter_by(name='Test Game').first()
        game1.isCompleted = True
        db_session.commit()

        # Setup gn2 with teams and games
        GameNightService.set_working_context(gn2.id)
        TeamService.create_team('Team C', [{'firstName': 'C', 'lastName': 'Player'}], '#0000FF')
        TeamService.create_team('Team D', [{'firstName': 'D', 'lastName': 'Player'}], '#FFFF00')
        GameService.create_game({
            'name': 'Test Game 2',
            'type': 'trivia',
            'sequence_number': 1,
            'point_scheme': 1,
            'metric_type': 'score',
            'scoring_direction': 'higher_better',
            'public_input': False
        }, [])

        # Activate gn2
        GameNightService.set_active_game_night(gn2.id)

        # Verify gn1 is now inactive
        db_session.refresh(gn1)
        assert gn1.is_active is False
        assert gn2.is_active is True

    def test_get_active_game_night(self, db_session):
        """Test getting the active game night."""
        from app.services.team_service import TeamService
        from app.services.game_service import GameService

        gn1 = GameNightService.create_game_night('Night 1', date.today())
        gn2 = GameNightService.create_game_night('Night 2', date.today())

        # No active game night initially
        active = GameNightService.get_active_game_night()
        assert active is None

        # Setup gn2 with teams and games
        GameNightService.set_working_context(gn2.id)
        TeamService.create_team('Team A', [{'firstName': 'A', 'lastName': 'Player'}], '#FF0000')
        TeamService.create_team('Team B', [{'firstName': 'B', 'lastName': 'Player'}], '#00FF00')
        GameService.create_game({
            'name': 'Test Game',
            'type': 'trivia',
            'sequence_number': 1,
            'point_scheme': 1,
            'metric_type': 'score',
            'scoring_direction': 'higher_better',
            'public_input': False
        }, [])

        # Set gn2 as active
        GameNightService.set_active_game_night(gn2.id)

        # Get active
        active = GameNightService.get_active_game_night()
        assert active is not None
        assert active.id == gn2.id

    def test_get_all_game_nights_desc(self, db_session):
        """Test getting all game nights in descending order."""
        gn1 = GameNightService.create_game_night('Night 1', date.today() - timedelta(days=2))
        gn2 = GameNightService.create_game_night('Night 2', date.today())
        gn3 = GameNightService.create_game_night('Night 3', date.today() - timedelta(days=1))

        game_nights = GameNightService.get_all_game_nights(order='desc')

        # Should be ordered newest to oldest
        assert game_nights[0].id == gn2.id
        assert game_nights[1].id == gn3.id
        assert game_nights[2].id == gn1.id

    def test_get_all_game_nights_asc(self, db_session):
        """Test getting all game nights in ascending order."""
        gn1 = GameNightService.create_game_night('Night 1', date.today() - timedelta(days=2))
        gn2 = GameNightService.create_game_night('Night 2', date.today())
        gn3 = GameNightService.create_game_night('Night 3', date.today() - timedelta(days=1))

        game_nights = GameNightService.get_all_game_nights(order='asc')

        # Should be ordered oldest to newest
        assert game_nights[0].id == gn1.id
        assert game_nights[1].id == gn3.id
        assert game_nights[2].id == gn2.id

    def test_get_completed_game_nights(self, db_session):
        """Test getting only completed game nights."""
        gn1 = GameNightService.create_game_night('Completed 1', date.today())
        gn1.is_completed = True
        gn2 = GameNightService.create_game_night('Not Completed', date.today())
        gn3 = GameNightService.create_game_night('Completed 2', date.today())
        gn3.is_completed = True
        db_session.commit()

        completed = GameNightService.get_completed_game_nights()

        assert len(completed) == 2
        assert all(gn.is_completed for gn in completed)

    def test_get_game_night_by_id(self, db_session, game_night):
        """Test getting game night by ID."""
        result = GameNightService.get_game_night_by_id(game_night.id)
        assert result.id == game_night.id
        assert result.name == game_night.name

    def test_get_game_night_by_id_not_found(self, db_session):
        """Test getting non-existent game night raises 404."""
        with pytest.raises(Exception):
            GameNightService.get_game_night_by_id(99999)

    def test_get_game_night_details(self, db_session, game_night, teams, game):
        """Test getting full game night details."""
        details = GameNightService.get_game_night_details(game_night.id)

        assert details['game_night'].id == game_night.id
        assert 'teams' in details
        assert 'games' in details
        assert 'completed_games' in details
        assert 'upcoming_games' in details
        assert 'winner' in details

    def test_end_game_night(self, db_session, game_night):
        """Test ending a game night."""
        # Mark as active first
        game_night.is_active = True
        db_session.commit()

        ended_gn = GameNightService.end_game_night(game_night.id)

        assert ended_gn.is_completed is True
        assert ended_gn.is_active is False
        assert ended_gn.ended_at is not None

    def test_wipe_game_night_data(self, db_session, game_night):
        """Test wiping game night data."""
        # Create teams and games
        team1 = Team(name='Team 1', color='#FF0000', game_night_id=game_night.id)
        team2 = Team(name='Team 2', color='#00FF00', game_night_id=game_night.id)
        db_session.add_all([team1, team2])
        db_session.commit()

        # Add participants
        p1 = Participant(firstName='John', lastName='Doe', team_id=team1.id)
        p2 = Participant(firstName='Jane', lastName='Smith', team_id=team2.id)
        db_session.add_all([p1, p2])
        db_session.commit()

        # Add game
        game = Game(
            name='Test Game',
            type='standard',
            sequence_number=1,
            game_night_id=game_night.id,
            point_scheme=1,
            metric_type='score',
            scoring_direction='higher_better'
        )
        db_session.add(game)
        db_session.commit()

        # Verify data exists
        assert len(Team.query.filter_by(game_night_id=game_night.id).all()) == 2
        assert len(Game.query.filter_by(game_night_id=game_night.id).all()) == 1

        # Wipe data
        GameNightService.wipe_game_night_data(game_night.id)

        # Verify data is wiped
        assert len(Team.query.filter_by(game_night_id=game_night.id).all()) == 0
        assert len(Game.query.filter_by(game_night_id=game_night.id).all()) == 0
        # Game night should still exist
        assert GameNight.query.get(game_night.id) is not None

    def test_delete_game_night(self, db_session, game_night):
        """Test deleting a game night."""
        game_night_id = game_night.id

        # Verify game night exists
        assert GameNight.query.get(game_night_id) is not None

        # Delete game night
        GameNightService.delete_game_night(game_night_id)

        # Verify game night is deleted
        assert GameNight.query.get(game_night_id) is None

    def test_delete_game_night_with_data(self, db_session, game_night, teams, game):
        """Test deleting game night cascades to all related data."""
        game_night_id = game_night.id

        # Verify related data exists
        assert len(Team.query.filter_by(game_night_id=game_night_id).all()) > 0
        assert len(Game.query.filter_by(game_night_id=game_night_id).all()) > 0

        # Delete game night
        GameNightService.delete_game_night(game_night_id)

        # Verify game night and all related data are deleted
        assert GameNight.query.get(game_night_id) is None
        assert len(Team.query.filter_by(game_night_id=game_night_id).all()) == 0
        assert len(Game.query.filter_by(game_night_id=game_night_id).all()) == 0

    def test_delete_game_night_not_found(self, db_session):
        """Test deleting non-existent game night raises 404."""
        with pytest.raises(Exception):
            GameNightService.delete_game_night(99999)

    def test_update_game_night(self, db_session, game_night):
        """Test updating game night details."""
        new_date = date.today() + timedelta(days=1)

        updated_gn = GameNightService.update_game_night(
            game_night_id=game_night.id,
            name='Updated Name',
            game_date=new_date
        )

        assert updated_gn.name == 'Updated Name'
        assert updated_gn.date == new_date

    def test_update_game_night_partial(self, db_session, game_night):
        """Test updating only some fields."""
        original_date = game_night.date

        updated_gn = GameNightService.update_game_night(
            game_night_id=game_night.id,
            name='New Name Only'
        )

        assert updated_gn.name == 'New Name Only'
        assert updated_gn.date == original_date
