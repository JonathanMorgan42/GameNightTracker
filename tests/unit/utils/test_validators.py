"""Comprehensive unit tests for validation utilities."""
import pytest
from app.utils.validators import (
    validate_string_length,
    validate_numeric_range,
    validate_integer_range,
    validate_penalties_list,
    extract_penalties_from_form,
    get_length_error_message,
    get_range_error_message,
    # Constants
    TEAM_NAME_MIN, TEAM_NAME_MAX,
    GAME_NAME_MIN, GAME_NAME_MAX,
    PENALTY_NAME_MIN, PENALTY_NAME_MAX,
    PENALTY_VALUE_MIN, PENALTY_VALUE_MAX,
    SCORE_VALUE_MIN, SCORE_VALUE_MAX,
    POINT_MULTIPLIER_MIN, POINT_MULTIPLIER_MAX,
    SCORE_NOTES_MAX
)


@pytest.mark.unit
@pytest.mark.validators
class TestStringLengthValidation:
    """Test suite for string length validation."""

    def test_valid_string_length(self):
        """Test validation passes for valid string length."""
        is_valid, error = validate_string_length(
            "Test Name", "Name", TEAM_NAME_MIN, TEAM_NAME_MAX
        )
        assert is_valid is True
        assert error is None

    def test_string_at_min_length(self):
        """Test validation at minimum boundary."""
        is_valid, error = validate_string_length(
            "A", "Name", 1, 50
        )
        assert is_valid is True
        assert error is None

    def test_string_at_max_length(self):
        """Test validation at maximum boundary."""
        max_string = "X" * 50
        is_valid, error = validate_string_length(
            max_string, "Name", 1, 50
        )
        assert is_valid is True
        assert error is None

    def test_string_below_min_length(self):
        """Test validation fails below minimum."""
        is_valid, error = validate_string_length(
            "", "Name", 1, 50
        )
        assert is_valid is False
        assert "too short" in error
        assert "minimum 1" in error

    def test_string_above_max_length(self):
        """Test validation fails above maximum."""
        long_string = "X" * 51
        is_valid, error = validate_string_length(
            long_string, "Name", 1, 50
        )
        assert is_valid is False
        assert "exceeds maximum length" in error
        assert "50" in error

    def test_string_with_whitespace_stripped(self):
        """Test that whitespace is stripped before validation."""
        is_valid, error = validate_string_length(
            "  Valid  ", "Name", 1, 50
        )
        assert is_valid is True

    def test_none_value_fails(self):
        """Test that None value fails validation."""
        is_valid, error = validate_string_length(
            None, "Name", 1, 50
        )
        assert is_valid is False
        assert "is required" in error

    def test_empty_string_after_strip(self):
        """Test empty string after stripping whitespace."""
        is_valid, error = validate_string_length(
            "   ", "Name", 1, 50
        )
        assert is_valid is False
        assert "too short" in error

    def test_numeric_value_converted_to_string(self):
        """Test numeric values are converted to strings."""
        is_valid, error = validate_string_length(
            123, "Value", 1, 10
        )
        assert is_valid is True

    def test_unicode_characters(self):
        """Test validation with unicode characters."""
        is_valid, error = validate_string_length(
            "Team 团队", "Name", 1, 50
        )
        assert is_valid is True

    def test_special_characters(self):
        """Test validation with special characters."""
        is_valid, error = validate_string_length(
            "Team!@#$%", "Name", 1, 50
        )
        assert is_valid is True

    def test_sql_injection_attempt(self):
        """Test that SQL injection strings are validated by length."""
        sql_injection = "'; DROP TABLE teams; --"
        is_valid, error = validate_string_length(
            sql_injection, "Name", 1, 50
        )
        # Should pass length validation (sanitization happens elsewhere)
        assert is_valid is True

    def test_xss_attempt(self):
        """Test XSS attempt string validation."""
        xss_attempt = "<script>alert('XSS')</script>"
        is_valid, error = validate_string_length(
            xss_attempt, "Name", 1, 50
        )
        # Should pass length validation
        assert is_valid is True

    def test_very_long_string_overflow(self):
        """Test extremely long string (potential buffer overflow)."""
        overflow_string = "X" * 10000
        is_valid, error = validate_string_length(
            overflow_string, "Name", 1, 50
        )
        assert is_valid is False
        assert "exceeds maximum" in error


@pytest.mark.unit
@pytest.mark.validators
class TestNumericRangeValidation:
    """Test suite for numeric range validation."""

    def test_valid_numeric_value(self):
        """Test validation passes for valid numeric value."""
        is_valid, error = validate_numeric_range(
            100, "Score", SCORE_VALUE_MIN, SCORE_VALUE_MAX
        )
        assert is_valid is True
        assert error is None

    def test_value_at_min_boundary(self):
        """Test validation at minimum boundary."""
        is_valid, error = validate_numeric_range(
            -999999.99, "Score", SCORE_VALUE_MIN, SCORE_VALUE_MAX
        )
        assert is_valid is True

    def test_value_at_max_boundary(self):
        """Test validation at maximum boundary."""
        is_valid, error = validate_numeric_range(
            999999.99, "Score", SCORE_VALUE_MIN, SCORE_VALUE_MAX
        )
        assert is_valid is True

    def test_value_below_min(self):
        """Test validation fails below minimum."""
        is_valid, error = validate_numeric_range(
            -1000000, "Score", SCORE_VALUE_MIN, SCORE_VALUE_MAX
        )
        assert is_valid is False
        assert "must be between" in error

    def test_value_above_max(self):
        """Test validation fails above maximum."""
        is_valid, error = validate_numeric_range(
            1000000, "Score", SCORE_VALUE_MIN, SCORE_VALUE_MAX
        )
        assert is_valid is False
        assert "must be between" in error

    def test_zero_value(self):
        """Test zero as valid value."""
        is_valid, error = validate_numeric_range(
            0, "Score", -100, 100
        )
        assert is_valid is True

    def test_negative_value(self):
        """Test negative value in valid range."""
        is_valid, error = validate_numeric_range(
            -50, "Score", -100, 100
        )
        assert is_valid is True

    def test_decimal_value(self):
        """Test decimal/float value."""
        is_valid, error = validate_numeric_range(
            45.567, "Score", 0, 100
        )
        assert is_valid is True

    def test_string_numeric_value(self):
        """Test numeric string is converted."""
        is_valid, error = validate_numeric_range(
            "100", "Score", 0, 200
        )
        assert is_valid is True

    def test_invalid_string_fails(self):
        """Test non-numeric string fails."""
        is_valid, error = validate_numeric_range(
            "not a number", "Score", 0, 100
        )
        assert is_valid is False
        assert "must be a valid number" in error

    def test_none_value_without_allow_none(self):
        """Test None value fails when not allowed."""
        is_valid, error = validate_numeric_range(
            None, "Score", 0, 100, allow_none=False
        )
        assert is_valid is False
        assert "is required" in error

    def test_none_value_with_allow_none(self):
        """Test None value passes when allowed."""
        is_valid, error = validate_numeric_range(
            None, "Score", 0, 100, allow_none=True
        )
        assert is_valid is True
        assert error is None

    def test_overflow_value(self):
        """Test extremely large value (overflow)."""
        is_valid, error = validate_numeric_range(
            9999999999999999, "Score", SCORE_VALUE_MIN, SCORE_VALUE_MAX
        )
        assert is_valid is False

    def test_scientific_notation(self):
        """Test scientific notation value."""
        is_valid, error = validate_numeric_range(
            1.5e2, "Score", 0, 200
        )
        assert is_valid is True

    def test_infinity_value(self):
        """Test infinity value fails."""
        is_valid, error = validate_numeric_range(
            float('inf'), "Score", 0, 1000
        )
        assert is_valid is False


@pytest.mark.unit
@pytest.mark.validators
class TestIntegerRangeValidation:
    """Test suite for integer range validation."""

    def test_valid_integer_value(self):
        """Test validation passes for valid integer."""
        is_valid, error = validate_integer_range(
            10, "Points", 1, 100
        )
        assert is_valid is True
        assert error is None

    def test_integer_at_min_boundary(self):
        """Test validation at minimum boundary."""
        is_valid, error = validate_integer_range(
            1, "Points", 1, 100
        )
        assert is_valid is True

    def test_integer_at_max_boundary(self):
        """Test validation at maximum boundary."""
        is_valid, error = validate_integer_range(
            100, "Points", 1, 100
        )
        assert is_valid is True

    def test_integer_below_min(self):
        """Test validation fails below minimum."""
        is_valid, error = validate_integer_range(
            0, "Points", 1, 100
        )
        assert is_valid is False
        assert "must be between" in error

    def test_integer_above_max(self):
        """Test validation fails above maximum."""
        is_valid, error = validate_integer_range(
            101, "Points", 1, 100
        )
        assert is_valid is False

    def test_integer_from_string(self):
        """Test integer string is converted."""
        is_valid, error = validate_integer_range(
            "50", "Points", 1, 100
        )
        assert is_valid is True

    def test_float_converted_to_integer(self):
        """Test float is converted to integer."""
        is_valid, error = validate_integer_range(
            50.7, "Points", 1, 100
        )
        assert is_valid is True

    def test_invalid_string_fails(self):
        """Test non-integer string fails."""
        is_valid, error = validate_integer_range(
            "not an int", "Points", 1, 100
        )
        assert is_valid is False
        assert "must be a valid integer" in error

    def test_none_value_allowed(self):
        """Test None value when allowed."""
        is_valid, error = validate_integer_range(
            None, "Points", 1, 100, allow_none=True
        )
        assert is_valid is True

    def test_overflow_integer(self):
        """Test extremely large integer."""
        is_valid, error = validate_integer_range(
            9999999999, "Points", 1, 100
        )
        assert is_valid is False


@pytest.mark.unit
@pytest.mark.validators
class TestPenaltiesValidation:
    """Test suite for penalty data validation."""

    def test_valid_penalties_list(self):
        """Test validation of valid penalties."""
        penalties_dict = {
            'penalties[0][name]': ['Late Penalty'],
            'penalties[0][value]': ['-5'],
            'penalties[0][stackable]': ['on'],
            'penalties[1][name]': ['Wrong Answer'],
            'penalties[1][value]': ['-10']
        }

        penalties, error = validate_penalties_list(penalties_dict)

        assert error is None
        assert len(penalties) == 2
        assert penalties[0]['name'] == 'Late Penalty'
        assert penalties[0]['value'] == -5
        assert penalties[0]['stackable'] is True
        assert penalties[1]['name'] == 'Wrong Answer'
        assert penalties[1]['value'] == -10
        assert penalties[1]['stackable'] is False

    def test_empty_penalties_list(self):
        """Test validation with no penalties."""
        penalties_dict = {}

        penalties, error = validate_penalties_list(penalties_dict)

        assert error is None
        assert penalties == []

    def test_penalty_name_too_short(self):
        """Test penalty name below minimum length."""
        penalties_dict = {
            'penalties[0][name]': [''],
            'penalties[0][value]': ['-5']
        }

        penalties, error = validate_penalties_list(penalties_dict)

        assert penalties is None
        assert error is not None
        assert "Penalty name" in error

    def test_penalty_name_too_long(self):
        """Test penalty name exceeding maximum length."""
        long_name = "X" * (PENALTY_NAME_MAX + 1)
        penalties_dict = {
            'penalties[0][name]': [long_name],
            'penalties[0][value]': ['-5']
        }

        penalties, error = validate_penalties_list(penalties_dict)

        assert penalties is None
        assert error is not None
        assert "Penalty name" in error

    def test_penalty_value_below_min(self):
        """Test penalty value below minimum."""
        penalties_dict = {
            'penalties[0][name]': ['Big Penalty'],
            'penalties[0][value]': [str(PENALTY_VALUE_MIN - 1)]
        }

        penalties, error = validate_penalties_list(penalties_dict)

        assert penalties is None
        assert error is not None
        assert "Penalty value" in error

    def test_penalty_value_above_max(self):
        """Test penalty value above maximum."""
        penalties_dict = {
            'penalties[0][name]': ['Huge Bonus'],
            'penalties[0][value]': [str(PENALTY_VALUE_MAX + 1)]
        }

        penalties, error = validate_penalties_list(penalties_dict)

        assert penalties is None
        assert error is not None
        assert "Penalty value" in error

    def test_penalty_value_overflow(self):
        """Test penalty value causing integer overflow."""
        penalties_dict = {
            'penalties[0][name]': ['Overflow'],
            'penalties[0][value]': ['99999999999999999999999999999']
        }

        penalties, error = validate_penalties_list(penalties_dict)

        assert penalties is None
        assert error is not None
        assert ("invalid or too large" in error.lower() or "between" in error.lower())

    def test_penalty_value_invalid_format(self):
        """Test penalty with invalid value format."""
        penalties_dict = {
            'penalties[0][name]': ['Test'],
            'penalties[0][value]': ['not a number']
        }

        penalties, error = validate_penalties_list(penalties_dict)

        assert penalties is None
        assert error is not None

    def test_penalty_name_with_special_characters(self):
        """Test penalty name with special characters."""
        penalties_dict = {
            'penalties[0][name]': ['Penalty!@#$%'],
            'penalties[0][value]': ['-5']
        }

        penalties, error = validate_penalties_list(penalties_dict)

        assert error is None
        assert penalties[0]['name'] == 'Penalty!@#$%'

    def test_penalty_name_sql_injection(self):
        """Test penalty name with SQL injection attempt."""
        penalties_dict = {
            'penalties[0][name]': ["'; DROP TABLE penalties; --"],
            'penalties[0][value]': ['-5']
        }

        penalties, error = validate_penalties_list(penalties_dict)

        # Should pass validation (sanitization happens at DB layer)
        assert error is None

    def test_penalty_name_xss_attempt(self):
        """Test penalty name with XSS attempt."""
        penalties_dict = {
            'penalties[0][name]': ["<script>alert('XSS')</script>"],
            'penalties[0][value]': ['-5']
        }

        penalties, error = validate_penalties_list(penalties_dict)

        # Should pass validation (escaping happens at template layer)
        assert error is None

    def test_multiple_penalties_with_mixed_validity(self):
        """Test that first invalid penalty stops validation."""
        penalties_dict = {
            'penalties[0][name]': ['Valid'],
            'penalties[0][value]': ['-5'],
            'penalties[1][name]': [''],  # Invalid
            'penalties[1][value]': ['-10'],
            'penalties[2][name]': ['Also Valid'],
            'penalties[2][value]': ['-3']
        }

        penalties, error = validate_penalties_list(penalties_dict)

        assert penalties is None
        assert error is not None


@pytest.mark.unit
@pytest.mark.validators
class TestExtractPenaltiesFromForm:
    """Test suite for extracting penalties from form (for re-display)."""

    def test_extract_valid_penalties(self):
        """Test extracting valid penalties."""
        penalties_dict = {
            'penalties[0][name]': ['Test'],
            'penalties[0][value]': ['-5'],
            'penalties[0][stackable]': ['on']
        }

        penalties = extract_penalties_from_form(penalties_dict)

        assert len(penalties) == 1
        assert penalties[0]['name'] == 'Test'
        assert penalties[0]['value'] == -5
        assert penalties[0]['stackable'] is True

    def test_extract_invalid_value_keeps_as_string(self):
        """Test that invalid values are kept as strings for display."""
        penalties_dict = {
            'penalties[0][name]': ['Test'],
            'penalties[0][value]': ['not a number']
        }

        penalties = extract_penalties_from_form(penalties_dict)

        assert penalties[0]['value'] == 'not a number'

    def test_extract_overflow_value_keeps_as_string(self):
        """Test overflow value is kept as string."""
        penalties_dict = {
            'penalties[0][name]': ['Test'],
            'penalties[0][value]': ['99999999999999999999']
        }

        penalties = extract_penalties_from_form(penalties_dict)

        assert penalties[0]['value'] == '99999999999999999999'

    def test_extract_malformed_entry_skipped(self):
        """Test that malformed entries are skipped."""
        penalties_dict = {
            'penalties[0][name]': ['Valid'],
            'penalties[0][value]': ['-5'],
            'penalties[1][name]': ['Missing Value']
            # Missing penalties[1][value]
        }

        penalties = extract_penalties_from_form(penalties_dict)

        # Should extract what's possible
        assert len(penalties) <= 2


@pytest.mark.unit
@pytest.mark.validators
class TestErrorMessages:
    """Test suite for error message generation."""

    def test_length_error_message_range(self):
        """Test length error message with min and max."""
        msg = get_length_error_message("Name", 3, 50)
        assert "Name" in msg
        assert "3" in msg
        assert "50" in msg
        assert "between" in msg

    def test_length_error_message_exact(self):
        """Test length error message for exact length."""
        msg = get_length_error_message("Code", 7, 7)
        assert "exactly 7" in msg

    def test_length_error_message_min_one(self):
        """Test length error message with min of 1."""
        msg = get_length_error_message("Name", 1, 50)
        assert "must not exceed" in msg
        assert "50" in msg

    def test_range_error_message(self):
        """Test numeric range error message."""
        msg = get_range_error_message("Score", -100, 100)
        assert "Score" in msg
        assert "-100" in msg
        assert "100" in msg
        assert "between" in msg

    def test_range_error_message_with_large_numbers(self):
        """Test range error with comma formatting."""
        msg = get_range_error_message("Value", -999999, 999999)
        assert "999,999" in msg or "999999" in msg


@pytest.mark.unit
@pytest.mark.validators
class TestValidationConstants:
    """Test suite to verify validation constants are sane."""

    def test_team_name_constraints(self):
        """Test team name constraints are valid."""
        assert TEAM_NAME_MIN >= 1
        assert TEAM_NAME_MAX >= TEAM_NAME_MIN
        assert TEAM_NAME_MAX <= 200

    def test_score_constraints(self):
        """Test score value constraints."""
        assert SCORE_VALUE_MIN < 0
        assert SCORE_VALUE_MAX > 0
        assert SCORE_VALUE_MAX >= 999999

    def test_penalty_constraints(self):
        """Test penalty value constraints."""
        assert PENALTY_VALUE_MIN < 0
        assert PENALTY_VALUE_MAX > 0
        assert abs(PENALTY_VALUE_MIN) == PENALTY_VALUE_MAX

    def test_point_multiplier_constraints(self):
        """Test point multiplier constraints."""
        assert POINT_MULTIPLIER_MIN >= 1
        assert POINT_MULTIPLIER_MAX >= POINT_MULTIPLIER_MIN


@pytest.mark.unit
@pytest.mark.validators
class TestBoundaryConditions:
    """Comprehensive boundary condition tests."""

    def test_string_exactly_at_boundaries(self):
        """Test strings exactly at min and max boundaries."""
        # At min
        is_valid, _ = validate_string_length("A", "Name", 1, 50)
        assert is_valid is True

        # One below min
        is_valid, _ = validate_string_length("", "Name", 1, 50)
        assert is_valid is False

        # At max
        is_valid, _ = validate_string_length("X" * 50, "Name", 1, 50)
        assert is_valid is True

        # One above max
        is_valid, _ = validate_string_length("X" * 51, "Name", 1, 50)
        assert is_valid is False

    def test_numeric_exactly_at_boundaries(self):
        """Test numeric values exactly at boundaries."""
        # At min
        is_valid, _ = validate_numeric_range(-999999.99, "Score", -999999.99, 999999.99)
        assert is_valid is True

        # Just below min
        is_valid, _ = validate_numeric_range(-1000000, "Score", -999999.99, 999999.99)
        assert is_valid is False

        # At max
        is_valid, _ = validate_numeric_range(999999.99, "Score", -999999.99, 999999.99)
        assert is_valid is True

        # Just above max
        is_valid, _ = validate_numeric_range(1000000, "Score", -999999.99, 999999.99)
        assert is_valid is False

    def test_integer_exactly_at_boundaries(self):
        """Test integers exactly at boundaries."""
        # At min
        is_valid, _ = validate_integer_range(1, "Points", 1, 100)
        assert is_valid is True

        # Just below min
        is_valid, _ = validate_integer_range(0, "Points", 1, 100)
        assert is_valid is False

        # At max
        is_valid, _ = validate_integer_range(100, "Points", 1, 100)
        assert is_valid is True

        # Just above max
        is_valid, _ = validate_integer_range(101, "Points", 1, 100)
        assert is_valid is False

    def test_penalty_at_exact_boundaries(self):
        """Test penalty values at exact boundaries."""
        # At min
        penalties_dict = {
            'penalties[0][name]': ['Test'],
            'penalties[0][value]': [str(PENALTY_VALUE_MIN)]
        }
        penalties, error = validate_penalties_list(penalties_dict)
        assert error is None

        # At max
        penalties_dict = {
            'penalties[0][name]': ['Test'],
            'penalties[0][value]': [str(PENALTY_VALUE_MAX)]
        }
        penalties, error = validate_penalties_list(penalties_dict)
        assert error is None


@pytest.mark.unit
@pytest.mark.validators
class TestSecurityValidation:
    """Security-focused validation tests."""

    def test_sql_injection_strings(self):
        """Test various SQL injection attempts."""
        sql_attempts = [
            "'; DROP TABLE teams; --",
            "' OR '1'='1",
            "admin'--",
            "1' UNION SELECT * FROM users--"
        ]

        for attempt in sql_attempts:
            # Length validation should pass (sanitization happens elsewhere)
            is_valid, _ = validate_string_length(attempt, "Name", 1, 200)
            # Will pass if within length limits
            if len(attempt) <= 200:
                assert is_valid is True

    def test_xss_injection_strings(self):
        """Test various XSS attempts."""
        xss_attempts = [
            "<script>alert('XSS')</script>",
            "<img src=x onerror=alert('XSS')>",
            "javascript:alert('XSS')",
            "<iframe src='evil.com'>"
        ]

        for attempt in xss_attempts:
            is_valid, _ = validate_string_length(attempt, "Name", 1, 200)
            if len(attempt) <= 200:
                assert is_valid is True

    def test_path_traversal_attempts(self):
        """Test path traversal attempts."""
        traversal_attempts = [
            "../../../etc/passwd",
            "..\\..\\..\\windows\\system32",
            "%2e%2e%2f%2e%2e%2f"
        ]

        for attempt in traversal_attempts:
            is_valid, _ = validate_string_length(attempt, "Name", 1, 200)
            if len(attempt) <= 200:
                assert is_valid is True

    def test_command_injection_attempts(self):
        """Test command injection attempts."""
        cmd_attempts = [
            "; rm -rf /",
            "| cat /etc/passwd",
            "& del *.*"
        ]

        for attempt in cmd_attempts:
            is_valid, _ = validate_string_length(attempt, "Name", 1, 200)
            if len(attempt) <= 200:
                assert is_valid is True

    def test_unicode_normalization_attacks(self):
        """Test unicode normalization attacks."""
        unicode_attempts = [
            "\u202e",  # Right-to-left override
            "\u0000",  # Null byte
            "Test\u200bName"  # Zero-width space
        ]

        for attempt in unicode_attempts:
            is_valid, _ = validate_string_length(attempt, "Name", 1, 200)
            # Should handle unicode gracefully
