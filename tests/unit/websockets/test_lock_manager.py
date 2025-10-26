"""Unit tests for EditLockManager."""
import pytest
from datetime import datetime, timedelta, timezone
from app.websockets.lock_manager import EditLockManager


class TestEditLockManager:
    """Test suite for EditLockManager."""

    def setup_method(self):
        """Set up test fixtures."""
        self.manager = EditLockManager(lock_timeout_minutes=1)

    def test_acquire_lock_success(self):
        """Test successful lock acquisition."""
        result = self.manager.acquire_lock(1, 1, 'score', 'user1', 'User One')
        assert result['success'] is True
        assert self.manager.has_lock(1, 1, 'score', 'user1')

    def test_acquire_lock_denied_existing(self):
        """Test lock denied when already held by another user."""
        self.manager.acquire_lock(1, 1, 'score', 'user1', 'User One')
        result = self.manager.acquire_lock(1, 1, 'score', 'user2', 'User Two')

        assert result['success'] is False
        assert result['locked_by'] == 'User One'

    def test_acquire_lock_same_user_refreshes(self):
        """Test that same user can re-acquire lock (refreshes timestamp)."""
        self.manager.acquire_lock(1, 1, 'score', 'user1', 'User One')
        result = self.manager.acquire_lock(1, 1, 'score', 'user1', 'User One')

        assert result['success'] is True

    def test_different_fields_independent(self):
        """Test that locks on different fields are independent."""
        self.manager.acquire_lock(1, 1, 'score', 'user1', 'User One')
        result = self.manager.acquire_lock(1, 1, 'penalty', 'user2', 'User Two')

        assert result['success'] is True
        assert self.manager.has_lock(1, 1, 'score', 'user1')
        assert self.manager.has_lock(1, 1, 'penalty', 'user2')

    def test_release_lock_success(self):
        """Test successful lock release."""
        self.manager.acquire_lock(1, 1, 'score', 'user1', 'User One')
        result = self.manager.release_lock(1, 1, 'score', 'user1')

        assert result is True
        assert not self.manager.has_lock(1, 1, 'score', 'user1')

    def test_release_lock_wrong_user(self):
        """Test that user cannot release another user's lock."""
        self.manager.acquire_lock(1, 1, 'score', 'user1', 'User One')
        result = self.manager.release_lock(1, 1, 'score', 'user2')

        assert result is False
        assert self.manager.has_lock(1, 1, 'score', 'user1')

    def test_lock_expiration(self):
        """Test that expired locks can be overridden."""
        # Acquire lock
        self.manager.acquire_lock(1, 1, 'score', 'user1', 'User One')

        # Manually set lock time to past
        key = (1, 1, 'score')
        self.manager.locks[key]['locked_at'] = datetime.now(timezone.utc) - timedelta(minutes=10)

        # Different user should be able to acquire
        result = self.manager.acquire_lock(1, 1, 'score', 'user2', 'User Two')
        assert result['success'] is True
        assert self.manager.has_lock(1, 1, 'score', 'user2')

    def test_release_all_user_locks(self):
        """Test releasing all locks for a user."""
        self.manager.acquire_lock(1, 1, 'score', 'user1', 'User One')
        self.manager.acquire_lock(1, 2, 'score', 'user1', 'User One')
        self.manager.acquire_lock(2, 1, 'score', 'user1', 'User One')

        released = self.manager.release_all_user_locks('user1')

        assert len(released) == 3
        assert not self.manager.has_lock(1, 1, 'score', 'user1')
        assert not self.manager.has_lock(1, 2, 'score', 'user1')
        assert not self.manager.has_lock(2, 1, 'score', 'user1')

    def test_get_game_locks(self):
        """Test retrieving all locks for a game."""
        self.manager.acquire_lock(1, 1, 'score', 'user1', 'User One')
        self.manager.acquire_lock(1, 2, 'penalty', 'user2', 'User Two')
        self.manager.acquire_lock(2, 1, 'score', 'user3', 'User Three')

        locks = self.manager.get_game_locks(1)

        assert len(locks) == 2
        assert any(l['team_id'] == 1 and l['field_name'] == 'score' for l in locks)
        assert any(l['team_id'] == 2 and l['field_name'] == 'penalty' for l in locks)

    def test_cleanup_expired_locks(self):
        """Test cleanup of expired locks."""
        self.manager.acquire_lock(1, 1, 'score', 'user1', 'User One')
        self.manager.acquire_lock(1, 2, 'score', 'user2', 'User Two')

        # Expire first lock
        key = (1, 1, 'score')
        self.manager.locks[key]['locked_at'] = datetime.now(timezone.utc) - timedelta(minutes=10)

        count = self.manager.cleanup_expired_locks()

        assert count == 1
        assert not self.manager.has_lock(1, 1, 'score', 'user1')
        assert self.manager.has_lock(1, 2, 'score', 'user2')
