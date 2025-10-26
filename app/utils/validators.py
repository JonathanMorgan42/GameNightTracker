"""
Centralized validation utilities for GameNight application.

This module provides validation constants and helper functions to ensure
all user inputs conform to database constraints and business rules.
"""

# ============================================================================
# STRING LENGTH CONSTRAINTS (based on database schema)
# ============================================================================

# Team constraints
TEAM_NAME_MIN = 1
TEAM_NAME_MAX = 50  # Reduced from 100 to prevent CSS issues
TEAM_COLOR_LENGTH = 7  # Hex color format: #RRGGBB

# Game constraints
GAME_NAME_MIN = 1
GAME_NAME_MAX = 50  # Reduced from 100 to prevent CSS issues
GAME_TYPE_MAX = 50
GAME_CUSTOM_TYPE_MAX = 50

# Participant constraints
PARTICIPANT_NAME_MIN = 1
PARTICIPANT_NAME_MAX = 50  # Reduced from 100 to prevent CSS issues

# Penalty constraints
PENALTY_NAME_MIN = 1
PENALTY_NAME_MAX = 100  # Reduced from 200 to prevent CSS issues

# Game Night constraints
GAME_NIGHT_NAME_MIN = 3
GAME_NIGHT_NAME_MAX = 100  # Reduced from 200 for consistency

# Score constraints
SCORE_NOTES_MAX = 500  # Reduced from 5000 for reasonable input size

# ============================================================================
# NUMERIC RANGE CONSTRAINTS
# ============================================================================

# Point scheme / multiplier constraints
POINT_MULTIPLIER_MIN = 1
POINT_MULTIPLIER_MAX = 100

# Penalty value constraints
PENALTY_VALUE_MIN = -999999
PENALTY_VALUE_MAX = 999999

# Score value constraints
SCORE_VALUE_MIN = -999999.99
SCORE_VALUE_MAX = 999999.99

# Sequence number constraints
SEQUENCE_NUMBER_MIN = 0
SEQUENCE_NUMBER_MAX = 9999

# Tournament match score constraints
MATCH_SCORE_MIN = -999999.99
MATCH_SCORE_MAX = 999999.99


# ============================================================================
# VALIDATION ERROR MESSAGES
# ============================================================================

def get_length_error_message(field_name, min_length, max_length):
    """Generate a consistent length validation error message."""
    if min_length == max_length:
        return f'{field_name} must be exactly {max_length} characters'
    elif min_length == 1:
        return f'{field_name} must not exceed {max_length} characters'
    else:
        return f'{field_name} must be between {min_length} and {max_length} characters'


def get_range_error_message(field_name, min_value, max_value):
    """Generate a consistent numeric range validation error message."""
    return f'{field_name} must be between {min_value:,} and {max_value:,}'


# ============================================================================
# BACKEND VALIDATION HELPERS
# ============================================================================

def validate_string_length(value, field_name, min_length, max_length):
    """
    Validate string length for backend processing.

    Args:
        value: String value to validate
        field_name: Name of the field (for error messages)
        min_length: Minimum allowed length
        max_length: Maximum allowed length

    Returns:
        tuple: (is_valid: bool, error_message: str or None)
    """
    if value is None:
        return False, f'{field_name} is required'

    value_str = str(value).strip()
    length = len(value_str)

    if length < min_length:
        return False, f'{field_name} is too short (minimum {min_length} characters)'
    if length > max_length:
        return False, f'{field_name} exceeds maximum length of {max_length} characters'

    return True, None


def validate_numeric_range(value, field_name, min_value, max_value, allow_none=False):
    """
    Validate numeric value is within acceptable range.

    Args:
        value: Numeric value to validate
        field_name: Name of the field (for error messages)
        min_value: Minimum allowed value
        max_value: Maximum allowed value
        allow_none: Whether None/null values are acceptable

    Returns:
        tuple: (is_valid: bool, error_message: str or None)
    """
    if value is None:
        if allow_none:
            return True, None
        return False, f'{field_name} is required'

    try:
        numeric_value = float(value)
    except (ValueError, TypeError):
        return False, f'{field_name} must be a valid number'

    import math
    if math.isnan(numeric_value) or math.isinf(numeric_value):
        return False, f'{field_name} must be a valid number'

    if numeric_value < min_value or numeric_value > max_value:
        return False, get_range_error_message(field_name, min_value, max_value)

    return True, None


def validate_integer_range(value, field_name, min_value, max_value, allow_none=False):
    """
    Validate integer value is within acceptable range.

    Args:
        value: Integer value to validate
        field_name: Name of the field (for error messages)
        min_value: Minimum allowed value
        max_value: Maximum allowed value
        allow_none: Whether None/null values are acceptable

    Returns:
        tuple: (is_valid: bool, error_message: str or None)
    """
    if value is None:
        if allow_none:
            return True, None
        return False, f'{field_name} is required'

    try:
        int_value = int(value)
    except (ValueError, TypeError):
        return False, f'{field_name} must be a valid integer'

    if int_value < min_value or int_value > max_value:
        return False, get_range_error_message(field_name, min_value, max_value)

    return True, None


def validate_penalties_list(penalties_dict):
    """
    Validate penalty data from form submission.

    Args:
        penalties_dict: Dictionary from request.form.to_dict(flat=False)

    Returns:
        tuple: (penalties_data list or None, error_message string or None)
    """
    penalties_data = []
    penalty_count = 0

    while f'penalties[{penalty_count}][name]' in penalties_dict:
        try:
            penalty_name = penalties_dict[f'penalties[{penalty_count}][name]'][0]
            penalty_value = penalties_dict[f'penalties[{penalty_count}][value]'][0]

            # Validate penalty name length
            is_valid, error = validate_string_length(
                penalty_name, 'Penalty name', PENALTY_NAME_MIN, PENALTY_NAME_MAX
            )
            if not is_valid:
                return None, error

            # Validate penalty value with overflow protection
            is_valid, error = validate_integer_range(
                penalty_value, 'Penalty value', PENALTY_VALUE_MIN, PENALTY_VALUE_MAX
            )
            if not is_valid:
                return None, error

            # Additional check for extreme overflow that could crash int() conversion
            try:
                penalty_value_int = int(penalty_value)
            except (ValueError, OverflowError) as e:
                return None, f'Penalty value at position {penalty_count + 1} is invalid or too large'

            penalty = {
                'name': penalty_name.strip(),
                'value': penalty_value_int,
                'stackable': f'penalties[{penalty_count}][stackable]' in penalties_dict
            }
            penalties_data.append(penalty)

        except (ValueError, TypeError, KeyError, OverflowError) as e:
            return None, f'Invalid penalty data at position {penalty_count + 1}: Value may be too large'

        penalty_count += 1

    return penalties_data, None


def extract_penalties_from_form(penalties_dict):
    """
    Extract penalty data from form for re-display (even if invalid).
    Used when validation fails and we need to show what the user entered.

    Args:
        penalties_dict: Dictionary from request.form.to_dict(flat=False)

    Returns:
        list: List of penalty dictionaries with name, value, and stackable fields
    """
    penalties_data = []
    penalty_count = 0

    while f'penalties[{penalty_count}][name]' in penalties_dict:
        try:
            penalty_name = penalties_dict[f'penalties[{penalty_count}][name]'][0]
            penalty_value_raw = penalties_dict[f'penalties[{penalty_count}][value]'][0]

            # Try to convert to int, but keep as string if it fails or would overflow
            try:
                # Check if value would cause overflow before converting
                if penalty_value_raw and len(str(penalty_value_raw)) >= 20:
                    penalty_value = penalty_value_raw
                else:
                    penalty_value = int(penalty_value_raw) if penalty_value_raw else ''
            except (ValueError, OverflowError):
                penalty_value = penalty_value_raw

            penalty = {
                'name': penalty_name,
                'value': penalty_value,
                'stackable': f'penalties[{penalty_count}][stackable]' in penalties_dict
            }
            penalties_data.append(penalty)

        except (KeyError, IndexError):
            pass

        penalty_count += 1

    return penalties_data
