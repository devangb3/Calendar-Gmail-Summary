import React, { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { 
  Box, 
  Container, 
  Paper, 
  Typography, 
  Button, 
  CircularProgress,
  Alert,
  Link,
  Chip
} from '@mui/material';
import { styled } from '@mui/material/styles';
import RefreshIcon from '@mui/icons-material/Refresh';
import LogoutIcon from '@mui/icons-material/Logout';
import CachedIcon from '@mui/icons-material/Cached';
import { auth, summary, isApiError, getErrorMessage } from '../utils/api';
import DatabaseStatus from './common/DatabaseStatus';

const StyledPaper = styled(Paper)(({ theme }) => ({
  padding: theme.spacing(3),
  margin: theme.spacing(2),
  borderRadius: '12px',
  boxShadow: '0 4px 6px rgba(0,0,0,0.1)',
}));

const ActionButton = styled(Button)(({ theme }) => ({
  margin: theme.spacing(1),
}));

const StatusChip = styled(Chip)(({ theme }) => ({
  margin: theme.spacing(1),
}));

function SummaryPage() {
  const [summaryData, setSummaryData] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [dbStatus, setDbStatus] = useState('available');
  const navigate = useNavigate();

  const fetchSummary = async () => {
    try {
      setLoading(true);
      setError(null);
      const response = await summary.get();
      setSummaryData(response.data);
      setDbStatus('available');
    } catch (err) {
      console.error("Error fetching summary:", err);
      if (err.response?.status === 401) {
        navigate('/login');
      } else if (err.response?.status === 503) {
        setDbStatus('unavailable');
        setError('Database service is currently unavailable. Some features may be limited.');
      } else {
        setError(getErrorMessage(err));
        if (err.response?.data?.status === 'degraded') {
          setDbStatus('degraded');
        }
      }
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchSummary();
  }, [navigate]);

  const handleLogout = async () => {
    try {
      await auth.logout();
      navigate('/login');
    } catch (err) {
      setError(getErrorMessage(err));
    }
  };

  const handleRefresh = () => {
    fetchSummary();
  };

  const getErrorSeverity = (errorMessage) => {
    if (dbStatus !== 'available') return 'warning';
    if (isApiError(error) && error.status >= 500) return 'error';
    return 'error';
  };

  return (
    <Container maxWidth="md">
      <Box sx={{ py: 4 }}>
        <Typography variant="h4" component="h1" gutterBottom align="center">
          Your Daily Summary
        </Typography>
        
        <Box sx={{ display: 'flex', justifyContent: 'center', gap: 2, mb: 2 }}>
          <DatabaseStatus status={dbStatus} />
          {summaryData?.cached && (
            <Chip
              icon={<CachedIcon />}
              label="Cached Summary"
              color="info"
              variant="outlined"
              size="small"
            />
          )}
        </Box>

        {error && (
          <Alert 
            severity={getErrorSeverity(error)} 
            sx={{ mb: 2 }}
            action={
              dbStatus !== 'available' && (
                <Button color="inherit" size="small" onClick={handleRefresh}>
                  Try Again
                </Button>
              )
            }
          >
            {error}
          </Alert>
        )}

        <Box sx={{ display: 'flex', justifyContent: 'center', gap: 2, mb: 3 }}>
          <ActionButton
            variant="contained"
            color="primary"
            startIcon={<RefreshIcon />}
            onClick={handleRefresh}
            disabled={loading}
          >
            Refresh Summary
          </ActionButton>
          <ActionButton
            variant="outlined"
            color="secondary"
            startIcon={<LogoutIcon />}
            onClick={handleLogout}
          >
            Logout
          </ActionButton>
        </Box>

        {loading ? (
          <Box sx={{ display: 'flex', justifyContent: 'center', my: 4 }}>
            <CircularProgress />
          </Box>
        ) : summaryData?.summary ? (
          <StyledPaper elevation={3}>
            <Typography variant="body1" component="div" sx={{ 
              whiteSpace: 'pre-wrap', 
              wordBreak: 'break-word',
              lineHeight: 1.6 
            }}>
              {summaryData.summary}
            </Typography>
          </StyledPaper>
        ) : !error && (
          <Alert severity="info">
            No summary available. Try refreshing to generate a new summary.
          </Alert>
        )}

        {!loading && !error && summaryData?.summary && (
          <Box sx={{ mt: 3, textAlign: 'center' }}>
            <Typography variant="body2" color="text.secondary">
              Last updated: {new Date().toLocaleTimeString()}
              {summaryData.cached && ' (from cache)'}
            </Typography>
            <Typography variant="body2" sx={{ mt: 1 }}>
              View more details in:
              {" "}
              <Link 
                href="https://calendar.google.com" 
                target="_blank" 
                rel="noopener noreferrer"
                sx={{ mx: 1 }}
              >
                Google Calendar
              </Link>
              |
              <Link 
                href="https://mail.google.com" 
                target="_blank" 
                rel="noopener noreferrer"
                sx={{ mx: 1 }}
              >
                Gmail
              </Link>
            </Typography>
          </Box>
        )}
      </Box>
    </Container>
  );
}

export default SummaryPage;
