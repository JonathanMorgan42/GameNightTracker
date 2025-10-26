"""Edit Lock Manager for real-time collaborative scoring."""
from datetime import datetime, timedelta, timezone
from threading import Lock
from collections import defaultdict


class EditLockManager:
    """Manages edit locks for score fields (in-memory)."""

    def __init__(self, lock_timeout_minutes=5):
        """Initialize the lock manager.

        Args:
            lock_timeout_minutes: Minutes before a lock automatically expires
        """
        # In-memory storage (for development/single-instance)
        self.locks = {}  # {(game_id, team_id, field): {'user_id', 'display_name', 'locked_at'}}
        self.lock_mutex = Lock()

        # Lock timeout (auto-release after N minutes of inactivity)
        self.lock_timeout = timedelta(minutes=lock_timeout_minutes)

    def acquire_lock(self, game_id, team_id, field_name, user_id, display_name):
        """Attempt to acquire lock on a field.

        Args:
            game_id: ID of the game
            team_id: ID of the team
            field_name: Name of the field being locked
            user_id: ID of the user requesting lock
            display_name: Display name of the user

        Returns:
            dict: {'success': bool, 'locked_by': str (if failed)}
        """
        with self.lock_mutex:
            key = (game_id, team_id, field_name)

            # Check if already locked
            if key in self.locks:
                existing_lock = self.locks[key]

                # Check if same user
                if existing_lock['user_id'] == user_id:
                    # Refresh lock timestamp
                    existing_lock['locked_at'] = datetime.now(timezone.utc)
                    return {'success': True}

                # Check if lock has expired
                if datetime.now(timezone.utc) - existing_lock['locked_at'] > self.lock_timeout:
                    # Lock expired, can override
                    pass
                else:
                    return {
                        'success': False,
                        'locked_by': existing_lock['display_name']
                    }

            # Acquire lock
            self.locks[key] = {
                'user_id': user_id,
                'display_name': display_name,
                'locked_at': datetime.now(timezone.utc)
            }

            return {'success': True}

    def release_lock(self, game_id, team_id, field_name, user_id):
        """Release a lock if owned by user.

        Args:
            game_id: ID of the game
            team_id: ID of the team
            field_name: Name of the field being unlocked
            user_id: ID of the user releasing lock

        Returns:
            bool: True if lock was released, False otherwise
        """
        with self.lock_mutex:
            key = (game_id, team_id, field_name)

            if key in self.locks and self.locks[key]['user_id'] == user_id:
                del self.locks[key]
                return True
            return False

    def has_lock(self, game_id, team_id, field_name, user_id):
        """Check if user has lock.

        Args:
            game_id: ID of the game
            team_id: ID of the team
            field_name: Name of the field
            user_id: ID of the user

        Returns:
            bool: True if user has the lock
        """
        key = (game_id, team_id, field_name)
        if key in self.locks:
            return self.locks[key]['user_id'] == user_id
        return False

    def release_all_user_locks(self, user_id):
        """Release all locks held by a user (on disconnect).

        Args:
            user_id: ID of the user whose locks should be released

        Returns:
            list: List of released locks with game_id, team_id, field_name
        """
        released = []
        with self.lock_mutex:
            to_remove = [
                key for key, lock in self.locks.items()
                if lock['user_id'] == user_id
            ]
            for key in to_remove:
                game_id, team_id, field_name = key
                del self.locks[key]
                released.append({
                    'game_id': game_id,
                    'team_id': team_id,
                    'field_name': field_name
                })
        return released

    def get_game_locks(self, game_id):
        """Get all active locks for a game.

        Args:
            game_id: ID of the game

        Returns:
            list: List of lock dictionaries with team_id, field_name, user info
        """
        locks = []
        with self.lock_mutex:
            for (gid, team_id, field_name), lock in self.locks.items():
                if gid == game_id:
                    locks.append({
                        'team_id': team_id,
                        'field_name': field_name,
                        'user_id': lock['user_id'],
                        'display_name': lock['display_name']
                    })
        return locks

    def cleanup_expired_locks(self):
        """Remove all expired locks. Can be called periodically.

        Returns:
            int: Number of locks cleaned up
        """
        with self.lock_mutex:
            expired_keys = [
                key for key, lock in self.locks.items()
                if datetime.now(timezone.utc) - lock['locked_at'] > self.lock_timeout
            ]
            for key in expired_keys:
                del self.locks[key]
            return len(expired_keys)
