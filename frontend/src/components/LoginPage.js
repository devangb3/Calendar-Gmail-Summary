import React, { useState } from 'react';
import { Box, Button, Container, Typography, Paper, Alert } from '@mui/material';
import GoogleIcon from '@mui/icons-material/Google';
import { styled } from '@mui/material/styles';
import { auth, getErrorMessage } from '../utils/api';
import DatabaseStatus from './common/DatabaseStatus';

const StyledPaper = styled(Paper)(({ theme }) => ({
  padding: '2rem',
  display: 'flex',
  flexDirection: 'column',
  alignItems: 'center',
  gap: '1.5rem',
  borderRadius: '12px',
  boxShadow: '0 8px 16px rgba(0,0,0,0.1)',
  background: 'rgba(255, 255, 255, 0.9)',
  backdropFilter: 'blur(10px)',
}));

const LoginButton = styled(Button)(({ theme }) => ({
  padding: '12px 24px',
  borderRadius: '30px',
  textTransform: 'none',
  fontSize: '1rem',
  boxShadow: '0 4px 6px rgba(0,0,0,0.1)',
  '&:hover': {
    boxShadow: '0 6px 8px rgba(0,0,0,0.15)',
  },
}));

function LoginPage() {
  const [error, setError] = useState(null);
  const [loading, setLoading] = useState(false);
  const [dbStatus, setDbStatus] = useState('available');

  const handleLogin = async () => {
    try {
      setLoading(true);
      setError(null);
      const response = await auth.login();
      if (response.data?.authorization_url) {
        window.location.href = response.data.authorization_url;
      } else {
        setError('Invalid response from server');
      }
    } catch (err) {
      console.error('Login error:', err);
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
    <Container maxWidth="sm">
      <Box
        sx={{
          minHeight: '100vh',
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'center',
          background: 'linear-gradient(135deg, #3f51b5 0%, #f50057 100%)',
          padding: '2rem',
        }}
      >
        <StyledPaper elevation={3}>
          <Typography variant="h4" component="h1" gutterBottom sx={{ fontWeight: 600, color: '#2c3e50' }}>
            Welcome to Calendar Summary
          </Typography>
          
          <Box sx={{ display: 'flex', justifyContent: 'center', width: '100%', mb: 2 }}>
            <DatabaseStatus status={dbStatus} />
          </Box>
          
          <Typography variant="body1" color="text.secondary" align="center" sx={{ mb: 3 }}>
            Get a smart summary of your calendar events and emails in one place
          </Typography>
          
          {error && (
            <Alert 
              severity={dbStatus !== 'available' ? 'warning' : 'error'} 
              sx={{ width: '100%', mb: 2 }}
            >
              {error}
            </Alert>
          )}
          
          <LoginButton
            variant="contained"
            color="primary"
            onClick={handleLogin}
            disabled={loading || dbStatus === 'unavailable'}
            startIcon={<GoogleIcon />}
          >
            {loading ? 'Connecting...' : 'Sign in with Google'}
          </LoginButton>
        </StyledPaper>
      </Box>
    </Container>
  );
}

export default LoginPage;
