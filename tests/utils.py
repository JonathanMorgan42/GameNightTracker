"""Test utility functions."""
from contextlib import contextmanager
from tests.factories import GameNightFactory, TeamFactory, GameFactory


@contextmanager
def assert_raises_with_message(exception_class, message_substring):
    """Assert exception is raised with specific message.

    Args:
        exception_class: Expected exception type
        message_substring: Substring expected in exception message

    Raises:
        AssertionError: If exception not raised or message doesn't match

    Example:
        with assert_raises_with_message(ValueError, "at least 2 teams"):
            TournamentService.create_tournament(game_id=1, included_team_ids=[])
    """
    try:
        yield
        assert False, f"Expected {exception_class.__name__} to be raised"
    except exception_class as e:
        assert message_substring.lower() in str(e).lower(), \
            f"Expected message to contain '{message_substring}', got '{str(e)}'"


def create_complete_game_night(db_session, name='Test GN', team_count=3, game_count=2):
    """Create a complete game night with teams and games.

    Args:
        db_session: Database session
        name: Game night name
        team_count: Number of teams to create
        game_count: Number of games to create

    Returns:
        Tuple of (game_night, teams, games)
    """
    gn = GameNightFactory.create(db_session, name=name)

    teams = TeamFactory.create_batch(
        db_session,
        count=team_count,
        game_night_id=gn.id
    )

    games = []
    for i in range(1, game_count + 1):
        game = GameFactory.create(
            db_session,
            name=f'Game {i}',
            game_night_id=gn.id,
            sequence_number=i
        )
        games.append(game)

    return gn, teams, games


def assert_cascade_delete(db_session, model, deleted_id, should_exist=False):
    """Assert that a record was cascade deleted (or preserved).

    Args:
        db_session: Database session
        model: Model class to query
        deleted_id: ID of record to check
        should_exist: If True, assert record exists; if False, assert deleted

    Raises:
        AssertionError: If existence doesn't match expectation
    """
    record = db_session.query(model).filter_by(id=deleted_id).first()
    if should_exist:
        assert record is not None, f"{model.__name__} {deleted_id} should exist but was deleted"
    else:
        assert record is None, f"{model.__name__} {deleted_id} should be deleted but still exists"


def create_authenticated_client(client, admin_user):
    """Authenticate a test client.

    Args:
        client: Flask test client
        admin_user: Admin user instance

    Returns:
        Authenticated client
    """
    with client:
        client.post('/auth/login', data={
            'username': admin_user.username,
            'password': 'testpassword123'
        }, follow_redirects=True)
        return client


def assert_response_contains(response, *strings):
    """Assert response contains all specified strings.

    Args:
        response: Flask response object
        *strings: Strings to check for in response

    Raises:
        AssertionError: If any string not found
    """
    response_data = response.data.decode('utf-8').lower()
    for s in strings:
        assert s.lower() in response_data, \
            f"Expected '{s}' in response but not found"


def assert_response_not_contains(response, *strings):
    """Assert response does not contain specified strings.

    Args:
        response: Flask response object
        *strings: Strings to check for absence in response

    Raises:
        AssertionError: If any string found
    """
    response_data = response.data.decode('utf-8').lower()
    for s in strings:
        assert s.lower() not in response_data, \
            f"Did not expect '{s}' in response but it was found"


def count_tests_in_file(filepath):
    """Count test functions in a file.

    Args:
        filepath: Path to test file

    Returns:
        Number of test functions found
    """
    count = 0
    with open(filepath, 'r') as f:
        for line in f:
            if line.strip().startswith('def test_'):
                count += 1
    return count
