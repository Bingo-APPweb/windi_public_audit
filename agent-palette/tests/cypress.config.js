// ═══════════════════════════════════════════════════════════════════════════
// WINDI Palette — Cypress Configuration
// ═══════════════════════════════════════════════════════════════════════════

const { defineConfig } = require('cypress');

module.exports = defineConfig({
  e2e: {
    baseUrl: 'http://localhost:8108',
    specPattern: 'cypress/e2e/**/*.cy.{js,jsx,ts,tsx}',
    supportFile: false,
    viewportWidth: 1280,
    viewportHeight: 800,
    video: false,
    screenshotOnRunFailure: true,
    defaultCommandTimeout: 10000,
    requestTimeout: 30000,
    responseTimeout: 30000,

    env: {
      BASE_URL: 'http://localhost:8108',
      HANDOVER_THRESHOLD_MS: 200
    },

    setupNodeEvents(on, config) {
      on('task', {
        log(message) {
          console.log(message);
          return null;
        }
      });
    }
  },

  // Reporter configuration
  reporter: 'spec',
  reporterOptions: {
    toConsole: true
  }
});
