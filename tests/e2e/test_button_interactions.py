"""
E2E tests for button interactions and form submissions.
Tests click handlers, double-submit protection, and form behaviors.
"""

import pytest
from playwright.sync_api import Page, expect


class TestButtonClicks:
    """Test button click handlers and responses."""

    def test_delete_game_button_opens_modal(self, authenticated_page: Page):
        """Test that clicking delete button opens confirmation modal."""
        page = authenticated_page
        page.goto("http://localhost:5000/admin/games")

        # Wait for games table to load
        page.wait_for_selector("#gamesTable", timeout=5000)

        # Click first delete button if exists
        delete_buttons = page.query_selector_all(".delete-game-btn")
        if len(delete_buttons) > 0:
            delete_buttons[0].click()

            # Modal should be visible
            modal = page.locator("#deleteModal")
            expect(modal).to_be_visible()

    def test_modal_close_button_works(self, authenticated_page: Page):
        """Test that modal close button (X) works."""
        page = authenticated_page
        page.goto("http://localhost:5000/admin/games")

        delete_buttons = page.query_selector_all(".delete-game-btn")
        if len(delete_buttons) > 0:
            delete_buttons[0].click()

            # Click close button
            page.click(".close")

            # Modal should be hidden
            modal = page.locator("#deleteModal")
            expect(modal).not_to_be_visible()

    def test_esc_key_closes_modal(self, authenticated_page: Page):
        """Test that ESC key closes modal."""
        page = authenticated_page
        page.goto("http://localhost:5000/admin/games")

        delete_buttons = page.query_selector_all(".delete-game-btn")
        if len(delete_buttons) > 0:
            delete_buttons[0].click()

            # Press ESC
            page.keyboard.press("Escape")

            # Modal should be hidden
            modal = page.locator("#deleteModal")
            expect(modal).not_to_be_visible()

    def test_click_outside_modal_closes_it(self, authenticated_page: Page):
        """Test that clicking outside modal closes it."""
        page = authenticated_page
        page.goto("http://localhost:5000/admin/games")

        delete_buttons = page.query_selector_all(".delete-game-btn")
        if len(delete_buttons) > 0:
            delete_buttons[0].click()

            # Click on modal background (outside content)
            page.click("#deleteModal", position={"x": 0, "y": 0})

            # Modal should be hidden
            modal = page.locator("#deleteModal")
            expect(modal).not_to_be_visible()


class TestDoubleSubmitPrevention:
    """Test protection against double-click form submissions."""

    def test_double_click_submit_creates_only_one_item(self, authenticated_page: Page):
        """Test that double-clicking submit doesn't create duplicates."""
        page = authenticated_page
        page.goto("http://localhost:5000/admin/add_team")

        # Fill in team form
        page.fill('input[name="name"]', 'Double Click Test Team')
        page.fill('input[name="color"]', '#FF0000')
        page.fill('input[name="participant1FirstName"]', 'John')
        page.fill('input[name="participant1LastName"]', 'Doe')
        page.fill('input[name="participant2FirstName"]', 'Jane')
        page.fill('input[name="participant2LastName"]', 'Smith')

        # Double-click submit button (simulate rapid clicking)
        submit_button = page.locator('button[type="submit"]')
        submit_button.click()
        submit_button.click()  # Second click should be ignored

        # Wait for redirect or success message
        page.wait_for_timeout(1000)

        # Try to submit the same form again
        page.goto("http://localhost:5000/admin/add_team")
        page.fill('input[name="name"]', 'Double Click Test Team')
        page.fill('input[name="color"]', '#0000FF')
        page.fill('input[name="participant1FirstName"]', 'A')
        page.fill('input[name="participant1LastName"]', 'B')
        page.fill('input[name="participant2FirstName"]', 'C')
        page.fill('input[name="participant2LastName"]', 'D')

        page.click('button[type="submit"]')
        page.wait_for_timeout(1000)

        # Should show validation error or prevent duplicate
        # Either way, we verify only one team was created
        page.goto("http://localhost:5000/admin/teams")
        team_rows = page.query_selector_all("tr:has-text('Double Click Test Team')")
        assert len(team_rows) <= 1, "Double-click created duplicate teams"

    def test_form_resubmission_after_back_button(self, authenticated_page: Page):
        """Test that browser back button doesn't cause form resubmission."""
        page = authenticated_page

        # Submit a form
        page.goto("http://localhost:5000/admin/add_team")
        page.fill('input[name="name"]', 'Back Button Test Team')
        page.fill('input[name="color"]', '#00FF00')
        page.fill('input[name="participant1FirstName"]', 'Test')
        page.fill('input[name="participant1LastName"]', 'User')
        page.fill('input[name="participant2FirstName"]', 'Another')
        page.fill('input[name="participant2LastName"]', 'User')

        page.click('button[type="submit"]')
        page.wait_for_timeout(1000)

        # Go back
        page.go_back()

        # Form should be empty or show new blank form
        name_input = page.locator('input[name="name"]')
        # Input should either not exist or be empty
        if name_input.count() > 0:
            expect(name_input).to_have_value("")


class TestScoreButtons:
    """Test score increment/decrement button functionality."""

    def test_score_increment_button(self, authenticated_page: Page):
        """Test that score increment button increases score."""
        page = authenticated_page
        page.goto("http://localhost:5000/admin/live_scoring")

        # Select a team
        page.select_option("#team-selector", index=1)
        page.wait_for_timeout(500)

        # Get initial score
        score_input = page.locator("#score-input")
        initial_value = float(score_input.input_value() or "0")

        # Click increment
        page.click('[data-action="increment-score"]')

        # Score should increase by 1
        new_value = float(score_input.input_value())
        assert new_value == initial_value + 1

    def test_score_decrement_button(self, authenticated_page: Page):
        """Test that score decrement button decreases score."""
        page = authenticated_page
        page.goto("http://localhost:5000/admin/live_scoring")

        # Select a team and set score
        page.select_option("#team-selector", index=1)
        page.wait_for_timeout(500)

        score_input = page.locator("#score-input")
        score_input.fill("10")

        # Click decrement
        page.click('[data-action="decrement-score"]')

        # Score should decrease by 1
        new_value = float(score_input.input_value())
        assert new_value == 9.0


class TestStopwatchButtons:
    """Test stopwatch start/stop/reset button functionality."""

    def test_start_stopwatch_button(self, authenticated_page: Page):
        """Test that stopwatch starts when button clicked."""
        page = authenticated_page
        page.goto("http://localhost:5000/admin/live_scoring")

        page.select_option("#team-selector", index=1)
        page.wait_for_timeout(500)

        # Start stopwatch
        page.click('[data-action="start-stopwatch"]')
        page.wait_for_timeout(1000)

        # Timer display should have updated
        timer_display = page.locator("#timer-display")
        timer_text = timer_display.text_content()
        assert timer_text != "00:00.000", "Timer did not start"

    def test_stop_stopwatch_button(self, authenticated_page: Page):
        """Test that stopwatch stops and updates score."""
        page = authenticated_page
        page.goto("http://localhost:5000/admin/live_scoring")

        page.select_option("#team-selector", index=1)
        page.wait_for_timeout(500)

        # Start and stop stopwatch
        page.click('[data-action="start-stopwatch"]')
        page.wait_for_timeout(500)
        page.click('[data-action="stop-stopwatch"]')

        # Score input should be populated
        score_input = page.locator("#score-input")
        score_value = float(score_input.input_value())
        assert score_value > 0, "Score was not set from timer"

    def test_reset_stopwatch_button(self, authenticated_page: Page):
        """Test that reset button resets timer to zero."""
        page = authenticated_page
        page.goto("http://localhost:5000/admin/live_scoring")

        page.select_option("#team-selector", index=1)
        page.wait_for_timeout(500)

        # Start timer
        page.click('[data-action="start-stopwatch"]')
        page.wait_for_timeout(500)

        # Reset timer
        page.click('[data-action="reset-stopwatch"]')

        # Timer should be back to zero
        timer_display = page.locator("#timer-display")
        expect(timer_display).to_have_text("00:00.000")


class TestPlaygroundButtons:
    """Test playground simulation button functionality."""

    def test_randomize_game_button(self, authenticated_page: Page):
        """Test that randomize button changes placements."""
        page = authenticated_page
        page.goto("http://localhost:5000/playground")

        # Wait for playground to load
        page.wait_for_selector(".btn-randomize-icon", timeout=5000)

        # Get initial placements
        initial_placements = []
        selects = page.query_selector_all(".placement-dropdown")
        for select in selects[:3]:  # Get first 3
            initial_placements.append(select.input_value())

        # Click randomize button
        randomize_buttons = page.query_selector_all(".btn-randomize-icon")
        if len(randomize_buttons) > 0:
            randomize_buttons[0].click()
            page.wait_for_timeout(500)

            # Get new placements
            new_placements = []
            selects = page.query_selector_all(".placement-dropdown")
            for select in selects[:3]:
                new_placements.append(select.input_value())

            # At least one placement should have changed
            assert initial_placements != new_placements, "Randomize did not change placements"
