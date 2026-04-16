/**
 * Logger Utility
 *
 * Simple structured logging for WPIL
 */

const LOG_LEVEL = process.env.LOG_LEVEL || "info";

const LEVELS = {
  debug: 0,
  info: 1,
  warn: 2,
  error: 3
};

const currentLevel = LEVELS[LOG_LEVEL] || LEVELS.info;

function formatMessage(level, message, meta = {}) {
  const timestamp = new Date().toISOString();
  const metaStr = Object.keys(meta).length > 0 ? ` ${JSON.stringify(meta)}` : "";
  return `[${timestamp}] [${level.toUpperCase()}] ${message}${metaStr}`;
}

export const logger = {
  debug(message, meta = {}) {
    if (currentLevel <= LEVELS.debug) {
      console.log(formatMessage("debug", message, meta));
    }
  },

  info(message, meta = {}) {
    if (currentLevel <= LEVELS.info) {
      console.log(formatMessage("info", message, meta));
    }
  },

  warn(message, meta = {}) {
    if (currentLevel <= LEVELS.warn) {
      console.warn(formatMessage("warn", message, meta));
    }
  },

  error(message, meta = {}) {
    if (currentLevel <= LEVELS.error) {
      console.error(formatMessage("error", message, meta));
    }
  }
};

export default logger;
