import React, { useState, useEffect, useCallback } from 'react';
import { useNavigate } from 'react-router-dom';
import {
  Box,
  Container,
  Typography,
  Button,
  Grid,
  Alert,
  Chip,
  Tooltip,
} from '@mui/material';
import { styled } from '@mui/material/styles';
import RefreshIcon from '@mui/icons-material/Refresh';
import LogoutIcon from '@mui/icons-material/Logout';
import CachedIcon from '@mui/icons-material/Cached';
import EventIcon from '@mui/icons-material/Event';
import EmailIcon from '@mui/icons-material/Email';
import AssignmentIcon from '@mui/icons-material/Assignment';
import { auth, summary } from '../utils/api';
import DatabaseStatus from './common/DatabaseStatus';
import DashboardCard from './common/DashboardCard';
import AudioSummary from './common/AudioSummary';
import logger from '../utils/logger';

const EnhancedHeader = styled(Box)(({ theme }) => ({
  background: 'linear-gradient(135deg, #3f51b5 0%, #f50057 100%)',
  color: '#fff',
  borderRadius: '20px',
  padding: theme.spacing(4),
  marginBottom: theme.spacing(4),
  boxShadow: '0 8px 32px 0 rgba(63,81,181,0.1)',
}));

const QuickSummary = styled(Typography)(({ theme, priority }) => {
  const colors = {
    HIGH: theme.palette.error.light,
    MEDIUM: theme.palette.warning.light,
    LOW: theme.palette.success.light
  };
  return {
    fontSize: '1.2rem',
    fontWeight: 500,
    lineHeight: 1.6,
    textAlign: 'left',
    padding: theme.spacing(3),
    background: `linear-gradient(to right, ${colors[priority] || colors.LOW}15, transparent)`,
    borderRadius: '12px',
    borderLeft: `4px solid ${colors[priority] || colors.LOW}`,
    margin: theme.spacing(2, 0),
    whiteSpace: 'pre-line'
  };
});

function SummaryPage() {
  const [summaryData, setSummaryData] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [dbStatus, setDbStatus] = useState('available');
  const [audioUrl, setAudioUrl] = useState(null);
  const navigate = useNavigate();

  const fetchSummary = useCallback(async (forceRefresh = false) => {
    try {
      setLoading(true);
      setError(null);
      const response = await summary.get(forceRefresh);
      setSummaryData(JSON.parse(response.data.summary));
      
      // Fetch audio URL
      try {
        const audioResponse = await summary.getAudioSummary();
        const audioBlob = new Blob([audioResponse.data], { type: 'audio/mpeg' });
        const url = URL.createObjectURL(audioBlob);
        setAudioUrl(url);
      } catch (audioErr) {
        logger.error('Error fetching audio summary:', audioErr);
        // Clear any existing audio URL on error
        setAudioUrl(null);
      }
      
      setDbStatus('available');
    } catch (err) {
      logger.error('Error fetching summary:', err);
      if (err.response?.status === 401) {
        navigate('/login');
      } else if (err.response?.status === 503) {
        setDbStatus('unavailable');
        setError('Database service is currently unavailable. Some features may be limited.');
      } else {
        setError(err.message || 'An error occurred while fetching the summary.');
      }
    } finally {
      setLoading(false);
    }
  }, [navigate]);

  useEffect(() => {
    fetchSummary();
  }, [fetchSummary]);

  // Clean up audio URL on unmount
  useEffect(() => {
    return () => {
      if (audioUrl) {
        URL.revokeObjectURL(audioUrl);
      }
    };
  }, [audioUrl]);

  const handleLogout = async () => {
    try {
      await auth.logout();
      navigate('/login');
    } catch (err) {
      logger.error('Logout failed:', err);
      setError(err.message || 'Failed to logout. Please try again.');
    }
  };

  const getStatCount = (type) => {
    if (!summaryData) return 0;
    switch (type) {
      case 'events':
        return summaryData.events?.length || 0;
      case 'emails':
        return summaryData.emails?.important?.length || 0;
      case 'tasks':
        // Ensure actionItems is an array before checking length
        return Array.isArray(summaryData.actionItems) ? summaryData.actionItems.length : 0;
      default:
        return 0;
    }
  };

  if (loading) {
    return null; // Loading state is handled by the parent layout
  }

  return (
    <Container maxWidth="lg">
      <EnhancedHeader>
        <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', mb: 2 }}>
          <Typography variant="h4" component="h1" sx={{ fontWeight: 700 }}>
            Daily Overview
          </Typography>
          <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
            <DatabaseStatus status={dbStatus} />
            {summaryData?.cached && (
              <Tooltip title="Showing cached data">
                <Chip
                  icon={<CachedIcon />}
                  label="Cached"
                  size="small"
                  sx={{
                    bgcolor: 'rgba(255, 255, 255, 0.2)',
                    color: 'white',
                    '& .MuiChip-icon': {
                      color: 'white',
                    },
                  }}
                />
              </Tooltip>
            )}
            <Button
              variant="contained"
              color="inherit"
              size="small"
              startIcon={<RefreshIcon />}
              onClick={() => fetchSummary(true)}
              sx={{
                bgcolor: 'rgba(255, 255, 255, 0.2)',
                color: 'white',
                '&:hover': {
                  bgcolor: 'rgba(255, 255, 255, 0.3)',
                },
              }}
            >
              Refresh
            </Button>
            <Button
              variant="outlined"
              color="inherit"
              size="small"
              startIcon={<LogoutIcon />}
              onClick={handleLogout}
              sx={{
                borderColor: 'rgba(255, 255, 255, 0.5)',
                color: 'white',
                '&:hover': {
                  borderColor: 'white',
                  bgcolor: 'rgba(255, 255, 255, 0.1)',
                },
              }}
            >
              Logout
            </Button>
          </Box>
        </Box>

        {summaryData?.quickSummary && (
          <QuickSummary priority={summaryData.quickSummary.priority_level}>
            {summaryData.quickSummary.overview}
          </QuickSummary>
        )}
      </EnhancedHeader>

      {error && (
        <Alert severity={dbStatus !== 'available' ? 'warning' : 'error'} sx={{ mb: 4 }}>
          {error}
        </Alert>
      )}

      <Box sx={{ mb: 4 }}>
        <AudioSummary
          audioUrl={audioUrl}
          title="Listen to your daily summary"
        />
      </Box>

      <Grid container spacing={3}>
        <Grid item xs={12} md={4}>
          <DashboardCard
            title="Calendar Events"
            subtitle="Upcoming meetings and events"
            action={
              <Button
                size="small"
                endIcon={<EventIcon />}
                onClick={() => navigate('/calendar')}
              >
                View All
              </Button>
            }
          >
            <Box sx={{ textAlign: 'center', py: 3 }}>
              <Typography variant="h3" color="primary" gutterBottom>
                {getStatCount('events')}
              </Typography>
              <Typography variant="body2" color="text.secondary">
                Events Today
              </Typography>
            </Box>
          </DashboardCard>
        </Grid>

        <Grid item xs={12} md={4}>
          <DashboardCard
            title="Important Emails"
            subtitle="Emails requiring attention"
            action={
              <Button
                size="small"
                endIcon={<EmailIcon />}
                onClick={() => navigate('/emails')}
              >
                View All
              </Button>
            }
          >
            <Box sx={{ textAlign: 'center', py: 3 }}>
              <Typography variant="h3" color="primary" gutterBottom>
                {getStatCount('emails')}
              </Typography>
              <Typography variant="body2" color="text.secondary">
                Important Messages
              </Typography>
            </Box>
          </DashboardCard>
        </Grid>

        <Grid item xs={12} md={4}>
          <DashboardCard
            title="Action Items"
            subtitle="Tasks requiring your attention"
            action={
              <Button
                size="small"
                endIcon={<AssignmentIcon />}
                onClick={() => navigate('/tasks')}
              >
                View All
              </Button>
            }
          >
            <Box sx={{ textAlign: 'center', py: 3 }}>
              <Typography variant="h3" color="primary" gutterBottom>
                {getStatCount('tasks')}
              </Typography>
              <Typography variant="body2" color="text.secondary">
                Pending Tasks
              </Typography>
            </Box>
          </DashboardCard>
        </Grid>
      </Grid>
    </Container>
  );
}

export default SummaryPage;
