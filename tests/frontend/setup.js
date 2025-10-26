/**
 * Vitest Setup File
 * Configures global test environment and mocks
 */

import { beforeEach, vi } from 'vitest';

// Mock global objects that might be used in the browser
global.localStorage = {
  getItem: vi.fn(),
  setItem: vi.fn(),
  removeItem: vi.fn(),
  clear: vi.fn()
};

global.sessionStorage = {
  getItem: vi.fn(),
  setItem: vi.fn(),
  removeItem: vi.fn(),
  clear: vi.fn()
};

// Mock console methods to reduce noise in test output
global.console = {
  ...console,
  log: vi.fn(),
  warn: vi.fn(),
  error: vi.fn()
};

// Reset all mocks before each test
beforeEach(() => {
  vi.clearAllMocks();
});
