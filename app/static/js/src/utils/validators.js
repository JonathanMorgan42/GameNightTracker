/**
 * Form validation utilities
 */

/**
 * Validate required field
 */
export function validateRequired(value, fieldName = 'Field') {
  if (!value || value.trim() === '') {
    return { valid: false, message: `${fieldName} is required` };
  }
  return { valid: true };
}

/**
 * Validate email format
 */
export function validateEmail(email) {
  const emailRegex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
  if (!emailRegex.test(email)) {
    return { valid: false, message: 'Invalid email format' };
  }
  return { valid: true };
}

/**
 * Validate number in range
 */
export function validateNumber(value, min = null, max = null) {
  const num = parseFloat(value);

  if (isNaN(num)) {
    return { valid: false, message: 'Must be a valid number' };
  }

  if (min !== null && num < min) {
    return { valid: false, message: `Must be at least ${min}` };
  }

  if (max !== null && num > max) {
    return { valid: false, message: `Must be at most ${max}` };
  }

  return { valid: true };
}

/**
 * Validate integer
 */
export function validateInteger(value) {
  const num = parseInt(value, 10);

  if (isNaN(num) || num.toString() !== value.toString()) {
    return { valid: false, message: 'Must be a whole number' };
  }

  return { valid: true };
}

/**
 * Validate string length
 */
export function validateLength(value, min = null, max = null) {
  const length = value ? value.length : 0;

  if (min !== null && length < min) {
    return { valid: false, message: `Must be at least ${min} characters` };
  }

  if (max !== null && length > max) {
    return { valid: false, message: `Must be at most ${max} characters` };
  }

  return { valid: true };
}

/**
 * Validate hex color
 */
export function validateHexColor(color) {
  const hexRegex = /^#([A-Fa-f0-9]{6}|[A-Fa-f0-9]{3})$/;

  if (!hexRegex.test(color)) {
    return { valid: false, message: 'Invalid color format (use #RRGGBB)' };
  }

  return { valid: true };
}

/**
 * Validate form field with multiple rules
 */
export function validateField(value, rules) {
  for (const rule of rules) {
    const result = rule(value);
    if (!result.valid) {
      return result;
    }
  }

  return { valid: true };
}

/**
 * Display validation error on form field
 */
export function showFieldError(fieldElement, message) {
  if (!fieldElement) return;

  // Remove existing error
  clearFieldError(fieldElement);

  // Add error class
  fieldElement.classList.add('is-invalid');

  // Create and add error message
  const errorDiv = document.createElement('div');
  errorDiv.className = 'invalid-feedback';
  errorDiv.textContent = message;

  fieldElement.parentNode.appendChild(errorDiv);
}

/**
 * Clear validation error from form field
 */
export function clearFieldError(fieldElement) {
  if (!fieldElement) return;

  fieldElement.classList.remove('is-invalid');

  const errorDiv = fieldElement.parentNode.querySelector('.invalid-feedback');
  if (errorDiv) {
    errorDiv.remove();
  }
}

/**
 * Clear all validation errors in form
 */
export function clearFormErrors(formElement) {
  if (!formElement) return;

  const invalidFields = formElement.querySelectorAll('.is-invalid');
  invalidFields.forEach(field => clearFieldError(field));
}
