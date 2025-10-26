/**
 * Centralized API service for making HTTP requests to the backend.
 * Handles CSRF tokens, error handling, and response parsing.
 */

export class ApiService {
  constructor() {
    this.csrfToken = this.getCSRFToken();
  }

  /**
   * Get CSRF token from meta tag or cookie
   */
  getCSRFToken() {
    const meta = document.querySelector('meta[name="csrf-token"]');
    if (meta) {
      return meta.getAttribute('content');
    }

    // Fallback to cookie
    const name = 'csrf_token=';
    const decodedCookie = decodeURIComponent(document.cookie);
    const cookies = decodedCookie.split(';');

    for (let cookie of cookies) {
      cookie = cookie.trim();
      if (cookie.indexOf(name) === 0) {
        return cookie.substring(name.length);
      }
    }
    return null;
  }

  /**
   * Make a GET request
   */
  async get(url, options = {}) {
    return this.request(url, {
      ...options,
      method: 'GET',
    });
  }

  /**
   * Make a POST request
   */
  async post(url, data, options = {}) {
    return this.request(url, {
      ...options,
      method: 'POST',
      body: data,
    });
  }

  /**
   * Make a PUT request
   */
  async put(url, data, options = {}) {
    return this.request(url, {
      ...options,
      method: 'PUT',
      body: data,
    });
  }

  /**
   * Make a DELETE request
   */
  async delete(url, options = {}) {
    return this.request(url, {
      ...options,
      method: 'DELETE',
    });
  }

  /**
   * Make a generic request
   */
  async request(url, options = {}) {
    const headers = {
      'X-Requested-With': 'XMLHttpRequest',
      ...options.headers,
    };

    // Add CSRF token for non-GET requests
    if (options.method !== 'GET' && this.csrfToken) {
      headers['X-CSRFToken'] = this.csrfToken;
    }

    // Handle different body types
    let body = options.body;
    if (body && !(body instanceof FormData)) {
      if (typeof body === 'object') {
        headers['Content-Type'] = 'application/json';
        body = JSON.stringify(body);
      }
    }

    const config = {
      ...options,
      headers,
      body,
      credentials: 'same-origin',
    };

    try {
      const response = await fetch(url, config);

      // Handle non-OK responses
      if (!response.ok) {
        const error = new Error(`HTTP error! status: ${response.status}`);
        error.response = response;
        error.status = response.status;

        // Try to parse error message from response
        try {
          const data = await response.json();
          error.message = data.message || data.error || error.message;
          error.data = data;
        } catch (e) {
          // Response is not JSON, use default message
        }

        throw error;
      }

      // Parse response based on content type
      const contentType = response.headers.get('content-type');
      if (contentType && contentType.includes('application/json')) {
        return await response.json();
      }

      return await response.text();

    } catch (error) {
      console.error('API request failed:', error);
      throw error;
    }
  }

  /**
   * Submit form data as multipart/form-data
   */
  async submitForm(url, formData) {
    return this.post(url, formData, {
      // Don't set Content-Type header, browser will set it with boundary
      headers: {},
    });
  }
}

// Export singleton instance
export const apiService = new ApiService();
