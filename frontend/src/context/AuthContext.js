import React, { createContext, useState, useEffect, useContext, useCallback } from 'react';
import { auth } from '../utils/api';
import logger from '../utils/logger';

export const AuthContext = createContext(null);

export function AuthProvider({ children }) {
  const [isAuthenticated, setIsAuthenticated] = useState(false);
  const [loading, setLoading] = useState(true);

  const checkAuthStatus = useCallback(async () => {
    try {
      logger.info('Checking authentication status');
      const response = await auth.check();
      const authenticated = response.data?.authenticated === true;
      setIsAuthenticated(authenticated);
      logger.info('Auth status check complete', { authenticated });
      
      // If authenticated and there's a stored redirect path, navigate to it
      if (authenticated) {
        const redirectPath = sessionStorage.getItem('redirectAfterLogin');
        if (redirectPath) {
          sessionStorage.removeItem('redirectAfterLogin');
          window.location.href = redirectPath;
        }
      }
      
      return authenticated;
    } catch (error) {
      if (error.response?.status === 401) {
        logger.info('Auth check returned 401, user not authenticated');
      } else {
        logger.error('Auth status check failed:', error);
      }
      setIsAuthenticated(false);
      return false;
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    checkAuthStatus();
  }, [checkAuthStatus]);

  const value = {
    isAuthenticated,
    setIsAuthenticated,
    loading,
    checkAuthStatus
  };

  return (
    <AuthContext.Provider value={value}>
      {children}
    </AuthContext.Provider>
  );
}

export function useAuthContext() {
  const context = useContext(AuthContext);
  if (!context) {
    throw new Error('useAuthContext must be used within an AuthProvider');
  }
  return context;
}