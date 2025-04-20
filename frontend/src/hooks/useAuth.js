import { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { auth } from '../utils/api';

export function useAuth() {
  const [isAuthenticated, setIsAuthenticated] = useState(false);
  const [isLoading, setIsLoading] = useState(true);
  const navigate = useNavigate();

  useEffect(() => {
    // Check authentication status when component mounts
    checkAuthStatus();
  }, []);

  const checkAuthStatus = async () => {
    try {
      // Try to get summary - this will fail with 401 if not authenticated
      await auth.checkSession();
      setIsAuthenticated(true);
    } catch (error) {
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
      console.error('Login failed:', error);
      throw error;
    }
  };

  const logout = async () => {
    try {
      await auth.logout();
      setIsAuthenticated(false);
      navigate('/login');
    } catch (error) {
      console.error('Logout failed:', error);
      throw error;
    }
  };

  return {
    isAuthenticated,
    isLoading,
    login,
    logout,
  };
}

export default useAuth;