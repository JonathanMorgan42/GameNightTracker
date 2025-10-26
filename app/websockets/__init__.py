"""WebSocket event handlers for real-time collaborative scoring."""
from flask_socketio import emit, join_room, leave_room, disconnect
from flask_login import current_user
from flask import request, session
from app.websockets.lock_manager import EditLockManager
from app.websockets.timer_aggregator import TimerAggregator
from app.models.score import Score
from app.models.game import Game
from app.models.round import Round
from app.models.round_score import RoundScore
from app import db
from app.utils.logger import get_logger
from app.utils.validators import (
    validate_numeric_range,
    SCORE_VALUE_MIN, SCORE_VALUE_MAX
)

logger = get_logger(__name__)

# Initialize managers
lock_manager = EditLockManager()
timer_aggregator = TimerAggregator()

# Store per-connection user data
_connection_data = {}


def serialize_scores(scores_dict):
    """Serialize scores dictionary for transmission."""
    result = {}
    for team_id, score in scores_dict.items():
        if isinstance(score, Score):
            result[team_id] = {
                'score_value': score.score_value,
                'points': score.points,
                'multi_timer_avg': score.multi_timer_avg,
                'timer_count': score.timer_count
            }
        else:
            result[team_id] = score
    return result


def register_handlers(socketio):
    """Register all WebSocket event handlers."""

    @socketio.on('connect')
    def handle_connect(auth=None):
        """Handle client connection."""
        session_id = request.sid

        # Get user identity
        if current_user.is_authenticated:
            user_id = f"admin_{current_user.id}"
            display_name = "admin"  # Simplified: just "admin"
        else:
            user_id = f"anon_{session_id}"
            display_name = "Player"  # Simplified: just "Player"

        # Store in connection data dictionary
        _connection_data[session_id] = {
            'user_id': user_id,
            'display_name': display_name
        }

        emit('connected', {
            'user_id': user_id,
            'display_name': display_name
        })

    @socketio.on('join_game')
    def handle_join_game(data):
        """Join a game room for real-time updates."""
        game_id = data.get('game_id')
        round_id = data.get('round_id')  # Optional round ID for round-based games
        room = f"game_{game_id}"
        join_room(room)

        # Determine if this is a round-based game
        game = Game.query.get(game_id)
        scores_dict = {}

        if game and game.has_rounds and round_id:
            # Send round-specific scores
            round_scores = RoundScore.query.filter_by(round_id=round_id).all()
            scores_dict = {rs.team_id: {
                'score_value': rs.score_value,
                'points': rs.points,
                'multi_timer_avg': rs.multi_timer_avg,
                'timer_count': rs.timer_count
            } for rs in round_scores}
        else:
            # Send regular game scores
            scores = Score.query.filter_by(game_id=game_id).all()
            scores_dict = {score.team_id: score for score in scores}

        active_locks = lock_manager.get_game_locks(game_id)

        emit('game_state', {
            'scores': serialize_scores(scores_dict),
            'locks': active_locks,
            'round_id': round_id
        })

        # Get connection data
        conn_data = _connection_data.get(request.sid, {})

        # Notify others
        emit('user_joined', {
            'user_id': conn_data.get('user_id'),
            'display_name': conn_data.get('display_name')
        }, room=room, skip_sid=request.sid)

    @socketio.on('leave_game')
    def handle_leave_game(data):
        """Leave a game room."""
        game_id = data.get('game_id')
        room = f"game_{game_id}"
        leave_room(room)

        # Get connection data
        conn_data = _connection_data.get(request.sid, {})

        # Notify others
        emit('user_left', {
            'user_id': conn_data.get('user_id'),
            'display_name': conn_data.get('display_name')
        }, room=room, skip_sid=request.sid)

    @socketio.on('request_edit_lock')
    def handle_request_lock(data):
        """Request exclusive lock on a score field."""
        game_id = data.get('game_id')
        team_id = data.get('team_id')
        field = data.get('field')  # Client sends 'field', not 'field_name'

        # Get connection data
        conn_data = _connection_data.get(request.sid, {})
        user_id = conn_data.get('user_id')
        display_name = conn_data.get('display_name')

        # Try to acquire lock
        lock_result = lock_manager.acquire_lock(
            game_id, team_id, field, user_id, display_name
        )

        if lock_result['success']:
            # Notify requester
            emit('lock_acquired', {
                'game_id': game_id,
                'team_id': team_id,
                'field': field
            })

            # Notify room
            room = f"game_{game_id}"
            emit('field_locked', {
                'team_id': team_id,
                'field': field,
                'user_id': user_id,
                'display_name': display_name
            }, room=room, skip_sid=request.sid)
        else:
            emit('lock_denied', {
                'team_id': team_id,
                'field': field,
                'locked_by': lock_result['locked_by']
            })

    @socketio.on('release_edit_lock')
    def handle_release_lock(data):
        """Release lock on a score field and save/broadcast final score."""
        game_id = data.get('game_id')
        team_id = data.get('team_id')
        field = data.get('field')
        score = data.get('score')
        points = data.get('points')

        # Get connection data
        conn_data = _connection_data.get(request.sid, {})
        user_id = conn_data.get('user_id')

        # Save score to database if provided
        if score is not None and points is not None:
            try:
                score_obj = Score.query.filter_by(game_id=game_id, team_id=team_id).first()
                if score_obj:
                    score_obj.score_value = score
                    score_obj.points = points
                else:
                    score_obj = Score(
                        game_id=game_id,
                        team_id=team_id,
                        score_value=score,
                        points=points
                    )
                    db.session.add(score_obj)

                db.session.commit()
            except Exception as e:
                db.session.rollback()
                logger.error(f"Error saving score on unlock for game_id={game_id}, team_id={team_id}: {e}", exc_info=True)

        # Release the lock
        lock_manager.release_lock(game_id, team_id, field, user_id)

        # Broadcast unlock with final score
        room = f"game_{game_id}"
        emit('field_unlocked', {
            'team_id': team_id,
            'field': field,
            'score': score,
            'points': points,
            'updated_by': conn_data.get('display_name')
        }, room=room)

    @socketio.on('update_score')
    def handle_update_score(data):
        """Handle real-time score update (supports both regular and round-based games)."""
        game_id = data.get('game_id')
        team_id = data.get('team_id')
        score = data.get('score')  # Client sends 'score', not 'score_value'
        points = data.get('points')
        round_id = data.get('round_id')  # Optional for round-based games

        # Get connection data
        conn_data = _connection_data.get(request.sid, {})

        # Validate score value
        is_valid, error = validate_numeric_range(
            score, 'Score value', SCORE_VALUE_MIN, SCORE_VALUE_MAX, allow_none=True
        )
        if not is_valid:
            emit('error', {'message': error})
            logger.warning(f"Invalid score value from {conn_data.get('display_name')}: {error}")
            return

        # Validate points value
        is_valid, error = validate_numeric_range(
            points, 'Points', SCORE_VALUE_MIN, SCORE_VALUE_MAX, allow_none=True
        )
        if not is_valid:
            emit('error', {'message': error})
            logger.warning(f"Invalid points value from {conn_data.get('display_name')}: {error}")
            return

        # Update database
        try:
            # Check if this is a round-based game
            game = Game.query.get(game_id)

            if game and game.has_rounds and round_id:
                # Update round score
                round_score = RoundScore.query.filter_by(round_id=round_id, team_id=team_id).first()
                if round_score:
                    round_score.score_value = score
                    round_score.points = points
                else:
                    round_score = RoundScore(
                        round_id=round_id,
                        team_id=team_id,
                        score_value=score,
                        points=points
                    )
                    db.session.add(round_score)

                # Sync cumulative scores to main Score table
                from app.services.score_service import ScoreService
                db.session.commit()  # Commit round score first
                ScoreService.sync_round_scores_to_main_scores(game_id)
            else:
                # Update regular score
                score_obj = Score.query.filter_by(game_id=game_id, team_id=team_id).first()
                if score_obj:
                    score_obj.score_value = score
                    score_obj.points = points
                else:
                    score_obj = Score(
                        game_id=game_id,
                        team_id=team_id,
                        score_value=score,
                        points=points
                    )
                    db.session.add(score_obj)

                db.session.commit()

            # Broadcast update
            room = f"game_{game_id}"
            emit('score_updated', {
                'team_id': team_id,
                'score': score,
                'points': points,
                'round_id': round_id,
                'updated_by': conn_data.get('display_name')
            }, room=room)

        except Exception as e:
            db.session.rollback()
            emit('error', {'message': str(e)})
            logger.error(f"Database error updating score: {e}", exc_info=True)

    @socketio.on('start_timer')
    def handle_start_timer(data):
        """User started their timer for a team."""
        game_id = data.get('game_id')
        team_id = data.get('team_id')

        # Get connection data
        conn_data = _connection_data.get(request.sid, {})
        user_id = conn_data.get('user_id')
        display_name = conn_data.get('display_name')

        timer_aggregator.start_timer(game_id, team_id, user_id, display_name)

        # Notify room
        room = f"game_{game_id}"
        emit('timer_started', {
            'team_id': team_id,
            'user_id': user_id,
            'display_name': display_name
        }, room=room)

    @socketio.on('stop_timer')
    def handle_stop_timer(data):
        """User stopped their timer."""
        game_id = data.get('game_id')
        team_id = data.get('team_id')
        time_value = data.get('time_value')  # in seconds

        # Get connection data
        conn_data = _connection_data.get(request.sid, {})
        user_id = conn_data.get('user_id')
        display_name = conn_data.get('display_name')

        # Validate time value (reasonable range: 0 to 999,999 seconds ~= 11.5 days)
        is_valid, error = validate_numeric_range(
            time_value, 'Timer value', 0, 999999, allow_none=False
        )
        if not is_valid:
            emit('error', {'message': error})
            logger.warning(f"Invalid timer value from {display_name}: {error}")
            return

        # Record timer value
        try:
            timer_aggregator.record_time(
                game_id, team_id, user_id, display_name, time_value
            )
        except Exception as e:
            emit('error', {'message': 'Failed to record timer value'})
            logger.error(f"Error recording timer: {e}", exc_info=True)
            return

        # Get all active timers for this team
        timer_data = timer_aggregator.get_team_timers(game_id, team_id)

        # Calculate average
        if timer_data['times']:
            avg_time = sum(timer_data['times']) / len(timer_data['times'])
        else:
            avg_time = time_value

        # Broadcast timer update with full timer details
        room = f"game_{game_id}"
        emit('timer_stopped', {
            'team_id': team_id,
            'user_id': user_id,
            'display_name': display_name,
            'time': time_value,
            'average': avg_time,
            'all_times': timer_data['times'],
            'timer_count': len(timer_data['times']),
            'timers': timer_data['timers']  # Include full timer details with IDs
        }, room=room)

    @socketio.on('clear_timers')
    def handle_clear_timers(data):
        """Clear all timer records for a team."""
        game_id = data.get('game_id')
        team_id = data.get('team_id')

        # Only admin can clear timers
        if not current_user.is_authenticated:
            emit('error', {'message': 'Only admins can clear timers'})
            return

        count = timer_aggregator.clear_team_timers(game_id, team_id)

        room = f"game_{game_id}"
        emit('timers_cleared', {
            'team_id': team_id,
            'count': count
        }, room=room)

    @socketio.on('disconnect')
    def handle_disconnect():
        """Handle client disconnection - release all locks."""
        # Get connection data
        conn_data = _connection_data.get(request.sid, {})
        user_id = conn_data.get('user_id')

        if user_id:
            # Release all locks
            released_locks = lock_manager.release_all_user_locks(user_id)

            # Notify rooms of released locks
            for lock in released_locks:
                room = f"game_{lock['game_id']}"
                emit('field_unlocked', {
                    'team_id': lock['team_id'],
                    'field': lock['field_name']
                }, room=room)

            # Stop all active timers
            stopped_timers = timer_aggregator.stop_user_timers(user_id)

            # Notify rooms of stopped timers
            for timer in stopped_timers:
                room = f"game_{timer['game_id']}"
                emit('timer_stopped', {
                    'team_id': timer['team_id'],
                    'user_id': user_id
                }, room=room)

        # Clean up connection data
        if request.sid in _connection_data:
            del _connection_data[request.sid]
