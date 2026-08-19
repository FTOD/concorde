const {defineConfig} = require('vitest/config') as typeof import('vitest/config');

module.exports = defineConfig({
  test: {
    environment: 'node',
    globals: true,
    setupFiles: ['./tests/setup.ts'],
    testTimeout: 30_000,
  },
});
