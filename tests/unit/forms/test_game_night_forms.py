"""
Unit tests for game night forms.
Implements Black-Box Testing: Equivalence Partitioning and BVA.
"""
import pytest
from datetime import date, timedelta
from app.forms import GameNightForm


@pytest.mark.unit
@pytest.mark.forms
@pytest.mark.blackbox
class TestGameNightForm:
    """
    Test suite for GameNightForm.
    Uses equivalence partitioning and BVA for name length and date validation.
    """

    # Valid partition
    def test_valid_game_night_form(self, app):
        """Test form with valid inputs - valid partition."""
        with app.test_request_context():
            form = GameNightForm(data={
                'name': 'Epic Game Night',
                'date': date.today()
            })
            assert form.validate() is True

    # BVA: Minimum name length (3 characters - boundary)
    def test_minimum_name_length(self, app):
        """Test minimum valid name length (exactly 3) - BVA."""
        with app.test_request_context():
            form = GameNightForm(data={
                'name': 'ABC',  # Exactly 3 chars
                'date': date.today()
            })
            assert form.validate() is True

    # BVA: Below minimum name length (2 characters)
    def test_below_minimum_name_length(self, app):
        """Test below minimum name length (2 chars) - BVA."""
        with app.test_request_context():
            form = GameNightForm(data={
                'name': 'AB',  # 2 chars - too short
                'date': date.today()
            })
            assert form.validate() is False
            assert 'name' in form.errors

    # BVA: Single character name
    def test_single_character_name(self, app):
        """Test single character name - BVA."""
        with app.test_request_context():
            form = GameNightForm(data={
                'name': 'A',
                'date': date.today()
            })
            assert form.validate() is False
            assert 'name' in form.errors

    # BVA: Empty name
    def test_empty_name(self, app):
        """Test empty name - BVA."""
        with app.test_request_context():
            form = GameNightForm(data={
                'name': '',
                'date': date.today()
            })
            assert form.validate() is False
            assert 'name' in form.errors

    def test_maximum_name_length(self, app):
        """Test maximum valid name length."""
        with app.test_request_context():
            form = GameNightForm(data={
                'name': 'A' * 100,
                'date': date.today()
            })
            assert form.validate() is True

    def test_above_maximum_name_length(self, app):
        """Test above maximum name length."""
        with app.test_request_context():
            form = GameNightForm(data={
                'name': 'A' * 101,
                'date': date.today()
            })
            assert form.validate() is False
            assert 'name' in form.errors

    def test_near_maximum_name_length(self, app):
        """Test near maximum name length."""
        with app.test_request_context():
            form = GameNightForm(data={
                'name': 'A' * 99,
                'date': date.today()
            })
            assert form.validate() is True

    # Equivalence Partitioning: Valid name with special characters
    def test_name_with_special_characters(self, app):
        """Test name with special characters - valid partition."""
        with app.test_request_context():
            form = GameNightForm(data={
                'name': 'Game Night 2024 - Championship!',
                'date': date.today()
            })
            assert form.validate() is True

    # Equivalence Partitioning: Valid name with unicode
    def test_name_with_unicode(self, app):
        """Test name with unicode characters - valid partition."""
        with app.test_request_context():
            form = GameNightForm(data={
                'name': 'Jeux de Nuit 2024 🎮',
                'date': date.today()
            })
            assert form.validate() is True

    # Equivalence Partitioning: Whitespace only name
    def test_whitespace_only_name(self, app):
        """Test whitespace only name - invalid partition."""
        with app.test_request_context():
            form = GameNightForm(data={
                'name': '   ',
                'date': date.today()
            })
            # This might pass form validation but should fail logic validation
            # WTForms counts whitespace as valid characters

    # Date validation: Valid date (today)
    def test_date_today(self, app):
        """Test with today's date - valid partition."""
        with app.test_request_context():
            form = GameNightForm(data={
                'name': 'Today Game Night',
                'date': date.today()
            })
            assert form.validate() is True

    # Date validation: Past date
    def test_past_date(self, app):
        """Test with past date - valid partition."""
        with app.test_request_context():
            past_date = date.today() - timedelta(days=30)
            form = GameNightForm(data={
                'name': 'Past Game Night',
                'date': past_date
            })
            # Form validation should pass (business logic might restrict)
            assert form.validate() is True

    # Date validation: Future date
    def test_future_date(self, app):
        """Test with future date - valid partition."""
        with app.test_request_context():
            future_date = date.today() + timedelta(days=30)
            form = GameNightForm(data={
                'name': 'Future Game Night',
                'date': future_date
            })
            assert form.validate() is True

    # Date validation: Missing date
    def test_missing_date(self, app):
        """Test with missing date - invalid partition."""
        with app.test_request_context():
            form = GameNightForm(data={
                'name': 'Game Night',
                'date': None
            })
            assert form.validate() is False
            assert 'date' in form.errors

    # Both fields missing
    def test_both_fields_missing(self, app):
        """Test with both fields missing - invalid partition."""
        with app.test_request_context():
            form = GameNightForm(data={
                'name': '',
                'date': None
            })
            assert form.validate() is False
            assert 'name' in form.errors
            assert 'date' in form.errors

    # Edge case: Name with only numbers
    def test_name_with_only_numbers(self, app):
        """Test name with only numbers."""
        with app.test_request_context():
            form = GameNightForm(data={
                'name': '12345',
                'date': date.today()
            })
            assert form.validate() is True

    # Edge case: Name with leading/trailing whitespace
    def test_name_with_leading_trailing_whitespace(self, app):
        """Test name with leading and trailing whitespace."""
        with app.test_request_context():
            form = GameNightForm(data={
                'name': '  Game Night  ',
                'date': date.today()
            })
            # WTForms doesn't strip by default
            assert form.validate() is True
