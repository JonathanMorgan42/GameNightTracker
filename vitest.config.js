import { defineConfig } from 'vitest/config';


export default defineConfig({
  test: {
    environment: 'jsdom',
    globals: true,
    setupFiles: ['./tests/frontend/setup.js'],
    coverage: {
      provider: 'v8',
      reporter: ['text', 'html', 'lcov'],
      include: ['app/static/js/**/*.js'],
      exclude: [
        'node_modules/**',
        'tests/**',
        '**/*.config.js',
        '**/dist/**'
      ],
      all: true,
      lines: 70,
      functions: 70,
      branches: 70,
      statements: 70
    },
    testMatch: ['**/tests/frontend/**/*.test.js'],
    mockReset: true,
    clearMocks: true,
    restoreMocks: true
  }
});
