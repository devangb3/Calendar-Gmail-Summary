import { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { auth } from '../utils/api';
import logger from '../utils/logger';

export function useAuth() {
  const [isAuthenticated, setIsAuthenticated] = useState(false);
  const [isLoading, setIsLoading] = useState(true);
  const [authError, setAuthError] = useState(null);
  const navigate = useNavigate();

  useEffect(() => {
    checkAuthStatus();
  }, []);

  const checkAuthStatus = async () => {
    try {
      const response = await auth.check();
      const authenticated = response.data?.authenticated === true;
      setIsAuthenticated(authenticated);
      if (!authenticated && window.location.pathname !== '/login') {
        navigate('/login');
      }
    } catch (error) {
      logger.error('Auth check failed:', error);
      setIsAuthenticated(false);
      setAuthError(error.message);
      if (window.location.pathname !== '/login') {
        navigate('/login');
      }
    } finally {
      setIsLoading(false);
    }
  };

  const login = async () => {
    try {
      setAuthError(null);
      const response = await auth.login();
      if (response.data?.authorization_url) {
        // Store required scopes info in session storage for verification
        if (response.data.scope_info) {
          sessionStorage.setItem('scope_info', JSON.stringify(response.data.scope_info));
        }
        window.location.href = response.data.authorization_url;
      }
    } catch (error) {
      logger.error('Login failed:', error);
      setAuthError(error.response?.data?.message || error.message);
      throw error;
    }
  };

  const logout = async () => {
    try {
      await auth.logout();
      setIsAuthenticated(false);
      sessionStorage.removeItem('scope_info'); // Clear stored scope info
      navigate('/login');
    } catch (error) {
      logger.error('Logout failed:', error);
      throw error;
    }
  };

  return {
    isAuthenticated,
    isLoading,
    authError,
    login,
    logout,
    checkAuthStatus
  };
}

export default useAuth;