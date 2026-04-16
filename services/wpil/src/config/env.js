/**
 * Environment Configuration
 *
 * Centralized config for WPIL
 */

export const config = {
  // Server
  PORT: process.env.PORT || 4000,
  HOST: process.env.HOST || "0.0.0.0",

  // WINDI Verify endpoint
  VERIFY_BASE_URL: process.env.WINDI_VERIFY_URL || "https://windi-domain.com/verify-public/api/verify",

  // WPIL Mode
  MODE: process.env.WPIL_MODE || "relay", // relay | local
  SKIP_REMOTE: process.env.WPIL_SKIP_REMOTE === "true",

  // Logging
  LOG_LEVEL: process.env.LOG_LEVEL || "info"
};

export default config;
