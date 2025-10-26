"""
Unit tests for team forms.
Implements Black-Box Testing: Equivalence Partitioning and BVA for color codes.
"""
import pytest
from app.forms import TeamForm


@pytest.mark.unit
@pytest.mark.forms
@pytest.mark.blackbox
class TestTeamForm:
    """
    Test suite for TeamForm.
    Uses equivalence partitioning for hex color validation and participant names.
    """

    # Valid partition
    def test_valid_team_form(self, app):
        """Test form with valid inputs - valid partition."""
        with app.test_request_context():
            form = TeamForm(data={
                'name': 'Team Alpha',
                'color': '#FF0000',
                'participant1FirstName': 'John',
                'participant1LastName': 'Doe',
                'participant2FirstName': 'Jane',
                'participant2LastName': 'Smith'
            })
            assert form.validate() is True

    # Equivalence Partitioning: Valid hex colors
    def test_valid_hex_colors(self, app):
        """Test various valid hex color codes - valid partition."""
        valid_colors = [
            '#000000',  # Black
            '#FFFFFF',  # White
            '#FF0000',  # Red
            '#00FF00',  # Green
            '#0000FF',  # Blue
            '#123ABC',  # Mixed case
            '#abcdef',  # Lowercase
            '#ABCDEF',  # Uppercase
        ]

        for color in valid_colors:
            with app.test_request_context():
                form = TeamForm(data={
                    'name': 'Test Team',
                    'color': color,
                    'participant1FirstName': 'John',
                    'participant1LastName': 'Doe',
                    'participant2FirstName': 'Jane',
                    'participant2LastName': 'Smith'
                })
                assert form.validate() is True, f"Color {color} should be valid"

    # Equivalence Partitioning: Invalid hex colors
    def test_invalid_hex_colors(self, app):
        """Test invalid hex color codes - invalid partition."""
        invalid_colors = [
            'FF0000',    # Missing #
            '#FF00',     # Too short (4 chars)
            '#FF00000',  # Too long (7 chars)
            '#GGGGGG',   # Invalid characters
            '#FF 00 00', # Spaces
            'red',       # Color name
            '#ff-00-00', # Dashes
            '#',         # Just hash
            '',          # Empty
        ]

        for color in invalid_colors:
            with app.test_request_context():
                form = TeamForm(data={
                    'name': 'Test Team',
                    'color': color,
                    'participant1FirstName': 'John',
                    'participant1LastName': 'Doe',
                    'participant2FirstName': 'Jane',
                    'participant2LastName': 'Smith'
                })
                assert form.validate() is False, f"Color {color} should be invalid"
                assert 'color' in form.errors

    # BVA: Empty team name
    def test_empty_team_name(self, app):
        """Test empty team name - BVA."""
        with app.test_request_context():
            form = TeamForm(data={
                'name': '',
                'color': '#FF0000',
                'participant1FirstName': 'John',
                'participant1LastName': 'Doe',
                'participant2FirstName': 'Jane',
                'participant2LastName': 'Smith'
            })
            assert form.validate() is False
            assert 'name' in form.errors

    # Equivalence Partitioning: Missing required participants
    def test_missing_participant1_first_name(self, app):
        """Test missing first participant's first name - invalid partition."""
        with app.test_request_context():
            form = TeamForm(data={
                'name': 'Test Team',
                'color': '#FF0000',
                'participant1FirstName': '',
                'participant1LastName': 'Doe',
                'participant2FirstName': 'Jane',
                'participant2LastName': 'Smith'
            })
            assert form.validate() is False
            assert 'participant1FirstName' in form.errors

    def test_missing_participant1_last_name(self, app):
        """Test missing first participant's last name - invalid partition."""
        with app.test_request_context():
            form = TeamForm(data={
                'name': 'Test Team',
                'color': '#FF0000',
                'participant1FirstName': 'John',
                'participant1LastName': '',
                'participant2FirstName': 'Jane',
                'participant2LastName': 'Smith'
            })
            assert form.validate() is False
            assert 'participant1LastName' in form.errors

    def test_missing_participant2_first_name(self, app):
        """Test missing second participant's first name - invalid partition."""
        with app.test_request_context():
            form = TeamForm(data={
                'name': 'Test Team',
                'color': '#FF0000',
                'participant1FirstName': 'John',
                'participant1LastName': 'Doe',
                'participant2FirstName': '',
                'participant2LastName': 'Smith'
            })
            assert form.validate() is False
            assert 'participant2FirstName' in form.errors

    def test_missing_participant2_last_name(self, app):
        """Test missing second participant's last name - invalid partition."""
        with app.test_request_context():
            form = TeamForm(data={
                'name': 'Test Team',
                'color': '#FF0000',
                'participant1FirstName': 'John',
                'participant1LastName': 'Doe',
                'participant2FirstName': 'Jane',
                'participant2LastName': ''
            })
            assert form.validate() is False
            assert 'participant2LastName' in form.errors

    # Optional participants should not cause validation errors
    def test_optional_participant3_valid(self, app):
        """Test adding optional third participant - valid partition."""
        with app.test_request_context():
            form = TeamForm(data={
                'name': 'Test Team',
                'color': '#FF0000',
                'participant1FirstName': 'John',
                'participant1LastName': 'Doe',
                'participant2FirstName': 'Jane',
                'participant2LastName': 'Smith',
                'participant3FirstName': 'Bob',
                'participant3LastName': 'Johnson'
            })
            assert form.validate() is True

    def test_optional_participant3_empty(self, app):
        """Test optional third participant empty - valid partition."""
        with app.test_request_context():
            form = TeamForm(data={
                'name': 'Test Team',
                'color': '#FF0000',
                'participant1FirstName': 'John',
                'participant1LastName': 'Doe',
                'participant2FirstName': 'Jane',
                'participant2LastName': 'Smith',
                'participant3FirstName': '',
                'participant3LastName': ''
            })
            assert form.validate() is True

    def test_all_six_participants(self, app):
        """Test all six participants filled - valid partition."""
        with app.test_request_context():
            form = TeamForm(data={
                'name': 'Large Team',
                'color': '#FF0000',
                'participant1FirstName': 'P1',
                'participant1LastName': 'Last1',
                'participant2FirstName': 'P2',
                'participant2LastName': 'Last2',
                'participant3FirstName': 'P3',
                'participant3LastName': 'Last3',
                'participant4FirstName': 'P4',
                'participant4LastName': 'Last4',
                'participant5FirstName': 'P5',
                'participant5LastName': 'Last5',
                'participant6FirstName': 'P6',
                'participant6LastName': 'Last6'
            })
            assert form.validate() is True

    def test_very_long_participant_names(self, app):
        """Test very long participant names should fail validation."""
        with app.test_request_context():
            long_name = 'A' * 200
            form = TeamForm(data={
                'name': 'Test Team',
                'color': '#FF0000',
                'participant1FirstName': long_name,
                'participant1LastName': long_name,
                'participant2FirstName': 'Jane',
                'participant2LastName': 'Smith'
            })
            assert form.validate() is False
            assert 'participant1FirstName' in form.errors or 'participant1LastName' in form.errors

    # Edge case: Special characters in names
    def test_special_characters_in_names(self, app):
        """Test special characters in participant names."""
        with app.test_request_context():
            form = TeamForm(data={
                'name': 'Test Team',
                'color': '#FF0000',
                'participant1FirstName': "O'Brien",
                'participant1LastName': 'Smith-Jones',
                'participant2FirstName': 'José',
                'participant2LastName': 'García'
            })
            assert form.validate() is True

    # Edge case: Unicode in names
    def test_unicode_in_names(self, app):
        """Test unicode characters in participant names."""
        with app.test_request_context():
            form = TeamForm(data={
                'name': 'International Team',
                'color': '#FF0000',
                'participant1FirstName': '李',
                'participant1LastName': '明',
                'participant2FirstName': 'Владимир',
                'participant2LastName': 'Путин'
            })
            assert form.validate() is True

    # Test default color
    def test_default_color(self, app):
        """Test that default color is set."""
        with app.test_request_context():
            form = TeamForm()
            assert form.color.data == '#3b82f6'
