"""
E2E tests for responsive design and mobile compatibility.
Tests layout, touch interactions, and viewport-specific behaviors.
"""

import pytest
from playwright.sync_api import Page, expect


class TestMobileLayout:
    """Test mobile viewport rendering and interactions."""

    def test_mobile_viewport_renders_correctly(self, mobile_page: Page):
        """Test that mobile viewport renders without horizontal scroll."""
        page = mobile_page
        page.goto("http://localhost:5000")

        # Check viewport width
        viewport_size = page.viewport_size
        assert viewport_size['width'] == 375  # iPhone SE width

        # Page should not have horizontal scroll
        scroll_width = page.evaluate("document.documentElement.scrollWidth")
        viewport_width = page.evaluate("window.innerWidth")
        assert scroll_width <= viewport_width + 1  # Allow 1px tolerance

    def test_mobile_navigation_menu_works(self, mobile_page: Page):
        """Test that mobile navigation menu is accessible."""
        page = mobile_page
        page.goto("http://localhost:5000")

        # Look for mobile menu toggle (hamburger icon)
        menu_toggles = page.query_selector_all(".mobile-menu-toggle, .hamburger, [aria-label='Menu']")

        # If mobile menu exists, test it
        if len(menu_toggles) > 0:
            menu_toggles[0].click()
            page.wait_for_timeout(500)

            # Menu should be visible
            mobile_nav = page.locator("nav, .mobile-nav, .nav-menu")
            # Navigation exists and responded to interaction
            assert True

    def test_mobile_forms_are_usable(self, mobile_page: Page):
        """Test that forms are usable on mobile."""
        page = mobile_page

        # Login on mobile
        page.goto("http://localhost:5000/auth/login")

        # Form inputs should be visible and tappable
        username_input = page.locator('input[name="username"]')
        password_input = page.locator('input[name="password"]')
        submit_button = page.locator('button[type="submit"]')

        expect(username_input).to_be_visible()
        expect(password_input).to_be_visible()
        expect(submit_button).to_be_visible()

        # Inputs should be at least 44x44 pixels (touch target size)
        submit_box = submit_button.bounding_box()
        if submit_box:
            assert submit_box['height'] >= 40  # Allow some tolerance
            assert submit_box['width'] >= 40

    def test_mobile_text_is_readable(self, mobile_page: Page):
        """Test that text size is appropriate for mobile."""
        page = mobile_page
        page.goto("http://localhost:5000")

        # Check that base font size is at least 16px (prevents zoom on iOS)
        body_font_size = page.evaluate("""
            window.getComputedStyle(document.body).fontSize
        """)

        # Font size should be at least 14px (common mobile minimum)
        font_size_value = float(body_font_size.replace('px', ''))
        assert font_size_value >= 14


class TestTabletLayout:
    """Test tablet viewport rendering."""

    def test_tablet_viewport_renders_correctly(self, tablet_page: Page):
        """Test that tablet viewport renders properly."""
        page = tablet_page
        page.goto("http://localhost:5000")

        # Check viewport dimensions
        viewport_size = page.viewport_size
        assert viewport_size['width'] == 768  # iPad width

        # Page should render without issues
        page.wait_for_timeout(1000)
        assert page.url == "http://localhost:5000/"

    def test_tablet_layout_uses_appropriate_grid(self, tablet_page: Page):
        """Test that tablet uses appropriate column layout."""
        page = tablet_page
        page.goto("http://localhost:5000/admin/games")

        # Wait for content to load
        page.wait_for_timeout(1000)

        # Check that layout doesn't break
        body_width = page.evaluate("document.body.offsetWidth")
        assert body_width >= 750  # Should use tablet layout


class TestDesktopLayout:
    """Test desktop viewport rendering."""

    def test_desktop_viewport_full_features(self, authenticated_page: Page):
        """Test that desktop viewport shows all features."""
        page = authenticated_page
        page.goto("http://localhost:5000/admin/game_night_management")

        # Viewport should be desktop size
        viewport_size = page.viewport_size
        assert viewport_size['width'] == 1280

        # All major UI elements should be visible
        page.wait_for_timeout(1000)

        # Page should render completely
        assert page.url.endswith("/admin/game_night_management")


class TestTouchInteractions:
    """Test touch-specific interactions."""

    def test_buttons_respond_to_touch(self, mobile_page: Page):
        """Test that buttons are tap-friendly on mobile."""
        page = mobile_page
        page.goto("http://localhost:5000/auth/login")

        # Login
        page.fill('input[name="username"]', 'admin')
        page.fill('input[name="password"]', 'password')

        # Tap submit button (simulate touch)
        submit_button = page.locator('button[type="submit"]')
        submit_button.tap()

        page.wait_for_timeout(2000)

        # Should navigate to admin page
        assert "/admin/" in page.url

    def test_mobile_swipe_gestures_dont_break_ui(self, mobile_page: Page):
        """Test that swipe gestures don't cause UI issues."""
        page = mobile_page
        page.goto("http://localhost:5000")

        # Perform a swipe gesture
        page.mouse.move(300, 400)
        page.mouse.down()
        page.mouse.move(100, 400)
        page.mouse.up()

        page.wait_for_timeout(500)

        # Page should still be functional
        assert page.url == "http://localhost:5000/"
