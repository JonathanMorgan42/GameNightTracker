"""Integration tests for admin routes."""
import pytest
from app.models import Team, Game, GameNight, Participant, Score


class TestTeamRoutes:
    """Test team management routes."""

    def test_add_team_page_loads(self, authenticated_client, db_session, game_night):
        """Test add team page loads."""
        response = authenticated_client.get('/admin/teams/add')
        assert response.status_code == 200
        assert b'Team' in response.data

    def test_add_team_success(self, authenticated_client, db_session, game_night):
        """Test adding a new team."""
        response = authenticated_client.post('/admin/teams/add', data={
            'name': 'New Team',
            'color': '#FF0000',
            'participant1FirstName': 'John',
            'participant1LastName': 'Doe',
            'participant2FirstName': 'Jane',
            'participant2LastName': 'Smith'
        }, follow_redirects=True)

        assert response.status_code == 200
        # Verify team was created
        team = Team.query.filter_by(name='New Team').first()
        assert team is not None
        assert team.color == '#FF0000'

    def test_edit_team_page_loads(self, authenticated_client, db_session, teams):
        """Test edit team page loads."""
        response = authenticated_client.get(f'/admin/teams/edit/{teams[0].id}')
        assert response.status_code == 200
        assert teams[0].name.encode() in response.data

    def test_edit_team_success(self, authenticated_client, db_session, teams, participants):
        """Test editing a team."""
        team = teams[0]
        response = authenticated_client.post(f'/admin/teams/edit/{team.id}', data={
            'name': 'Updated Team Name',
            'color': '#00FF00',
            'participant1FirstName': 'Updated',
            'participant1LastName': 'Player',
            'participant2FirstName': 'Another',
            'participant2LastName': 'Update'
        }, follow_redirects=True)

        assert response.status_code == 200
        db_session.refresh(team)
        assert team.name == 'Updated Team Name'
        assert team.color == '#00FF00'


class TestGameRoutes:
    """Test game management routes."""

    def test_add_game_page_loads(self, authenticated_client, db_session, game_night, teams):
        """Test add game page loads."""
        response = authenticated_client.get('/admin/games/add')
        assert response.status_code == 200
        assert b'Game' in response.data

    def test_add_game_success(self, authenticated_client, db_session, game_night, teams):
        """Test adding a new game."""
        response = authenticated_client.post('/admin/games/add', data={
            'name': 'New Game',
            'type': 'trivia',  # Must be a valid choice from GameForm
            'sequence_number': 1,
            'point_scheme': 1,
            'metric_type': 'score',
            'scoring_direction': 'higher_better',
            'public_input': False
        }, follow_redirects=True)

        assert response.status_code == 200
        # Verify game was created
        game = Game.query.filter_by(name='New Game').first()
        assert game is not None

    def test_edit_game_page_loads(self, authenticated_client, db_session, game):
        """Test edit game page loads."""
        response = authenticated_client.get(f'/admin/games/edit/{game.id}')
        assert response.status_code == 200
        assert game.name.encode() in response.data

    def test_edit_game_success(self, authenticated_client, db_session, game):
        """Test editing a game."""
        response = authenticated_client.post(f'/admin/games/edit/{game.id}', data={
            'name': 'Updated Game',
            'type': 'strategy',  # Must be a valid choice from GameForm
            'sequence_number': game.sequence_number,
            'point_scheme': 2,
            'metric_type': 'time',
            'scoring_direction': 'lower_better',
            'public_input': True
        }, follow_redirects=True)

        assert response.status_code == 200
        db_session.refresh(game)
        assert game.name == 'Updated Game'
        assert game.type == 'strategy'


class TestScoreRoutes:
    """Test score management routes."""

    def test_edit_scores_page_loads(self, authenticated_client, db_session, game, teams):
        """Test scores editing page loads."""
        response = authenticated_client.get(f'/admin/scores/edit/{game.id}')
        assert response.status_code == 200
        assert game.name.encode() in response.data

    def test_save_scores_success(self, authenticated_client, db_session, game, teams):
        """Test saving scores."""
        response = authenticated_client.post(f'/admin/scores/edit/{game.id}', data={
            'game_id': game.id,
            f'score-{teams[0].id}': '100',
            f'points-input-{teams[0].id}': '3',
            f'score-{teams[1].id}': '90',
            f'points-input-{teams[1].id}': '2',
            'is_completed': False
        }, follow_redirects=True)

        assert response.status_code == 200

        # Verify scores were saved
        score1 = Score.query.filter_by(game_id=game.id, team_id=teams[0].id).first()
        score2 = Score.query.filter_by(game_id=game.id, team_id=teams[1].id).first()

        assert score1 is not None
        assert score2 is not None


class TestGameNightRoutes:
    """Test game night management routes."""

    def test_game_night_management_page_loads(self, authenticated_client, db_session):
        """Test game night management page loads."""
        response = authenticated_client.get('/admin/game-nights')
        assert response.status_code == 200

    def test_create_game_night_page_loads(self, authenticated_client, db_session):
        """Test create game night page loads."""
        response = authenticated_client.get('/admin/game-nights/create')
        assert response.status_code == 200

    def test_create_game_night_success(self, authenticated_client, db_session):
        """Test creating a game night."""
        from datetime import date
        response = authenticated_client.post('/admin/game-nights/create', data={
            'name': 'Test Night',
            'date': date.today().isoformat()
        }, follow_redirects=True)

        assert response.status_code == 200
        game_night = GameNight.query.filter_by(name='Test Night').first()
        assert game_night is not None

    def test_activate_game_night(self, authenticated_client, db_session, game_night):
        """Test activating a game night."""
        response = authenticated_client.post(f'/admin/game-nights/{game_night.id}/activate',
                                            follow_redirects=True)

        assert response.status_code == 200
        db_session.refresh(game_night)
        assert game_night.is_active is True

    def test_end_game_night(self, authenticated_client, db_session, game_night):
        """Test ending a game night."""
        game_night.is_active = True
        db_session.commit()

        response = authenticated_client.post(f'/admin/game-nights/{game_night.id}/end',
                                            follow_redirects=True)

        assert response.status_code == 200
        db_session.refresh(game_night)
        assert game_night.is_completed is True

    def test_wipe_game_night(self, authenticated_client, db_session, game_night, teams, game):
        """Test wiping game night data."""
        response = authenticated_client.post(f'/admin/game-nights/{game_night.id}/wipe',
                                            follow_redirects=True)

        assert response.status_code == 200
        # Verify data is wiped
        assert len(Team.query.filter_by(game_night_id=game_night.id).all()) == 0
        assert len(Game.query.filter_by(game_night_id=game_night.id).all()) == 0


class TestAuthenticationRequired:
    """Test that admin routes require authentication."""

    def test_add_team_requires_auth(self, client, db_session):
        """Test add team requires authentication."""
        response = client.get('/admin/teams/add')
        assert response.status_code == 302

    def test_add_game_requires_auth(self, client, db_session):
        """Test add game requires authentication."""
        response = client.get('/admin/games/add')
        assert response.status_code == 302

    def test_edit_scores_requires_auth(self, client, db_session):
        """Test edit scores requires authentication."""
        response = client.get('/admin/scores/edit/1')
        assert response.status_code == 302

    def test_game_night_management_requires_auth(self, client, db_session):
        """Test game night management requires authentication."""
        response = client.get('/admin/game-nights')
        assert response.status_code == 302
