/**
 * Simple state management service for application-wide state.
 * Provides reactive updates and event-driven state changes.
 */

export class StateService {
  constructor() {
    this.state = {};
    this.subscribers = new Map();
  }

  /**
   * Get state value by key
   */
  get(key) {
    return this.state[key];
  }

  /**
   * Set state value and notify subscribers
   */
  set(key, value) {
    const oldValue = this.state[key];

    // Don't update if value hasn't changed
    if (oldValue === value) {
      return;
    }

    this.state[key] = value;
    this.notify(key, value, oldValue);
  }

  /**
   * Update multiple state values at once
   */
  update(updates) {
    Object.entries(updates).forEach(([key, value]) => {
      this.set(key, value);
    });
  }

  /**
   * Subscribe to state changes for a specific key
   */
  subscribe(key, callback) {
    if (!this.subscribers.has(key)) {
      this.subscribers.set(key, []);
    }

    this.subscribers.get(key).push(callback);

    // Return unsubscribe function
    return () => {
      const callbacks = this.subscribers.get(key);
      const index = callbacks.indexOf(callback);
      if (index > -1) {
        callbacks.splice(index, 1);
      }
    };
  }

  /**
   * Notify subscribers of state change
   */
  notify(key, newValue, oldValue) {
    if (!this.subscribers.has(key)) {
      return;
    }

    this.subscribers.get(key).forEach(callback => {
      try {
        callback(newValue, oldValue);
      } catch (error) {
        console.error(`Error in state subscriber for key "${key}":`, error);
      }
    });
  }

  /**
   * Clear all state
   */
  clear() {
    this.state = {};
    this.subscribers.clear();
  }

  /**
   * Get all state
   */
  getAll() {
    return { ...this.state };
  }
}

// Export singleton instance
export const stateService = new StateService();
