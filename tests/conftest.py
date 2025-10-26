"""Pytest configuration and fixtures."""
import pytest
from app import create_app, db
from app.models import Admin, Team, Participant, Game, Score, GameNight, Tournament, Match, Penalty


@pytest.fixture(scope='session')
def app():
    """Create application for testing."""
    app = create_app('testing')

    with app.app_context():
        db.create_all()
        yield app
        db.session.remove()
        # Disable foreign keys temporarily for drop
        db.session.execute(db.text('PRAGMA foreign_keys=OFF'))
        db.drop_all()
        db.session.execute(db.text('PRAGMA foreign_keys=ON'))


@pytest.fixture(scope='function')
def db_session(app):
    """Create a new database session for a test."""
    with app.app_context():
        # Create all tables
        db.create_all()

        yield db.session

        # Rollback any changes and remove session
        db.session.rollback()
        db.session.remove()

        # Disable foreign keys temporarily for drop
        db.session.execute(db.text('PRAGMA foreign_keys=OFF'))
        db.drop_all()
        db.session.execute(db.text('PRAGMA foreign_keys=ON'))


@pytest.fixture(scope='function')
def client(app, db_session):
    """Create test client with database setup."""
    # The db_session fixture ensures tables are created
    # and we're using the same session throughout the test
    return app.test_client()


@pytest.fixture
def admin_user(db_session):
    """Create a test admin user."""
    admin = Admin(username='testadmin')
    admin.setPassword('testpassword123')
    db_session.add(admin)
    db_session.commit()
    return admin


@pytest.fixture
def authenticated_client(client, admin_user):
    """Create an authenticated test client."""
    # Simply log in using the proper endpoint with follow_redirects
    with client:
        client.post('/auth/login', data={
            'username': admin_user.username,
            'password': 'testpassword123'
        }, follow_redirects=True)
        yield client


@pytest.fixture
def game_night(db_session):
    """Create a test game night."""
    from datetime import date
    gn = GameNight(
        name='Test Game Night',
        date=date.today(),
        is_active=True,
        is_working_context=True  # Admin routes need this for team/game creation
    )
    db_session.add(gn)
    db_session.commit()
    return gn


@pytest.fixture
def teams(db_session, game_night):
    """Create test teams."""
    team1 = Team(name='Team Alpha', color='#FF0000', game_night_id=game_night.id)
    team2 = Team(name='Team Beta', color='#00FF00', game_night_id=game_night.id)
    team3 = Team(name='Team Gamma', color='#0000FF', game_night_id=game_night.id)

    db_session.add_all([team1, team2, team3])
    db_session.commit()

    return [team1, team2, team3]


@pytest.fixture
def participants(db_session, teams):
    """Create test participants."""
    participants = []
    for i, team in enumerate(teams):
        p1 = Participant(firstName=f'Player{i*2+1}', lastName='Doe', team_id=team.id)
        p2 = Participant(firstName=f'Player{i*2+2}', lastName='Smith', team_id=team.id)
        participants.extend([p1, p2])

    db_session.add_all(participants)
    db_session.commit()

    return participants


@pytest.fixture
def game(db_session, game_night):
    """Create a test game."""
    game = Game(
        name='Test Game',
        type='trivia',  # Must be a valid choice from GameForm
        game_night_id=game_night.id,
        sequence_number=1,
        point_scheme=1,
        metric_type='score',
        scoring_direction='higher_better'
    )
    db_session.add(game)
    db_session.commit()
    return game


@pytest.fixture
def completed_game(db_session, game_night, teams):
    """Create a completed game with scores."""
    game = Game(
        name='Completed Game',
        type='standard',
        game_night_id=game_night.id,
        isCompleted=True
    )
    db_session.add(game)
    db_session.commit()

    # Add scores for each team
    for i, team in enumerate(teams):
        score = Score(
            game_id=game.id,
            team_id=team.id,
            score_value=100 - (i * 10),
            points=(3 - i)
        )
        db_session.add(score)

    db_session.commit()
    return game
