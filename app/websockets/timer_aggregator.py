"""Timer Aggregator for multi-user timing."""
from datetime import datetime
from threading import Lock
from app import db
from app.models.timer_record import TimerRecord
from app.models.score import Score


class TimerAggregator:
    """Aggregates multiple timer values for a team."""

    def __init__(self):
        """Initialize the timer aggregator."""
        self.active_timers = {}  # {(game_id, team_id, user_id): {'start_time', 'display_name'}}
        self.timer_mutex = Lock()

    def start_timer(self, game_id, team_id, user_id, display_name):
        """Record timer start.

        Args:
            game_id: ID of the game
            team_id: ID of the team
            user_id: ID of the user starting the timer
            display_name: Display name of the user
        """
        with self.timer_mutex:
            key = (game_id, team_id, user_id)
            self.active_timers[key] = {
                'start_time': datetime.utcnow(),
                'display_name': display_name
            }

    def record_time(self, game_id, team_id, user_id, display_name, time_value):
        """Record a timer value to database.

        Args:
            game_id: ID of the game
            team_id: ID of the team
            user_id: ID of the user recording time
            display_name: Display name of the user
            time_value: Time value in seconds (float)

        Returns:
            TimerRecord: The created timer record
        """
        # Save to database
        timer_record = TimerRecord(
            game_id=game_id,
            team_id=team_id,
            user_id=user_id,
            user_display_name=display_name,
            time_value=time_value,
            is_active=True
        )
        db.session.add(timer_record)
        db.session.commit()

        # Remove from active timers
        with self.timer_mutex:
            key = (game_id, team_id, user_id)
            if key in self.active_timers:
                del self.active_timers[key]

        return timer_record

    def get_team_timers(self, game_id, team_id):
        """Get all active timer records for a team.

        Args:
            game_id: ID of the game
            team_id: ID of the team

        Returns:
            dict: {'times': list of float, 'timers': list of timer info dicts}
        """
        records = TimerRecord.query.filter_by(
            game_id=game_id,
            team_id=team_id,
            is_active=True
        ).all()

        return {
            'times': [r.time_value for r in records],
            'timers': [{
                'id': r.id,
                'user_id': r.user_id,
                'display_name': r.user_display_name,
                'time_value': r.time_value,
                'recorded_at': r.recorded_at.isoformat(),
                'is_admin': r.user_id.startswith('admin_') if r.user_id else False
            } for r in records]
        }

    def clear_team_timers(self, game_id, team_id):
        """Mark all timers for a team as inactive.

        Args:
            game_id: ID of the game
            team_id: ID of the team

        Returns:
            int: Number of timers cleared
        """
        count = TimerRecord.query.filter_by(
            game_id=game_id,
            team_id=team_id,
            is_active=True
        ).update({'is_active': False})
        db.session.commit()
        return count

    def calculate_average(self, game_id, team_id):
        """Calculate average time and update Score model.

        Args:
            game_id: ID of the game
            team_id: ID of the team

        Returns:
            float or None: Average time value, or None if no timers
        """
        timer_data = self.get_team_timers(game_id, team_id)

        if not timer_data['times']:
            return None

        avg_time = sum(timer_data['times']) / len(timer_data['times'])

        # Update Score model
        score = Score.query.filter_by(game_id=game_id, team_id=team_id).first()
        if score:
            score.multi_timer_avg = avg_time
            score.timer_count = len(timer_data['times'])
            score.score_value = avg_time  # Use average as the official score
            db.session.commit()
        else:
            # Create new score if it doesn't exist
            score = Score(
                game_id=game_id,
                team_id=team_id,
                score_value=avg_time,
                multi_timer_avg=avg_time,
                timer_count=len(timer_data['times']),
                points=0  # Points will be calculated later
            )
            db.session.add(score)
            db.session.commit()

        return avg_time

    def get_active_timers_for_game(self, game_id):
        """Get all active timers for a game.

        Args:
            game_id: ID of the game

        Returns:
            list: List of active timer info dicts
        """
        with self.timer_mutex:
            active = []
            for (gid, team_id, user_id), timer_info in self.active_timers.items():
                if gid == game_id:
                    active.append({
                        'team_id': team_id,
                        'user_id': user_id,
                        'display_name': timer_info['display_name'],
                        'start_time': timer_info['start_time'].isoformat()
                    })
            return active

    def stop_user_timers(self, user_id):
        """Stop all timers for a user (e.g., on disconnect).

        Args:
            user_id: ID of the user whose timers should be stopped

        Returns:
            list: List of stopped timer keys (game_id, team_id)
        """
        with self.timer_mutex:
            to_remove = [
                key for key in self.active_timers.keys()
                if key[2] == user_id  # user_id is third element in tuple
            ]
            stopped = []
            for key in to_remove:
                del self.active_timers[key]
                stopped.append({
                    'game_id': key[0],
                    'team_id': key[1]
                })
            return stopped
