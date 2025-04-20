import React, { useState, useEffect, useCallback } from 'react';
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
import logger from '../utils/logger';
import EmailCard from './common/EmailCard';
import SmartReplyModal from './common/SmartReplyModal';

const ActionButton = styled(Button)(({ theme }) => ({
  margin: theme.spacing(1),
}));

const EnhancedHeader = styled(Box)(({ theme }) => ({
  display: 'flex',
  flexDirection: 'column',
  alignItems: 'center',
  background: 'linear-gradient(90deg, #3f51b5 0%, #f50057 100%)',
  color: '#fff',
  borderRadius: '16px',
  padding: theme.spacing(4, 2, 3, 2),
  marginBottom: theme.spacing(3),
  boxShadow: '0 8px 24px 0 rgba(63,81,181,0.08)',
}));

const EnhancedSummaryPaper = styled(Paper)(({ theme }) => ({
  padding: theme.spacing(4),
  margin: theme.spacing(2, 0),
  borderRadius: '16px',
  background: '#fff',
  boxShadow: '0 6px 24px 0 rgba(63,81,181,0.08)',
  border: '1.5px solid #e3e8f0',
  maxWidth: 700,
  marginLeft: 'auto',
  marginRight: 'auto',
}));

const SummaryText = styled(Typography)(({ theme }) => ({
  fontSize: '1.18rem',
  lineHeight: 1.85,
  color: theme.palette.text.primary,
  whiteSpace: 'pre-line',
  wordBreak: 'break-word',
  letterSpacing: 0.01,
  fontWeight: 400,
  padding: theme.spacing(0.5, 0),
  borderLeft: `4px solid ${theme.palette.primary.light}`,
  background: 'rgba(63,81,181,0.03)',
  borderRadius: '6px',
  paddingLeft: theme.spacing(2),
}));

const LastUpdatedBox = styled(Box)(({ theme }) => ({
  marginTop: theme.spacing(3),
  textAlign: 'center',
  padding: theme.spacing(2, 0, 0, 0),
  borderTop: `1px dashed ${theme.palette.grey[300]}`,
}));

function SummaryPage() {
  const [summaryData, setSummaryData] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [dbStatus, setDbStatus] = useState('available');
  const [selectedEmail, setSelectedEmail] = useState(null);
  const [showSmartReplyModal, setShowSmartReplyModal] = useState(false);
  const navigate = useNavigate();

  const fetchSummary = useCallback(async (forceRefresh = false) => {
    try {
      logger.info('Fetching summary data', { forceRefresh });
      setLoading(true);
      setError(null);
      const response = await summary.get(forceRefresh);
      setSummaryData(response.data);
      setDbStatus('available');
      logger.info('Summary data fetched successfully', { cached: response.data?.cached });
    } catch (err) {
      logger.error('Error fetching summary:', err);
      if (err.response?.status === 401) {
        logger.info('User not authenticated, redirecting to login');
        navigate('/login');
      } else if (err.response?.status === 503) {
        logger.warn('Database service unavailable');
        setDbStatus('unavailable');
        setError('Database service is currently unavailable. Some features may be limited.');
      } else {
        setError(getErrorMessage(err));
        if (err.response?.data?.status === 'degraded') {
          logger.warn('Database service degraded');
          setDbStatus('degraded');
        }
      }
    } finally {
      setLoading(false);
    }
  }, [navigate]);

  useEffect(() => {
    logger.info('SummaryPage mounted, fetching initial data');
    fetchSummary();
  }, [fetchSummary]);

  const handleLogout = async () => {
    try {
      logger.info('User initiated logout');
      await auth.logout();
      logger.info('Logout successful, redirecting to login');
      navigate('/login');
    } catch (err) {
      logger.error('Logout failed:', err);
      setError(getErrorMessage(err));
    }
  };

  const handleRefresh = () => {
    logger.info('Manual refresh initiated');
    fetchSummary(true);
  };

  const handleSmartReply = (email) => {
    setSelectedEmail(email);
    setShowSmartReplyModal(true);
  };

  const getErrorSeverity = (errorMessage) => {
    if (dbStatus !== 'available') return 'warning';
    if (isApiError(error) && error.status >= 500) return 'error';
    return 'error';
  };

  return (
    <Container maxWidth="md" sx={{ minHeight: '100vh', py: 4 }}>
      <EnhancedHeader>
        <Typography variant="h3" component="h1" gutterBottom sx={{ fontWeight: 700, letterSpacing: 0.5 }}>
          Your Daily Summary
        </Typography>
        <Box sx={{ display: 'flex', justifyContent: 'center', gap: 2, mb: 1 }}>
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
      </EnhancedHeader>

      {error && (
        <Alert 
          severity={getErrorSeverity(error)} 
          sx={{ mb: 2, maxWidth: 600, mx: 'auto' }}
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
        <Box sx={{ display: 'flex', justifyContent: 'center', my: 6 }}>
          <CircularProgress size={48} />
        </Box>
      ) : (
        <>
          {summaryData?.summary && (
            <EnhancedSummaryPaper elevation={3}>
              <SummaryText component="div">
                {summaryData.summary}
              </SummaryText>
            </EnhancedSummaryPaper>
          )}

          {summaryData?.emails && summaryData.emails.length > 0 && (
            <Box sx={{ mt: 4 }}>
              <Typography variant="h6" gutterBottom sx={{ mb: 3 }}>
                Latest Emails ({summaryData.emails.length})
                <Typography component="span" variant="body2" color="text.secondary" sx={{ ml: 1 }}>
                  Most recent first
                </Typography>
              </Typography>
              {summaryData.emails.map((email) => (
                <EmailCard
                  key={email.id}
                  email={email}
                  onSmartReply={handleSmartReply}
                />
              ))}
            </Box>
          )}
        </>
      )}

      {!loading && !error && summaryData?.summary && (
        <LastUpdatedBox>
          <Typography variant="body2" color="text.secondary">
            Last updated: {new Date().toLocaleTimeString()}
            {summaryData.cached && ' (from cache)'}
          </Typography>
          <Typography variant="body2" sx={{ mt: 1 }}>
            View more details in:&nbsp;
            <Link 
              href="https://calendar.google.com" 
              target="_blank" 
              rel="noopener noreferrer"
              sx={{ mx: 1, fontWeight: 500 }}
            >
              Google Calendar
            </Link>
            |
            <Link 
              href="https://mail.google.com" 
              target="_blank" 
              rel="noopener noreferrer"
              sx={{ mx: 1, fontWeight: 500 }}
            >
              Gmail
            </Link>
          </Typography>
        </LastUpdatedBox>
      )}

      <SmartReplyModal
        open={showSmartReplyModal}
        email={selectedEmail}
        onClose={() => {
          setShowSmartReplyModal(false);
          setSelectedEmail(null);
        }}
      />
    </Container>
  );
}

export default SummaryPage;
