import React, { useState, useEffect } from 'react';
import { useNavigate, useLocation } from 'react-router-dom';
import { Box, Button, Container, Typography, Paper, Alert } from '@mui/material';
import GoogleIcon from '@mui/icons-material/Google';
import { styled } from '@mui/material/styles';
import { auth, getErrorMessage } from '../utils/api';
import DatabaseStatus from './common/DatabaseStatus';
import { useAuthContext } from '../context/AuthContext';
import logger from '../utils/logger';

const EnhancedLoginHeader = styled(Box)(({ theme }) => ({
  width: '100%',
  background: 'linear-gradient(90deg, #3f51b5 0%, #f50057 100%)',
  color: '#fff',
  borderRadius: '18px',
  padding: theme.spacing(4, 2, 3, 2),
  marginBottom: theme.spacing(3),
  boxShadow: '0 8px 24px 0 rgba(63,81,181,0.10)',
  display: 'flex',
  flexDirection: 'column',
  alignItems: 'center',
}));

const EnhancedPaper = styled(Paper)(({ theme }) => ({
  padding: theme.spacing(4, 3),
  display: 'flex',
  flexDirection: 'column',
  alignItems: 'center',
  gap: theme.spacing(3),
  borderRadius: '16px',
  boxShadow: '0 8px 24px rgba(63,81,181,0.10)',
  background: 'rgba(255,255,255,0.96)',
  backdropFilter: 'blur(10px)',
  maxWidth: 420,
  margin: 'auto',
}));

const EnhancedLoginButton = styled(Button)(({ theme }) => ({
  padding: '14px 32px',
  borderRadius: '30px',
  textTransform: 'none',
  fontSize: '1.08rem',
  fontWeight: 600,
  boxShadow: '0 4px 12px rgba(63,81,181,0.10)',
  letterSpacing: 0.2,
  background: 'linear-gradient(90deg, #3f51b5 0%, #f50057 100%)',
  color: '#fff',
  '&:hover': {
    background: 'linear-gradient(90deg, #3949ab 0%, #c51162 100%)',
    boxShadow: '0 6px 16px rgba(63,81,181,0.15)',
  },
}));

function LoginPage() {
  const [error, setError] = useState(null);
  const [loading, setLoading] = useState(false);
  const [dbStatus, setDbStatus] = useState('available');
  const { isAuthenticated } = useAuthContext();
  const navigate = useNavigate();
  const location = useLocation();

  useEffect(() => {
    // If already authenticated, redirect to home or the page they were trying to access
    if (isAuthenticated) {
      const from = location.state?.from?.pathname || '/';
      navigate(from, { replace: true });
    }
  }, [isAuthenticated, navigate, location]);

  const handleLogin = async () => {
    try {
      logger.info('User initiating login');
      setLoading(true);
      setError(null);
      const response = await auth.login();
      if (response.data?.authorization_url) {
        logger.info('Login authorization URL received');
        window.location.href = response.data.authorization_url;
      } else {
        setError('Invalid response from server');
      }
    } catch (err) {
      logger.error('Login failed:', err);
      if (err.response?.status === 503) {
        setDbStatus('unavailable');
        setError('Database service is unavailable. Please try again later.');
      } else {
        setError(getErrorMessage(err));
      }
    } finally {
      setLoading(false);
    }
  };

  return (
    <Container
      maxWidth={false}
      disableGutters
      sx={{
        minHeight: '100vh',
        width: '100vw',
        p: 0,
        m: 0,
        overflow: 'hidden',
      }}
    >
      <Box
        sx={{
          minHeight: '100vh',
          width: '100vw',
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'center',
          background: 'linear-gradient(135deg, #3f51b5 0%, #f50057 100%)',
          padding: 0,
          margin: 0,
        }}
      >
        <EnhancedPaper elevation={3}>
          <EnhancedLoginHeader>
            <Typography variant="h3" component="h1" gutterBottom sx={{ fontWeight: 800, letterSpacing: 0.5 }}>
              Welcome to Calendar Summary
            </Typography>
            <Box sx={{ display: 'flex', justifyContent: 'center', width: '100%', mb: 1 }}>
              <DatabaseStatus status={dbStatus} />
            </Box>
          </EnhancedLoginHeader>
          <Typography variant="body1" color="text.secondary" align="center" sx={{ mb: 2, fontSize: '1.08rem' }}>
            Get a <b>smart summary</b> of your calendar events and emails in one place.<br />
            Sign in with Google to get started.
          </Typography>
          {error && (
            <Alert 
              severity={dbStatus !== 'available' ? 'warning' : 'error'} 
              sx={{ width: '100%', mb: 2, fontSize: '1rem' }}
            >
              {error}
            </Alert>
          )}
          <EnhancedLoginButton
            variant="contained"
            onClick={handleLogin}
            disabled={loading || dbStatus === 'unavailable'}
            startIcon={<GoogleIcon />}
          >
            {loading ? 'Connecting...' : 'Sign in with Google'}
          </EnhancedLoginButton>
        </EnhancedPaper>
      </Box>
    </Container>
  );
}

export default LoginPage;
