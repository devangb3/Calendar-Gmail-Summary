import { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { auth } from '../utils/api';
import logger from '../utils/logger';

export function useAuth() {
  const [isAuthenticated, setIsAuthenticated] = useState(false);
  const [isLoading, setIsLoading] = useState(true);
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
      if (window.location.pathname !== '/login') {
        navigate('/login');
      }
    } finally {
      setIsLoading(false);
    }
  };

  const login = async () => {
    try {
      const response = await auth.login();
      if (response.data?.authorization_url) {
        window.location.href = response.data.authorization_url;
      }
    } catch (error) {
      logger.error('Login failed:', error);
      throw error;
    }
  };

  const logout = async () => {
    try {
      await auth.logout();
      setIsAuthenticated(false);
      navigate('/login');
    } catch (error) {
      logger.error('Logout failed:', error);
      throw error;
    }
  };

  return {
    isAuthenticated,
    isLoading,
    login,
    logout,
    checkAuthStatus
  };
}

export default useAuth;