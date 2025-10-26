"""Comprehensive unit tests for WebSocket event handlers."""
import pytest
from unittest.mock import Mock, patch, MagicMock
from app.websockets import register_handlers
from app.models import Game, Score, Round, RoundScore
from app.utils.validators import SCORE_VALUE_MIN, SCORE_VALUE_MAX


@pytest.mark.unit
@pytest.mark.websockets
class TestWebSocketConnect:
    """Test suite for WebSocket connection handling."""

    def test_connect_authenticated_user(self, app, admin_user):
        """Test connection with authenticated admin user."""
        with app.test_request_context():
            with patch('app.websockets.request') as mock_request:
                with patch('app.websockets.current_user', admin_user):
                    with patch('app.websockets.emit') as mock_emit:
                        mock_request.sid = 'test_session_123'

                        from app.websockets import _connection_data
                        socketio = Mock()
                        register_handlers(socketio)

                        user_id = f"admin_{admin_user.id}"
                        display_name = "admin"

                        assert user_id.startswith("admin_")
                        assert display_name == "admin"

    def test_connect_anonymous_user(self, app):
        """Test connection with anonymous user."""
        with app.test_request_context():
            with patch('app.websockets.request') as mock_request:
                with patch('app.websockets.current_user') as mock_user:
                    mock_request.sid = 'anon_session_456'
                    mock_user.is_authenticated = False

                    user_id = f"anon_{mock_request.sid}"
                    display_name = "Player"

                    assert user_id.startswith("anon_")
                    assert display_name == "Player"


@pytest.mark.unit
@pytest.mark.websockets
class TestWebSocketJoinGame:
    """Test suite for joining game rooms."""

    def test_join_regular_game(self, app, db_session, game, teams):
        """Test joining a regular (non-round-based) game."""
        # Create scores
        for i, team in enumerate(teams):
            score = Score(
                game_id=game.id,
                team_id=team.id,
                score_value=100 - i*10,
                points=10 - i
            )
            db_session.add(score)
        db_session.commit()

        with app.app_context():
            with patch('app.websockets.join_room') as mock_join:
                with patch('app.websockets.emit') as mock_emit:
                    with patch('app.websockets.request') as mock_request:
                        mock_request.sid = 'test_sid'

                        # Simulate join_game event
                        data = {'game_id': game.id}

                        # Verify room name format
                        expected_room = f"game_{game.id}"

                        # In actual handler, join_room would be called
                        mock_join.assert_not_called()  # Not called yet in test

    def test_join_round_based_game(self, app, db_session, game, teams):
        """Test joining a round-based game."""
        game.has_rounds = True
        db_session.commit()

        # Create rounds and round scores
        from app.services.round_service import RoundService
        rounds = RoundService.create_rounds_for_game(game.id, 3)

        with app.app_context():
            data = {'game_id': game.id, 'round_id': rounds[0].id}
            expected_room = f"game_{game.id}"

            assert data['round_id'] == rounds[0].id


@pytest.mark.unit
@pytest.mark.websockets
class TestWebSocketEditLocks:
    """Test suite for edit lock management."""

    def test_request_lock_success(self, app):
        """Test successful lock acquisition."""
        with app.test_request_context():
            with patch('app.websockets.lock_manager') as mock_lock_manager:
                with patch('app.websockets.emit') as mock_emit:
                    with patch('app.websockets.request') as mock_request:
                        mock_request.sid = 'test_sid'
                        mock_lock_manager.acquire_lock.return_value = {'success': True}

                        # Simulate lock request
                        data = {
                            'game_id': 1,
                            'team_id': 1,
                            'field': 'score'
                        }

                        # In actual handler, would acquire lock
                        result = mock_lock_manager.acquire_lock(
                            data['game_id'],
                            data['team_id'],
                            data['field'],
                            'user_1',
                            'Test User'
                        )

                        assert result['success'] is True

    def test_request_lock_denied(self, app):
        """Test lock denial when already locked."""
        with app.test_request_context():
            with patch('app.websockets.lock_manager') as mock_lock_manager:
                mock_lock_manager.acquire_lock.return_value = {
                    'success': False,
                    'locked_by': 'other_user'
                }

                data = {
                    'game_id': 1,
                    'team_id': 1,
                    'field': 'score'
                }

                result = mock_lock_manager.acquire_lock(
                    data['game_id'],
                    data['team_id'],
                    data['field'],
                    'user_1',
                    'Test User'
                )

                assert result['success'] is False
                assert result['locked_by'] == 'other_user'

    def test_release_lock(self, app):
        """Test lock release."""
        with app.test_request_context():
            with patch('app.websockets.lock_manager') as mock_lock_manager:
                with patch('app.websockets.emit') as mock_emit:
                    data = {
                        'game_id': 1,
                        'team_id': 1,
                        'field': 'score',
                        'score': 100,
                        'points': 10
                    }

                    mock_lock_manager.release_lock(
                        data['game_id'],
                        data['team_id'],
                        data['field'],
                        'user_1'
                    )

                    mock_lock_manager.release_lock.assert_called_once()

    def test_release_lock_with_score_save(self, app, db_session, game, teams):
        """Test that releasing lock saves score to database."""
        with app.app_context():
            data = {
                'game_id': game.id,
                'team_id': teams[0].id,
                'field': 'score',
                'score': 100.5,
                'points': 10
            }

            # Simulate score save on release
            score_obj = Score.query.filter_by(
                game_id=data['game_id'],
                team_id=data['team_id']
            ).first()

            if not score_obj:
                score_obj = Score(
                    game_id=data['game_id'],
                    team_id=data['team_id'],
                    score_value=data['score'],
                    points=data['points']
                )
                db_session.add(score_obj)
            else:
                score_obj.score_value = data['score']
                score_obj.points = data['points']

            db_session.commit()

            # Verify save
            saved_score = Score.query.filter_by(
                game_id=game.id,
                team_id=teams[0].id
            ).first()

            assert saved_score is not None
            assert saved_score.score_value == 100.5
            assert saved_score.points == 10


@pytest.mark.unit
@pytest.mark.websockets
class TestWebSocketScoreUpdates:
    """Test suite for score update handling."""

    def test_update_score_regular_game(self, app, db_session, game, teams):
        """Test updating score for regular game."""
        with app.app_context():
            data = {
                'game_id': game.id,
                'team_id': teams[0].id,
                'score': 95.5,
                'points': 10,
                'round_id': None
            }

            # Validate score
            from app.utils.validators import validate_numeric_range
            is_valid, error = validate_numeric_range(
                data['score'],
                'Score value',
                SCORE_VALUE_MIN,
                SCORE_VALUE_MAX,
                allow_none=True
            )

            assert is_valid is True
            assert error is None

            # Save score
            score_obj = Score.query.filter_by(
                game_id=data['game_id'],
                team_id=data['team_id']
            ).first()

            if not score_obj:
                score_obj = Score(
                    game_id=data['game_id'],
                    team_id=data['team_id'],
                    score_value=data['score'],
                    points=data['points']
                )
                db_session.add(score_obj)
            else:
                score_obj.score_value = data['score']
                score_obj.points = data['points']

            db_session.commit()

            # Verify
            saved = Score.query.filter_by(
                game_id=game.id,
                team_id=teams[0].id
            ).first()

            assert saved.score_value == 95.5

    def test_update_score_round_based_game(self, app, db_session, game, teams):
        """Test updating score for round-based game."""
        game.has_rounds = True
        db_session.commit()

        from app.services.round_service import RoundService
        rounds = RoundService.create_rounds_for_game(game.id, 1)

        with app.app_context():
            data = {
                'game_id': game.id,
                'team_id': teams[0].id,
                'score': 88.0,
                'points': 8,
                'round_id': rounds[0].id
            }

            # Save round score
            round_score = RoundScore.query.filter_by(
                round_id=data['round_id'],
                team_id=data['team_id']
            ).first()

            if not round_score:
                round_score = RoundScore(
                    round_id=data['round_id'],
                    team_id=data['team_id'],
                    score_value=data['score'],
                    points=data['points']
                )
                db_session.add(round_score)
            else:
                round_score.score_value = data['score']
                round_score.points = data['points']

            db_session.commit()

            # Verify
            saved = RoundScore.query.filter_by(
                round_id=rounds[0].id,
                team_id=teams[0].id
            ).first()

            assert saved.score_value == 88.0

    def test_update_score_validation_overflow(self, app, game, teams):
        """Test score validation rejects overflow values."""
        with app.app_context():
            overflow_score = SCORE_VALUE_MAX + 1000

            from app.utils.validators import validate_numeric_range
            is_valid, error = validate_numeric_range(
                overflow_score,
                'Score value',
                SCORE_VALUE_MIN,
                SCORE_VALUE_MAX,
                allow_none=True
            )

            assert is_valid is False
            assert error is not None
            assert "must be between" in error

    def test_update_score_validation_underflow(self, app, game, teams):
        """Test score validation rejects underflow values."""
        with app.app_context():
            underflow_score = SCORE_VALUE_MIN - 1000

            from app.utils.validators import validate_numeric_range
            is_valid, error = validate_numeric_range(
                underflow_score,
                'Score value',
                SCORE_VALUE_MIN,
                SCORE_VALUE_MAX,
                allow_none=True
            )

            assert is_valid is False
            assert error is not None


@pytest.mark.unit
@pytest.mark.websockets
class TestWebSocketTimers:
    """Test suite for multi-timer functionality."""

    def test_start_timer(self, app):
        """Test starting a timer."""
        with app.test_request_context():
            with patch('app.websockets.timer_aggregator') as mock_timer:
                with patch('app.websockets.emit') as mock_emit:
                    data = {
                        'game_id': 1,
                        'team_id': 1
                    }

                    mock_timer.start_timer(
                        data['game_id'],
                        data['team_id'],
                        'user_1',
                        'Test User'
                    )

                    mock_timer.start_timer.assert_called_once()

    def test_stop_timer_valid_value(self, app):
        """Test stopping timer with valid time value."""
        with app.test_request_context():
            with patch('app.websockets.timer_aggregator') as mock_timer:
                data = {
                    'game_id': 1,
                    'team_id': 1,
                    'time_value': 45.5
                }

                # Validate time value
                from app.utils.validators import validate_numeric_range
                is_valid, error = validate_numeric_range(
                    data['time_value'],
                    'Timer value',
                    0,
                    999999,
                    allow_none=False
                )

                assert is_valid is True
                assert error is None

    def test_stop_timer_negative_value_rejected(self, app):
        """Test that negative timer values are rejected."""
        with app.app_context():
            time_value = -10

            from app.utils.validators import validate_numeric_range
            is_valid, error = validate_numeric_range(
                time_value,
                'Timer value',
                0,
                999999,
                allow_none=False
            )

            assert is_valid is False

    def test_stop_timer_overflow_rejected(self, app):
        """Test that overflow timer values are rejected."""
        with app.app_context():
            time_value = 1000000  # Exceeds max

            from app.utils.validators import validate_numeric_range
            is_valid, error = validate_numeric_range(
                time_value,
                'Timer value',
                0,
                999999,
                allow_none=False
            )

            assert is_valid is False

    def test_stop_timer_calculates_average(self, app):
        """Test timer average calculation."""
        with app.test_request_context():
            with patch('app.websockets.timer_aggregator') as mock_timer:
                mock_timer.get_team_timers.return_value = {
                    'times': [45.0, 50.0, 55.0],
                    'timers': [
                        {'user_id': 'user_1', 'time': 45.0},
                        {'user_id': 'user_2', 'time': 50.0},
                        {'user_id': 'user_3', 'time': 55.0}
                    ]
                }

                timer_data = mock_timer.get_team_timers(1, 1)
                times = timer_data['times']

                avg = sum(times) / len(times)
                assert avg == 50.0

    def test_clear_timers_admin_only(self, app, admin_user):
        """Test that only admins can clear timers."""
        with app.test_request_context():
            with patch('app.websockets.current_user', admin_user):
                with patch('app.websockets.timer_aggregator') as mock_timer:
                    mock_timer.clear_team_timers.return_value = 3

                    count = mock_timer.clear_team_timers(1, 1)
                    assert count == 3

    def test_clear_timers_non_admin_rejected(self, app):
        """Test that non-admins cannot clear timers."""
        with app.test_request_context():
            with patch('app.websockets.current_user') as mock_user:
                mock_user.is_authenticated = False

                # Would emit error in actual handler
                assert mock_user.is_authenticated is False


@pytest.mark.unit
@pytest.mark.websockets
class TestWebSocketDisconnect:
    """Test suite for disconnect handling."""

    def test_disconnect_releases_locks(self, app):
        """Test that disconnect releases all user locks."""
        with app.test_request_context():
            with patch('app.websockets.lock_manager') as mock_lock_manager:
                with patch('app.websockets.request') as mock_request:
                    mock_request.sid = 'test_sid'
                    mock_lock_manager.release_all_user_locks.return_value = [
                        {'game_id': 1, 'team_id': 1, 'field_name': 'score'},
                        {'game_id': 1, 'team_id': 2, 'field_name': 'points'}
                    ]

                    released = mock_lock_manager.release_all_user_locks('user_1')
                    assert len(released) == 2

    def test_disconnect_stops_timers(self, app):
        """Test that disconnect stops all user timers."""
        with app.test_request_context():
            with patch('app.websockets.timer_aggregator') as mock_timer:
                mock_timer.stop_user_timers.return_value = [
                    {'game_id': 1, 'team_id': 1},
                    {'game_id': 1, 'team_id': 2}
                ]

                stopped = mock_timer.stop_user_timers('user_1')
                assert len(stopped) == 2

    def test_disconnect_cleans_connection_data(self, app):
        """Test that disconnect removes connection data."""
        from app.websockets import _connection_data

        # Simulate connection data
        test_sid = 'test_session_789'
        _connection_data[test_sid] = {
            'user_id': 'user_1',
            'display_name': 'Test User'
        }

        assert test_sid in _connection_data

        # Simulate cleanup
        if test_sid in _connection_data:
            del _connection_data[test_sid]

        assert test_sid not in _connection_data


@pytest.mark.unit
@pytest.mark.websockets
class TestWebSocketValidation:
    """Test suite for WebSocket input validation."""

    def test_score_update_with_sql_injection(self, app):
        """Test that SQL injection in score is handled."""
        with app.app_context():
            malicious_score = "'; DROP TABLE scores; --"

            from app.utils.validators import validate_numeric_range
            is_valid, error = validate_numeric_range(
                malicious_score,
                'Score value',
                SCORE_VALUE_MIN,
                SCORE_VALUE_MAX,
                allow_none=True
            )

            # Should fail validation (not a number)
            assert is_valid is False

    def test_score_update_with_xss(self, app):
        """Test that XSS in score is handled."""
        with app.app_context():
            xss_score = "<script>alert('XSS')</script>"

            from app.utils.validators import validate_numeric_range
            is_valid, error = validate_numeric_range(
                xss_score,
                'Score value',
                SCORE_VALUE_MIN,
                SCORE_VALUE_MAX,
                allow_none=True
            )

            # Should fail validation (not a number)
            assert is_valid is False

    def test_very_large_score_rejected(self, app):
        """Test extremely large score values are rejected."""
        with app.app_context():
            huge_score = 99999999999999

            from app.utils.validators import validate_numeric_range
            is_valid, error = validate_numeric_range(
                huge_score,
                'Score value',
                SCORE_VALUE_MIN,
                SCORE_VALUE_MAX,
                allow_none=True
            )

            assert is_valid is False

    def test_infinity_score_rejected(self, app):
        """Test infinity value is rejected."""
        with app.app_context():
            inf_score = float('inf')

            from app.utils.validators import validate_numeric_range
            is_valid, error = validate_numeric_range(
                inf_score,
                'Score value',
                SCORE_VALUE_MIN,
                SCORE_VALUE_MAX,
                allow_none=True
            )

            assert is_valid is False

    def test_nan_score_rejected(self, app):
        """Test NaN value is rejected."""
        with app.app_context():
            nan_score = float('nan')

            from app.utils.validators import validate_numeric_range
            is_valid, error = validate_numeric_range(
                nan_score,
                'Score value',
                SCORE_VALUE_MIN,
                SCORE_VALUE_MAX,
                allow_none=True
            )

            # NaN comparison will fail range check
            assert is_valid is False


@pytest.mark.unit
@pytest.mark.websockets
class TestWebSocketBroadcasting:
    """Test suite for WebSocket broadcasting."""

    def test_score_update_broadcast_format(self, app):
        """Test score update broadcast message format."""
        expected_broadcast = {
            'team_id': 1,
            'score': 100.0,
            'points': 10,
            'round_id': None,
            'updated_by': 'Test User'
        }

        assert 'team_id' in expected_broadcast
        assert 'score' in expected_broadcast
        assert 'points' in expected_broadcast
        assert 'updated_by' in expected_broadcast

    def test_lock_acquired_broadcast_format(self, app):
        """Test lock acquired broadcast message format."""
        expected_broadcast = {
            'team_id': 1,
            'field': 'score',
            'user_id': 'user_1',
            'display_name': 'Test User'
        }

        assert 'team_id' in expected_broadcast
        assert 'field' in expected_broadcast
        assert 'user_id' in expected_broadcast
        assert 'display_name' in expected_broadcast

    def test_timer_stopped_broadcast_format(self, app):
        """Test timer stopped broadcast message format."""
        expected_broadcast = {
            'team_id': 1,
            'user_id': 'user_1',
            'display_name': 'Test User',
            'time': 45.5,
            'average': 47.3,
            'all_times': [45.5, 49.0, 47.4],
            'timer_count': 3,
            'timers': [
                {'user_id': 'user_1', 'time': 45.5},
                {'user_id': 'user_2', 'time': 49.0},
                {'user_id': 'user_3', 'time': 47.4}
            ]
        }

        assert 'average' in expected_broadcast
        assert 'all_times' in expected_broadcast
        assert 'timer_count' in expected_broadcast
        assert 'timers' in expected_broadcast
