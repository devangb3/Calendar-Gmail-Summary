import axios from 'axios';
import logger from './logger';

// Use environment variables with production URL fallback for Render deployment
const API_URL = process.env.REACT_APP_API_URL || 'https://calendar-gmail-backend.onrender.com';
const FRONTEND_URL = process.env.REACT_APP_FRONTEND_URL || 'https://calendar-gmail-summary-frontend.onrender.com';

// Custom error class for API errors
class ApiError extends Error {
  constructor(message, status, details = null) {
    super(message);
    this.name = 'ApiError';
    this.status = status;
    this.details = details;
  }
}

const api = axios.create({
  baseURL: API_URL,
  withCredentials: true,
  headers: {
    'Content-Type': 'application/json',
  },
  timeout: 60000, // Increased to 45 second timeout
});

// Add a request interceptor to handle before request is sent
api.interceptors.request.use(
  (config) => {
    logger.info(`API Request: ${config.method?.toUpperCase()} ${config.url}`, {
      headers: config.headers,
      params: config.params,
      data: config.data
    });
    return config;
  },
  (error) => {
    logger.error('API Request Error:', error);
    return Promise.reject(new ApiError('Request failed', 0, error));
  }
);

// Add a response interceptor for common error handling
api.interceptors.response.use(
  (response) => {
    logger.info(`API Response: ${response.status} ${response.config.url}`, {
      status: response.status,
      data: response.data
    });

    // Handle successful authentication redirect
    if (response.data?.redirect_url) {
      window.location.replace(response.data.redirect_url);
      return;
    }
    return response;
  },
  (error) => {
    logger.error('API Response Error:', {
      url: error.config?.url,
      status: error.response?.status,
      data: error.response?.data,
      message: error.message
    });

    if (error.response) {
      // The request was made and the server responded with a status code
      // that falls out of the range of 2xx
      const errorMessage = error.response.data?.message || error.response.data?.error || 'An error occurred';
      const status = error.response.status;

      if (status === 401) {
        // Redirect to login on authentication errors
        window.location.replace(`${FRONTEND_URL}/login`);
      }

      return Promise.reject(new ApiError(errorMessage, status, error.response.data));
    } else if (error.request) {
      // The request was made but no response was received
      return Promise.reject(new ApiError('No response from server', 0));
    } else {
      // Something happened in setting up the request that triggered an Error
      return Promise.reject(new ApiError('Failed to send request', 0));
    }
  }
);

// API endpoints
export const auth = {
  login: () => {
    logger.info('Initiating login request');
    return api.get('/auth/login'); // Updated path
  },
  logout: () => {
    logger.info('Initiating logout request');
    return api.get('/auth/logout'); // Updated path
  },
  check: () => {
    logger.debug('Checking authentication status via API');
    // Use axios instance and correct backend endpoint
    return api.get('/auth/check'); 
  }
};

export const summary = {
  get: (forceRefresh = false) => {
    logger.info('Fetching summary', { forceRefresh });
    return api.get('/api/summary' + (forceRefresh ? '?refresh=true' : ''));
  },
  getSmartReplies: (threadId) => {
    logger.info('Fetching smart replies for thread:', threadId);
    return api.get(`/api/smart-replies/${threadId}`);
  },
  sendReply: (data) => {
    logger.info('Sending email reply');
    return api.post('/api/send-reply', data);
  },
  getAudioSummary: () => {
    logger.info('Fetching audio summary');
    return fetch(`${API_URL}/api/audio-summary`, {
      method: 'GET',
      credentials: 'include',
      headers: {
        'Accept': 'audio/mpeg'
      }
    });
  }
};

export const calendar = {
  getPendingInvites: () => {
    logger.info('Fetching pending calendar invites');
    return api.get('/api/pending-invites');
  },
  acceptInvite: (eventId) => {
    logger.info('Accepting calendar invite:', eventId);
    return api.post(`/api/accept-invite/${eventId}`);
  },
  declineInvite: (eventId) => {
    logger.info('Declining calendar invite:', eventId);
    return api.post(`/api/decline-invite/${eventId}`);
  }
};

// Helper function to check if error is an API error
export const isApiError = (error) => {
  return error instanceof ApiError || error?.isAxiosError || error?.response !== undefined;
};

// Helper function to get a user-friendly error message
export const getErrorMessage = (error) => {
  if (!error) {
    logger.warn('getErrorMessage called with no error');
    return 'An unknown error occurred';
  }

  if (isApiError(error)) {
    return error.message;
  }

  if (error.response?.data?.message) {
    return error.response.data.message;
  }

  if (error.message) {
    // Clean up common axios error messages
    if (error.message.includes('Network Error')) {
      return 'Unable to connect to the server. Please check your internet connection.';
    }
    return error.message;
  }

  logger.warn('Unhandled error type in getErrorMessage', { error });
  return 'An unexpected error occurred';
};

export default api;