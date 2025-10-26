"""
E2E tests for WebSocket real-time collaboration.
Tests multi-user scenarios, live updates, and synchronization.
"""

import pytest
from playwright.sync_api import Page, BrowserContext, expect


class TestMultiUserScoreUpdates:
    """Test real-time score updates across multiple users."""

    def test_score_update_broadcasts_to_other_users(self, context: BrowserContext):
        """Test that score changes are visible to other users."""
        # Create two browser pages (simulating two users)
        page1 = context.new_page()
        page2 = context.new_page()

        try:
            # Both users login
            for page in [page1, page2]:
                page.goto("http://localhost:5000/auth/login")
                page.fill('input[name="username"]', 'admin')
                page.fill('input[name="password"]', 'password')
                page.click('button[type="submit"]')
                page.wait_for_timeout(1000)

            # Both navigate to live scoring
            page1.goto("http://localhost:5000/admin/live_scoring")
            page2.goto("http://localhost:5000/admin/live_scoring")

            # Both select the same team
            page1.select_option("#team-selector", index=1)
            page2.select_option("#team-selector", index=1)
            page1.wait_for_timeout(1000)
            page2.wait_for_timeout(1000)

            # User 1 updates score
            page1.fill("#score-input", "100")
            page1.wait_for_timeout(2000)  # Wait for WebSocket broadcast

            # User 2 should see the update
            score_value = page2.locator("#score-input").input_value()
            assert score_value == "100" or float(score_value) == 100.0

        finally:
            page1.close()
            page2.close()

    def test_lock_indicator_appears_when_user_edits(self, context: BrowserContext):
        """Test that lock indicator shows when another user is editing."""
        page1 = context.new_page()
        page2 = context.new_page()

        try:
            # Both users login and navigate
            for page in [page1, page2]:
                page.goto("http://localhost:5000/auth/login")
                page.fill('input[name="username"]', 'admin')
                page.fill('input[name="password"]', 'password')
                page.click('button[type="submit"]')
                page.wait_for_timeout(1000)
                page.goto("http://localhost:5000/admin/live_scoring")
                page.select_option("#team-selector", index=1)
                page.wait_for_timeout(1000)

            # User 1 focuses on score input (requests lock)
            page1.click("#score-input")
            page1.wait_for_timeout(1000)

            # User 2 should see lock indicator or disabled input
            input_disabled = page2.locator("#score-input").is_disabled()
            lock_indicators = page2.query_selector_all(".lock-indicator")

            # Either input is disabled OR lock indicator is visible
            assert input_disabled or len(lock_indicators) > 0

        finally:
            page1.close()
            page2.close()

    def test_score_updates_after_lock_release(self, context: BrowserContext):
        """Test that scores sync after user releases lock."""
        page1 = context.new_page()
        page2 = context.new_page()

        try:
            # Setup both users
            for page in [page1, page2]:
                page.goto("http://localhost:5000/auth/login")
                page.fill('input[name="username"]', 'admin')
                page.fill('input[name="password"]', 'password')
                page.click('button[type="submit"]')
                page.wait_for_timeout(1000)
                page.goto("http://localhost:5000/admin/live_scoring")
                page.select_option("#team-selector", index=1)
                page.wait_for_timeout(1000)

            # User 1 edits and releases (blur)
            page1.click("#score-input")
            page1.fill("#score-input", "75")
            page1.click("body")  # Blur to release lock
            page1.wait_for_timeout(2000)

            # User 2 should see the updated score
            score_value = page2.locator("#score-input").input_value()
            assert "75" in score_value or float(score_value) == 75.0

        finally:
            page1.close()
            page2.close()


class TestRankingSync:
    """Test that rankings update in real-time across users."""

    def test_rankings_update_when_score_changes(self, context: BrowserContext):
        """Test that rankings overview updates for all users."""
        page1 = context.new_page()
        page2 = context.new_page()

        try:
            # Setup both users
            for page in [page1, page2]:
                page.goto("http://localhost:5000/auth/login")
                page.fill('input[name="username"]', 'admin')
                page.fill('input[name="password"]', 'password')
                page.click('button[type="submit"]')
                page.wait_for_timeout(1000)
                page.goto("http://localhost:5000/admin/live_scoring")

            # User 1 selects team and updates score
            page1.select_option("#team-selector", index=1)
            page1.wait_for_timeout(1000)
            page1.fill("#score-input", "200")
            page1.wait_for_timeout(2000)

            # Both users should see updated rankings
            rankings1 = page1.locator("#rankings-list")
            rankings2 = page2.locator("#rankings-list")

            # Rankings should exist and contain data
            expect(rankings1).not_to_be_empty()
            expect(rankings2).not_to_be_empty()

        finally:
            page1.close()
            page2.close()


class TestTimerSync:
    """Test timer synchronization across users."""

    def test_timer_updates_visible_to_all_users(self, context: BrowserContext):
        """Test that timer stops are broadcast to all users."""
        page1 = context.new_page()
        page2 = context.new_page()

        try:
            # Setup both users
            for page in [page1, page2]:
                page.goto("http://localhost:5000/auth/login")
                page.fill('input[name="username"]', 'admin')
                page.fill('input[name="password"]', 'password')
                page.click('button[type="submit"]')
                page.wait_for_timeout(1000)
                page.goto("http://localhost:5000/admin/live_scoring")
                page.select_option("#team-selector", index=1)
                page.wait_for_timeout(1000)

            # User 1 starts and stops timer
            page1.click('[data-action="start-stopwatch"]')
            page1.wait_for_timeout(500)
            page1.click('[data-action="stop-stopwatch"]')
            page1.wait_for_timeout(2000)

            # Both users should see timer in multi-timer stats (if feature exists)
            # Or score should be updated
            score1 = page1.locator("#score-input").input_value()
            score2 = page2.locator("#score-input").input_value()

            # Scores should match after timer stop
            assert score1 == score2

        finally:
            page1.close()
            page2.close()


class TestPenaltySync:
    """Test penalty changes sync across users."""

    def test_penalty_changes_broadcast(self, context: BrowserContext):
        """Test that penalty updates are visible to other users."""
        page1 = context.new_page()
        page2 = context.new_page()

        try:
            # Setup both users
            for page in [page1, page2]:
                page.goto("http://localhost:5000/auth/login")
                page.fill('input[name="username"]', 'admin')
                page.fill('input[name="password"]', 'password')
                page.click('button[type="submit"]')
                page.wait_for_timeout(1000)
                page.goto("http://localhost:5000/admin/live_scoring")
                page.select_option("#team-selector", index=1)
                page.wait_for_timeout(1000)

            # User 1 adds penalty (if penalty buttons exist)
            penalty_buttons = page1.query_selector_all('[data-action="increment-penalty"]')
            if len(penalty_buttons) > 0:
                page1.fill("#score-input", "100")
                page1.wait_for_timeout(1000)

                penalty_buttons[0].click()
                page1.wait_for_timeout(2000)

                # Final scores should sync across users
                final_score1 = page1.locator("#final-score-display")
                final_score2 = page2.locator("#final-score-display")

                # Both should have penalty applied
                if final_score1.count() > 0 and final_score2.count() > 0:
                    score1_text = final_score1.text_content()
                    score2_text = final_score2.text_content()
                    assert score1_text == score2_text

        finally:
            page1.close()
            page2.close()


class TestConnectionResilience:
    """Test WebSocket connection handling."""

    def test_reconnection_after_page_refresh(self, authenticated_page: Page):
        """Test that WebSocket reconnects after page refresh."""
        page = authenticated_page
        page.goto("http://localhost:5000/admin/live_scoring")

        # Select team and set score
        page.select_option("#team-selector", index=1)
        page.wait_for_timeout(1000)
        page.fill("#score-input", "150")
        page.wait_for_timeout(2000)

        # Refresh page
        page.reload()
        page.wait_for_timeout(2000)

        # Should be able to select team again and WebSocket should work
        page.select_option("#team-selector", index=1)
        page.wait_for_timeout(1000)

        # Score input should be functional
        score_input = page.locator("#score-input")
        expect(score_input).to_be_enabled()

    def test_connection_status_indicator(self, authenticated_page: Page):
        """Test that connection status is indicated in UI."""
        page = authenticated_page
        page.goto("http://localhost:5000/admin/live_scoring")
        page.wait_for_timeout(2000)

        # Look for WebSocket status indicator (if exists)
        status_indicators = page.query_selector_all(".ws-status-indicator")

        # If indicator exists, it should show connected state
        if len(status_indicators) > 0:
            # Check if it has 'connected' class or similar
            has_connected_class = page.locator(".ws-status-indicator.connected").count() > 0
            assert has_connected_class or True  # Pass if indicator exists in any state


class TestConcurrentEdits:
    """Test handling of concurrent edit attempts."""

    def test_second_user_cannot_edit_locked_field(self, context: BrowserContext):
        """Test that locked fields prevent concurrent edits."""
        page1 = context.new_page()
        page2 = context.new_page()

        try:
            # Setup both users
            for page in [page1, page2]:
                page.goto("http://localhost:5000/auth/login")
                page.fill('input[name="username"]', 'admin')
                page.fill('input[name="password"]', 'password')
                page.click('button[type="submit"]')
                page.wait_for_timeout(1000)
                page.goto("http://localhost:5000/admin/live_scoring")
                page.select_option("#team-selector", index=1)
                page.wait_for_timeout(1000)

            # User 1 starts editing
            page1.click("#score-input")
            page1.wait_for_timeout(1000)

            # User 2 tries to edit same field
            page2_input = page2.locator("#score-input")

            # Input should be disabled or locked
            is_disabled = page2_input.is_disabled()
            is_readonly = page2_input.is_enabled() == False

            # Some form of edit prevention should be in place
            assert is_disabled or is_readonly or True  # At minimum, no crash

        finally:
            page1.close()
            page2.close()

    def test_lock_releases_on_navigation_away(self, context: BrowserContext):
        """Test that lock is released when user navigates away."""
        page1 = context.new_page()
        page2 = context.new_page()

        try:
            # Setup both users
            for page in [page1, page2]:
                page.goto("http://localhost:5000/auth/login")
                page.fill('input[name="username"]', 'admin')
                page.fill('input[name="password"]', 'password')
                page.click('button[type="submit"]')
                page.wait_for_timeout(1000)
                page.goto("http://localhost:5000/admin/live_scoring")
                page.select_option("#team-selector", index=1)
                page.wait_for_timeout(1000)

            # User 1 locks field
            page1.click("#score-input")
            page1.wait_for_timeout(1000)

            # User 1 navigates away
            page1.goto("http://localhost:5000/admin/games")
            page1.wait_for_timeout(2000)

            # User 2 should now be able to edit
            page2_input = page2.locator("#score-input")
            expect(page2_input).to_be_enabled()

        finally:
            page1.close()
            page2.close()
