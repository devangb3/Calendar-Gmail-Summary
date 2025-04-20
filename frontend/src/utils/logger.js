// Configure log levels
const LOG_LEVELS = {
  ERROR: 'ERROR',
  WARN: 'WARN',
  INFO: 'INFO',
  DEBUG: 'DEBUG'
};

class Logger {
  constructor() {
    this.logs = [];
    this.maxLogs = 1000; // Keep last 1000 logs in memory
  }

  log(level, message, data = null) {
    const timestamp = new Date().toISOString();
    const logEntry = {
      timestamp,
      level,
      message,
      data
    };

    // Add to memory logs
    this.logs.push(logEntry);
    if (this.logs.length > this.maxLogs) {
      this.logs.shift(); // Remove oldest log if we exceed maxLogs
    }

    // Format the console output
    const consoleMessage = `[${timestamp}] [${level}] ${message}`;
    
    // Log to console based on environment and level
    if (process.env.NODE_ENV !== 'production' || level === LOG_LEVELS.ERROR) {
      switch (level) {
        case LOG_LEVELS.ERROR:
          console.error(consoleMessage, data || '');
          break;
        case LOG_LEVELS.WARN:
          console.warn(consoleMessage, data || '');
          break;
        case LOG_LEVELS.INFO:
          console.info(consoleMessage, data || '');
          break;
        case LOG_LEVELS.DEBUG:
          console.debug(consoleMessage, data || '');
          break;
        default:
          console.log(consoleMessage, data || '');
      }
    }

    // In production, send errors to your error tracking service if available
    if (process.env.NODE_ENV === 'production' && level === LOG_LEVELS.ERROR) {
      // TODO: Implement error tracking service integration
      // Example: Sentry.captureException(data);
    }
  }

  error(message, error = null) {
    this.log(LOG_LEVELS.ERROR, message, error);
  }

  warn(message, data = null) {
    this.log(LOG_LEVELS.WARN, message, data);
  }

  info(message, data = null) {
    this.log(LOG_LEVELS.INFO, message, data);
  }

  debug(message, data = null) {
    this.log(LOG_LEVELS.DEBUG, message, data);
  }

  getLogs() {
    return [...this.logs];
  }
}

export const logger = new Logger();
export default logger;