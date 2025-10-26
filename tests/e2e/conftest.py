"""
Pytest configuration for Playwright E2E tests.
Provides fixtures for browser automation testing.
"""

import pytest
from playwright.sync_api import sync_playwright, Browser, BrowserContext, Page


@pytest.fixture(scope="session")
def browser():
    """Create a browser instance for the test session."""
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        yield browser
        browser.close()


@pytest.fixture
def context(browser: Browser):
    """Create a new browser context for each test."""
    context = browser.new_context(
        viewport={"width": 1280, "height": 720},
        locale="en-US",
    )
    yield context
    context.close()


@pytest.fixture
def page(context: BrowserContext):
    """Create a new page for each test."""
    page = context.new_page()
    yield page
    page.close()


@pytest.fixture
def authenticated_page(page: Page):
    """Create an authenticated admin page."""
    # Navigate to login page
    page.goto("http://localhost:5000/auth/login")

    # Fill in credentials
    page.fill('input[name="username"]', 'admin')
    page.fill('input[name="password"]', 'password')

    # Submit form
    page.click('button[type="submit"]')

    # Wait for redirect to admin page
    page.wait_for_url("**/admin/**", timeout=5000)

    yield page


@pytest.fixture
def mobile_page(browser: Browser):
    """Create a page with mobile viewport."""
    context = browser.new_context(
        viewport={"width": 375, "height": 667},  # iPhone SE
        user_agent="Mozilla/5.0 (iPhone; CPU iPhone OS 14_0 like Mac OS X)"
    )
    page = context.new_page()
    yield page
    page.close()
    context.close()


@pytest.fixture
def tablet_page(browser: Browser):
    """Create a page with tablet viewport."""
    context = browser.new_context(
        viewport={"width": 768, "height": 1024},  # iPad
        user_agent="Mozilla/5.0 (iPad; CPU OS 14_0 like Mac OS X)"
    )
    page = context.new_page()
    yield page
    page.close()
    context.close()
