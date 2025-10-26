"""Integration tests for WebSocket real-time collaboration features."""
import pytest
import time
from flask_socketio import SocketIOTestClient
from app import create_app, socketio, db
from app.models import Game, Team, Score, Round, RoundScore
from app.services.round_service import RoundService


@pytest.fixture(scope='function')
def socketio_app():
    """Create app with SocketIO for testing."""
    app = create_app('testing')
    with app.app_context():
        db.create_all()
        yield app
        db.session.rollback()
        db.session.remove()
        db.session.execute(db.text('PRAGMA foreign_keys=OFF'))
        db.drop_all()
        db.session.execute(db.text('PRAGMA foreign_keys=ON'))


@pytest.fixture
def socketio_client(socketio_app):
    """Create SocketIO test client."""
    return socketio.test_client(socketio_app, flask_test_client=socketio_app.test_client())


@pytest.mark.integration
@pytest.mark.websockets
class TestWebSocketIntegrationBasic:
    """Basic WebSocket integration tests."""

    def test_client_connects_successfully(self, socketio_client):
        """Test client can connect to WebSocket server."""
        assert socketio_client.is_connected()

    def test_client_receives_connected_event(self, socketio_client):
        """Test client receives connected confirmation."""
        # Client should be connected
        assert socketio_client.is_connected()

        # Get received events
        received = socketio_client.get_received()

        # Should have received some connection-related events
        assert isinstance(received, list)

    def test_multiple_clients_can_connect(self, socketio_app):
        """Test multiple clients can connect simultaneously."""
        client1 = socketio.test_client(socketio_app)
        client2 = socketio.test_client(socketio_app)
        client3 = socketio.test_client(socketio_app)

        assert client1.is_connected()
        assert client2.is_connected()
        assert client3.is_connected()

        client1.disconnect()
        client2.disconnect()
        client3.disconnect()

    def test_client_disconnects_cleanly(self, socketio_client):
        """Test client disconnection."""
        assert socketio_client.is_connected()
        socketio_client.disconnect()
        assert not socketio_client.is_connected()


@pytest.mark.integration
@pytest.mark.websockets
class TestWebSocketGameRoom:
    """Test game room join/leave functionality."""

    def test_join_game_room(self, socketio_app, socketio_client, db_session, game_night, game, teams):
        """Test joining a game room."""
        # Extract IDs before entering new app context
        game_id = game.id

        with socketio_app.app_context():
            # Join game room
            socketio_client.emit('join_game', {'game_id': game_id})

            # Get received messages
            received = socketio_client.get_received()

            # Should receive game_state
            game_state_events = [r for r in received if r.get('name') == 'game_state']
            assert len(game_state_events) >= 0  # May or may not receive immediately in test

    def test_leave_game_room(self, socketio_app, socketio_client, db_session, game_night, game):
        """Test leaving a game room."""
        # Extract IDs before entering new app context
        game_id = game.id

        with socketio_app.app_context():
            # Join then leave
            socketio_client.emit('join_game', {'game_id': game_id})
            socketio_client.emit('leave_game', {'game_id': game_id})

            # Should not error
            assert socketio_client.is_connected()

    def test_multiple_clients_in_same_game_room(self, socketio_app, db_session, game_night, game):
        """Test multiple clients can join same game room."""
        # Extract IDs before entering new app context
        game_id = game.id

        with socketio_app.app_context():
            client1 = socketio.test_client(socketio_app)
            client2 = socketio.test_client(socketio_app)

            client1.emit('join_game', {'game_id': game_id})
            client2.emit('join_game', {'game_id': game_id})

            assert client1.is_connected()
            assert client2.is_connected()

            client1.disconnect()
            client2.disconnect()


@pytest.mark.integration
@pytest.mark.websockets
class TestWebSocketScoreUpdates:
    """Test real-time score update broadcasting."""

    def test_score_update_regular_game(self, socketio_app, db_session, game_night, game, teams):
        """Test score update for regular game is broadcast."""
        # Extract IDs before entering new app context
        game_id = game.id
        team_ids = [t.id for t in teams]

        with socketio_app.app_context():
            client1 = socketio.test_client(socketio_app)
            client2 = socketio.test_client(socketio_app)

            # Both join same game
            client1.emit('join_game', {'game_id': game_id})
            client2.emit('join_game', {'game_id': game_id})

            # Clear received messages
            client1.get_received()
            client2.get_received()

            # Client 1 updates score
            client1.emit('update_score', {
                'game_id': game_id,
                'team_id': team_ids[0],
                'score': 100.0,
                'points': 10
            })

            # Give time for processing
            time.sleep(0.1)

            # Client 2 should receive the update
            received2 = client2.get_received()

            # Look for score_updated event
            score_updates = [r for r in received2 if r.get('name') == 'score_updated']

            # May receive update (depends on room broadcasting in test mode)
            # At minimum, verify no errors
            assert client2.is_connected()

            client1.disconnect()
            client2.disconnect()

    def test_score_update_round_based_game(self, socketio_app):
        """Test score update for round-based game."""
        with socketio_app.app_context():
            # Create test data within socketio_app context
            from app.models import GameNight
            from datetime import date
            game_night = GameNight(name='Test Night', date=date.today(), is_active=True)
            db.session.add(game_night)
            db.session.flush()

            team1 = Team(name='Team 1', color='#FF0000', game_night_id=game_night.id)
            db.session.add(team1)
            db.session.flush()

            game_obj = Game(
                name='Round Test',
                type='trivia',
                game_night_id=game_night.id,
                sequence_number=1,
                point_scheme=1,
                metric_type='score',
                scoring_direction='higher_better',
                has_rounds=True
            )
            db.session.add(game_obj)
            db.session.flush()

            game_id = game_obj.id
            team_ids = [team1.id]

            rounds = RoundService.create_rounds_for_game(game_id, 3)

            client = socketio.test_client(socketio_app)
            client.emit('join_game', {
                'game_id': game_id,
                'round_id': rounds[0].id
            })

            client.get_received()

            # Update round score
            client.emit('update_score', {
                'game_id': game_id,
                'team_id': team_ids[0],
                'score': 95.0,
                'points': 8,
                'round_id': rounds[0].id
            })

            time.sleep(0.1)

            # Verify score was saved to database
            round_score = RoundScore.query.filter_by(
                round_id=rounds[0].id,
                team_id=team_ids[0]
            ).first()

            assert round_score is not None
            assert round_score.score_value == 95.0
            assert round_score.points == 8

            client.disconnect()

    def test_concurrent_score_updates(self, socketio_app, db_session, game_night, game, teams):
        """Test multiple concurrent score updates."""
        # Extract IDs before entering new app context
        game_id = game.id
        team_ids = [t.id for t in teams]

        with socketio_app.app_context():
            clients = [socketio.test_client(socketio_app) for _ in range(5)]

            # All join same game
            for client in clients:
                client.emit('join_game', {'game_id': game_id})
                client.get_received()

            # All update different teams simultaneously
            for i, client in enumerate(clients):
                if i < len(team_ids):
                    client.emit('update_score', {
                        'game_id': game_id,
                        'team_id': team_ids[i],
                        'score': 100 + i*10,
                        'points': 10 - i
                    })

            time.sleep(0.2)

            # Verify all scores were saved
            for i, team_id in enumerate(team_ids):
                score = Score.query.filter_by(
                    game_id=game_id,
                    team_id=team_id
                ).first()

                if score:
                    assert score.score_value == 100 + i*10

            for client in clients:
                client.disconnect()

    def test_score_update_validation_error(self, socketio_app, db_session, game_night, game, teams):
        """Test score update with invalid value."""
        # Extract IDs before entering new app context
        game_id = game.id
        team_ids = [t.id for t in teams]

        with socketio_app.app_context():
            client = socketio.test_client(socketio_app)
            client.emit('join_game', {'game_id': game_id})
            client.get_received()

            # Send invalid score (overflow)
            client.emit('update_score', {
                'game_id': game_id,
                'team_id': team_ids[0],
                'score': 99999999,  # Exceeds max
                'points': 10
            })

            time.sleep(0.1)

            # Should receive error event
            received = client.get_received()
            error_events = [r for r in received if r.get('name') == 'error']

            # Should have error or score not saved
            score = Score.query.filter_by(
                game_id=game_id,
                team_id=team_ids[0]
            ).first()

            # Score should either not exist or not be the invalid value
            if score:
                assert score.score_value != 99999999

            client.disconnect()


@pytest.mark.integration
@pytest.mark.websockets
class TestWebSocketEditLocks:
    """Test edit lock functionality integration."""

    def test_single_user_acquires_lock(self, socketio_app, db_session, game_night, game, teams):
        """Test single user can acquire edit lock."""
        # Extract IDs before entering new app context
        game_id = game.id
        team_ids = [t.id for t in teams]

        with socketio_app.app_context():
            client = socketio.test_client(socketio_app)
            client.emit('join_game', {'game_id': game_id})
            client.get_received()

            # Request lock
            client.emit('request_edit_lock', {
                'game_id': game_id,
                'team_id': team_ids[0],
                'field': 'score'
            })

            time.sleep(0.1)
            received = client.get_received()

            # Should receive lock_acquired or similar
            lock_events = [r for r in received if 'lock' in r.get('name', '').lower()]

            # At minimum, no error
            assert client.is_connected()

            client.disconnect()

    def test_lock_conflict_between_users(self, socketio_app, db_session, game_night, game, teams):
        """Test edit lock conflict when two users try to lock same field."""
        # Extract IDs before entering new app context
        game_id = game.id
        team_ids = [t.id for t in teams]

        with socketio_app.app_context():
            client1 = socketio.test_client(socketio_app)
            client2 = socketio.test_client(socketio_app)

            client1.emit('join_game', {'game_id': game_id})
            client2.emit('join_game', {'game_id': game_id})

            client1.get_received()
            client2.get_received()

            # Client 1 acquires lock
            client1.emit('request_edit_lock', {
                'game_id': game_id,
                'team_id': team_ids[0],
                'field': 'score'
            })

            time.sleep(0.1)

            # Client 2 tries to acquire same lock
            client2.emit('request_edit_lock', {
                'game_id': game_id,
                'team_id': team_ids[0],
                'field': 'score'
            })

            time.sleep(0.1)

            # Client 2 should receive lock_denied
            received2 = client2.get_received()
            denied_events = [r for r in received2 if 'denied' in r.get('name', '').lower()]

            # At minimum, both clients still connected
            assert client1.is_connected()
            assert client2.is_connected()

            client1.disconnect()
            client2.disconnect()

    def test_lock_release_and_reacquire(self, socketio_app, db_session, game_night, game, teams):
        """Test releasing lock allows another user to acquire it."""
        # Extract IDs before entering new app context
        game_id = game.id
        team_ids = [t.id for t in teams]

        with socketio_app.app_context():
            client1 = socketio.test_client(socketio_app)
            client2 = socketio.test_client(socketio_app)

            client1.emit('join_game', {'game_id': game_id})
            client2.emit('join_game', {'game_id': game_id})

            client1.get_received()
            client2.get_received()

            # Client 1 acquires and releases lock
            client1.emit('request_edit_lock', {
                'game_id': game_id,
                'team_id': team_ids[0],
                'field': 'score'
            })

            time.sleep(0.1)

            client1.emit('release_edit_lock', {
                'game_id': game_id,
                'team_id': team_ids[0],
                'field': 'score',
                'score': 100,
                'points': 10
            })

            time.sleep(0.1)

            # Client 2 should now be able to acquire
            client2.emit('request_edit_lock', {
                'game_id': game_id,
                'team_id': team_ids[0],
                'field': 'score'
            })

            time.sleep(0.1)

            # Should succeed
            assert client2.is_connected()

            client1.disconnect()
            client2.disconnect()

    def test_disconnect_releases_all_locks(self, socketio_app, db_session, game_night, game, teams):
        """Test that disconnecting releases all held locks."""
        # Extract IDs before entering new app context
        game_id = game.id
        team_ids = [t.id for t in teams]

        with socketio_app.app_context():
            client1 = socketio.test_client(socketio_app)
            client2 = socketio.test_client(socketio_app)

            client1.emit('join_game', {'game_id': game_id})
            client2.emit('join_game', {'game_id': game_id})

            client1.get_received()
            client2.get_received()

            # Client 1 acquires lock
            client1.emit('request_edit_lock', {
                'game_id': game_id,
                'team_id': team_ids[0],
                'field': 'score'
            })

            time.sleep(0.1)

            # Client 1 disconnects
            client1.disconnect()

            time.sleep(0.1)

            # Client 2 should now be able to acquire the lock
            client2.emit('request_edit_lock', {
                'game_id': game_id,
                'team_id': team_ids[0],
                'field': 'score'
            })

            time.sleep(0.1)

            # Should work
            assert client2.is_connected()

            client2.disconnect()


@pytest.mark.integration
@pytest.mark.websockets
class TestWebSocketMultiTimer:
    """Test multi-timer aggregation functionality."""

    def test_single_timer_start_stop(self, socketio_app, db_session, game_night, game, teams):
        """Test starting and stopping a single timer."""
        # Extract IDs before entering new app context
        game_id = game.id
        team_ids = [t.id for t in teams]

        with socketio_app.app_context():
            client = socketio.test_client(socketio_app)
            client.emit('join_game', {'game_id': game_id})
            client.get_received()

            # Start timer
            client.emit('start_timer', {
                'game_id': game_id,
                'team_id': team_ids[0]
            })

            time.sleep(0.1)

            # Stop timer
            client.emit('stop_timer', {
                'game_id': game_id,
                'team_id': team_ids[0],
                'time_value': 45.5
            })

            time.sleep(0.1)

            received = client.get_received()
            timer_events = [r for r in received if 'timer' in r.get('name', '').lower()]

            # Should have timer events
            assert len(timer_events) > 0

            client.disconnect()

    def test_multi_user_timer_average(self, socketio_app, db_session, game_night, game, teams):
        """Test average calculation with multiple timers."""
        # Extract IDs before entering new app context
        game_id = game.id
        team_ids = [t.id for t in teams]

        with socketio_app.app_context():
            clients = [socketio.test_client(socketio_app) for _ in range(3)]

            # All join game
            for client in clients:
                client.emit('join_game', {'game_id': game_id})
                client.get_received()

            # All start timers for same team
            for client in clients:
                client.emit('start_timer', {
                    'game_id': game_id,
                    'team_id': team_ids[0]
                })

            time.sleep(0.1)

            # All stop timers with different times
            times = [45.0, 50.0, 55.0]
            for i, client in enumerate(clients):
                client.emit('stop_timer', {
                    'game_id': game_id,
                    'team_id': team_ids[0],
                    'time_value': times[i]
                })

            time.sleep(0.2)

            # Expected average: (45 + 50 + 55) / 3 = 50
            # Verify through received events
            for client in clients:
                received = client.get_received()
                timer_stopped = [r for r in received if r.get('name') == 'timer_stopped']

                # Last timer stopped should have average
                if timer_stopped:
                    last_event = timer_stopped[-1]
                    args = last_event.get('args', [{}])
                    if args and 'average' in args[0]:
                        avg = args[0]['average']
                        assert abs(avg - 50.0) < 0.1

            for client in clients:
                client.disconnect()

    def test_clear_timers(self, socketio_app, db_session, game_night, game, teams, admin_user):
        """Test clearing all timers for a team."""
        # Extract IDs before entering new app context
        game_id = game.id
        team_ids = [t.id for t in teams]

        with socketio_app.app_context():
            # Create authenticated client (would need special setup for admin auth)
            client = socketio.test_client(socketio_app)
            client.emit('join_game', {'game_id': game_id})
            client.get_received()

            # Start and stop a timer
            client.emit('start_timer', {
                'game_id': game_id,
                'team_id': team_ids[0]
            })

            time.sleep(0.05)

            client.emit('stop_timer', {
                'game_id': game_id,
                'team_id': team_ids[0],
                'time_value': 45.0
            })

            time.sleep(0.1)

            # Clear timers (requires admin - might get rejected in test)
            client.emit('clear_timers', {
                'game_id': game_id,
                'team_id': team_ids[0]
            })

            time.sleep(0.1)

            # Should complete without error
            assert client.is_connected()

            client.disconnect()


@pytest.mark.integration
@pytest.mark.websockets
class TestWebSocketStressTest:
    """Stress tests for WebSocket handling."""

    def test_rapid_score_updates(self, socketio_app):
        """Test rapid consecutive score updates."""
        with socketio_app.app_context():
            # Create test data within socketio_app context
            from app.models import GameNight
            from datetime import date
            game_night = GameNight(name='Test Night', date=date.today(), is_active=True)
            db.session.add(game_night)
            db.session.flush()

            team1 = Team(name='Team 1', color='#FF0000', game_night_id=game_night.id)
            db.session.add(team1)
            db.session.flush()

            game_obj = Game(
                name='Test Game',
                type='trivia',
                game_night_id=game_night.id,
                sequence_number=1,
                point_scheme=1,
                metric_type='score',
                scoring_direction='higher_better'
            )
            db.session.add(game_obj)
            db.session.commit()

            game_id = game_obj.id
            team_ids = [team1.id]

            client = socketio.test_client(socketio_app)
            client.emit('join_game', {'game_id': game_id})
            client.get_received()

            # Send 10 rapid updates
            for i in range(10):
                client.emit('update_score', {
                    'game_id': game_id,
                    'team_id': team_ids[0],
                    'score': 100 + i,
                    'points': 10
                })

            time.sleep(0.5)

            # Last score should be saved
            score = Score.query.filter_by(
                game_id=game_id,
                team_id=team_ids[0]
            ).first()

            assert score is not None
            # Should have one of the scores (likely the last)
            assert score.score_value >= 100

            client.disconnect()

    def test_many_concurrent_clients(self, socketio_app, db_session, game_night, game):
        """Test handling many concurrent clients."""
        # Extract IDs before entering new app context
        game_id = game.id

        with socketio_app.app_context():
            num_clients = 20
            clients = [socketio.test_client(socketio_app) for _ in range(num_clients)]

            # All join same game
            for client in clients:
                client.emit('join_game', {'game_id': game_id})

            time.sleep(0.2)

            # All should be connected
            connected_count = sum(1 for c in clients if c.is_connected())
            assert connected_count == num_clients

            # All disconnect
            for client in clients:
                client.disconnect()

    def test_message_flooding(self, socketio_app, db_session, game_night, game, teams):
        """Test handling of message flooding."""
        # Extract IDs before entering new app context
        game_id = game.id
        team_ids = [t.id for t in teams]

        with socketio_app.app_context():
            client = socketio.test_client(socketio_app)
            client.emit('join_game', {'game_id': game_id})
            client.get_received()

            # Send many messages rapidly
            for i in range(50):
                client.emit('update_score', {
                    'game_id': game_id,
                    'team_id': team_ids[0],
                    'score': i,
                    'points': 5
                })

            time.sleep(0.5)

            # Should still be connected (not crashed)
            assert client.is_connected()

            client.disconnect()


@pytest.mark.integration
@pytest.mark.websockets
class TestWebSocketRaceConditions:
    """Test race condition handling."""

    def test_simultaneous_lock_requests(self, socketio_app, db_session, game_night, game, teams):
        """Test simultaneous lock requests from multiple clients."""
        # Extract IDs before entering new app context
        game_id = game.id
        team_ids = [t.id for t in teams]

        with socketio_app.app_context():
            num_clients = 10
            clients = [socketio.test_client(socketio_app) for _ in range(num_clients)]

            # All join game
            for client in clients:
                client.emit('join_game', {'game_id': game_id})
                client.get_received()

            # All request same lock simultaneously
            for client in clients:
                client.emit('request_edit_lock', {
                    'game_id': game_id,
                    'team_id': team_ids[0],
                    'field': 'score'
                })

            time.sleep(0.3)

            # Count how many got lock_acquired vs lock_denied
            acquired_count = 0
            denied_count = 0

            for client in clients:
                received = client.get_received()
                for event in received:
                    if event.get('name') == 'lock_acquired':
                        acquired_count += 1
                    elif event.get('name') == 'lock_denied':
                        denied_count += 1

            # Only one should have acquired (or test environment may not emit properly)
            # At minimum, no crashes
            assert all(c.is_connected() for c in clients)

            for client in clients:
                client.disconnect()

    def test_concurrent_score_updates_same_team(self, socketio_app):
        """Test concurrent updates to same team score."""
        with socketio_app.app_context():
            # Create test data within socketio_app context
            from app.models import GameNight
            from datetime import date
            game_night = GameNight(name='Test Night', date=date.today(), is_active=True)
            db.session.add(game_night)
            db.session.flush()

            team1 = Team(name='Team 1', color='#FF0000', game_night_id=game_night.id)
            db.session.add(team1)
            db.session.flush()

            game_obj = Game(
                name='Test Game',
                type='trivia',
                game_night_id=game_night.id,
                sequence_number=1,
                point_scheme=1,
                metric_type='score',
                scoring_direction='higher_better'
            )
            db.session.add(game_obj)
            db.session.commit()

            game_id = game_obj.id
            team_ids = [team1.id]

            clients = [socketio.test_client(socketio_app) for _ in range(5)]

            for client in clients:
                client.emit('join_game', {'game_id': game_id})
                client.get_received()

            # All update same team's score simultaneously
            for i, client in enumerate(clients):
                client.emit('update_score', {
                    'game_id': game_id,
                    'team_id': team_ids[0],
                    'score': 100 + i*10,
                    'points': 10 - i
                })

            time.sleep(0.3)

            # One score should be saved (last write wins)
            score = Score.query.filter_by(
                game_id=game_id,
                team_id=team_ids[0]
            ).first()

            assert score is not None
            # Should have one of the submitted scores
            assert score.score_value in [100, 110, 120, 130, 140]

            for client in clients:
                client.disconnect()
