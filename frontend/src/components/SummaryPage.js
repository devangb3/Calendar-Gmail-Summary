import React, { useState, useEffect, useCallback } from 'react';
import { useNavigate } from 'react-router-dom';
import { 
  Box, 
  Container, 
  Typography, 
  Button, 
  CircularProgress,
  Alert,
  Chip,
  Grid,
  List,
  ListItem,
  ListItemText,
  Divider,
  IconButton
} from '@mui/material';
import { styled } from '@mui/material/styles';
import RefreshIcon from '@mui/icons-material/Refresh';
import LogoutIcon from '@mui/icons-material/Logout';
import CachedIcon from '@mui/icons-material/Cached';
import EventIcon from '@mui/icons-material/Event';
import EmailIcon from '@mui/icons-material/Email';
import AssignmentIcon from '@mui/icons-material/Assignment';
import AccessTimeIcon from '@mui/icons-material/AccessTime';
import SmartToyIcon from '@mui/icons-material/SmartToy';
import { auth, summary, getErrorMessage } from '../utils/api';
import DatabaseStatus from './common/DatabaseStatus';
import DashboardCard from './common/DashboardCard';
import PriorityBadge from './common/PriorityBadge';
import SmartReplyModal from './common/SmartReplyModal';
import AudioSummary from './common/AudioSummary';
import CalendarInvites from './common/CalendarInvites';
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

const ActionButton = styled(Button)(({ theme }) => ({
  margin: theme.spacing(1),
  borderRadius: '12px',
  padding: theme.spacing(1, 3),
}));

const EventTypeChip = styled(Chip)(({ type, theme }) => {
  const colors = {
    MEETING: { bg: '#e3f2fd', color: '#1976d2' },
    DEADLINE: { bg: '#fce4ec', color: '#c2185b' },
    PERSONAL: { bg: '#e8f5e9', color: '#2e7d32' },
    OTHER: { bg: '#f5f5f5', color: '#616161' }
  };
  const style = colors[type] || colors.OTHER;
  return {
    backgroundColor: style.bg,
    color: style.color,
    fontWeight: 500,
    border: `1px solid ${style.color}20`
  };
});

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
      setLoading(true);
      setError(null);
      const response = await summary.get(forceRefresh);
      setSummaryData(JSON.parse(response.data.summary));
      setDbStatus('available');
    } catch (err) {
      logger.error('Error fetching summary:', err);
      if (err.response?.status === 401) {
        navigate('/login');
      } else if (err.response?.status === 503) {
        setDbStatus('unavailable');
        setError('Database service is currently unavailable. Some features may be limited.');
      } else {
        setError(getErrorMessage(err));
      }
    } finally {
      setLoading(false);
    }
  }, [navigate]);

  useEffect(() => {
    fetchSummary();
  }, [fetchSummary]);

  const handleLogout = async () => {
    try {
      await auth.logout();
      navigate('/login');
    } catch (err) {
      setError(getErrorMessage(err));
    }
  };

  if (loading) {
    return (
      <Box sx={{ display: 'flex', justifyContent: 'center', alignItems: 'center', minHeight: '100vh' }}>
        <CircularProgress size={48} />
      </Box>
    );
  }

  return (
    <Container maxWidth="lg" sx={{ py: 4 }}>
      <EnhancedHeader>
        <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', mb: 2 }}>
          <Typography variant="h4" component="h1" sx={{ fontWeight: 700 }}>
            Daily Summary
          </Typography>
          <Box>
            <DatabaseStatus status={dbStatus} />
            {summaryData?.cached && (
              <Chip
                icon={<CachedIcon />}
                label="Cached"
                color="info"
                variant="outlined"
                size="small"
                sx={{ ml: 1 }}
              />
            )}
          </Box>
        </Box>
        
        <QuickSummary priority={summaryData?.quickSummary?.priority_level}>
          {summaryData?.quickSummary?.overview}
        </QuickSummary>

        <Box sx={{ mt: 2, mb: 2 }}>
          <AudioSummary />
        </Box>

        <Box sx={{ display: 'flex', justifyContent: 'center', mt: 2 }}>
          <ActionButton
            variant="contained"
            color="inherit"
            startIcon={<RefreshIcon />}
            onClick={() => fetchSummary(true)}
          >
            Refresh
          </ActionButton>
          <ActionButton
            variant="outlined"
            color="inherit"
            startIcon={<LogoutIcon />}
            onClick={handleLogout}
          >
            Logout
          </ActionButton>
        </Box>
      </EnhancedHeader>

      {error && (
        <Alert 
          severity={dbStatus !== 'available' ? 'warning' : 'error'} 
          sx={{ mb: 4, maxWidth: 800, mx: 'auto' }}
        >
          {error}
        </Alert>
      )}

      <Grid container spacing={3}>
        {/* Add Calendar Invites section at the top */}
        <Grid item xs={12}>
          <DashboardCard 
            title="Pending Calendar Invites" 
            icon={<EventIcon />}
          >
            <CalendarInvites 
              onInviteAccepted={() => fetchSummary(true)} 
            />
          </DashboardCard>
        </Grid>

        <Grid item xs={12} md={6}>
          <DashboardCard 
            title="Upcoming Events" 
            icon={<EventIcon />}
          >
            <List>
              {summaryData?.events.upcoming.map((event) => (
                <React.Fragment key={`event-${event.title}-${event.time}`}>
                  <ListItem 
                    sx={{ 
                      display: 'flex', 
                      flexDirection: 'column', 
                      alignItems: 'flex-start',
                      py: 2 
                    }}
                  >
                    <Box sx={{ display: 'flex', gap: 1, mb: 1, alignItems: 'center' }}>
                      <EventTypeChip label={event.type} type={event.type} size="small" />
                      <PriorityBadge priority={event.priority} />
                    </Box>
                    <Typography variant="subtitle1" sx={{ fontWeight: 500 }}>
                      {event.title}
                    </Typography>
                    <Box sx={{ display: 'flex', alignItems: 'center', mt: 1, color: 'text.secondary' }}>
                      <AccessTimeIcon sx={{ fontSize: 18, mr: 1 }} />
                      <Typography variant="body2">
                        {event.time}
                      </Typography>
                    </Box>
                  </ListItem>
                  <Divider />
                </React.Fragment>
              ))}
              {summaryData?.events.upcoming.length === 0 && (
                <ListItem>
                  <ListItemText primary="No upcoming events" />
                </ListItem>
              )}
            </List>
          </DashboardCard>
        </Grid>

        <Grid item xs={12} md={6}>
          <DashboardCard 
            title="Important Emails" 
            icon={<EmailIcon />}
          >
            <List>
              {summaryData?.emails.important.map((email) => (
                <React.Fragment key={`email-${email.threadId}-${email.subject}`}>
                  <ListItem 
                    sx={{ 
                      display: 'flex', 
                      flexDirection: 'column', 
                      alignItems: 'flex-start',
                      py: 2 
                    }}
                  >
                    <Box sx={{ display: 'flex', gap: 1, mb: 1, alignItems: 'center', width: '100%' }}>
                      <PriorityBadge priority={email.priority} />
                      {email.actionRequired && (
                        <Chip 
                          label="Action Required" 
                          size="small"
                          color="error"
                          variant="outlined"
                        />
                      )}
                    </Box>
                    <Typography variant="subtitle1" sx={{ fontWeight: 500 }}>
                      {email.subject}
                    </Typography>
                    <Typography variant="body2" color="text.secondary">
                      From: {email.from}
                    </Typography>
                  </ListItem>
                  <Divider />
                </React.Fragment>
              ))}
              {summaryData?.emails.important.length === 0 && (
                <ListItem>
                  <ListItemText primary="No important emails" />
                </ListItem>
              )}
            </List>
          </DashboardCard>
        </Grid>

        <Grid item xs={12}>
          <DashboardCard 
            title="Action Items" 
            icon={<AssignmentIcon />}
          >
            <List>
              {summaryData?.actionItems.map((item) => (
                <React.Fragment key={`action-${item.task}-${item.priority}`}>
                  <ListItem 
                    sx={{ 
                      display: 'flex', 
                      flexDirection: 'column', 
                      alignItems: 'flex-start',
                      py: 2 
                    }}
                  >
                    <Box sx={{ display: 'flex', gap: 1, mb: 1, alignItems: 'center' }}>
                      <PriorityBadge priority={item.priority} />
                      <Chip 
                        label={item.source} 
                        size="small"
                        color="primary"
                        variant="outlined"
                      />
                    </Box>
                    <Typography variant="subtitle1">
                      {item.task}
                    </Typography>
                    {item.deadline && (
                      <Box sx={{ display: 'flex', alignItems: 'center', mt: 1, color: 'text.secondary' }}>
                        <AccessTimeIcon sx={{ fontSize: 18, mr: 1 }} />
                        <Typography variant="body2">
                          Deadline: {item.deadline}
                        </Typography>
                      </Box>
                    )}
                  </ListItem>
                  <Divider />
                </React.Fragment>
              ))}
              {summaryData?.actionItems.length === 0 && (
                <ListItem>
                  <ListItemText primary="No action items" />
                </ListItem>
              )}
            </List>
          </DashboardCard>
        </Grid>

        <Grid item xs={12}>
          <DashboardCard 
            title="Recent Emails" 
            icon={<EmailIcon />}
          >
            <List>
              {summaryData?.emails?.important?.slice(0, 5).map((email) => (
                <React.Fragment key={`recent-${email.threadId}-${email.subject}`}>
                  <ListItem 
                    sx={{ 
                      display: 'flex', 
                      flexDirection: 'column', 
                      alignItems: 'flex-start',
                      py: 2 
                    }}
                  >
                    <Box sx={{ display: 'flex', gap: 1, mb: 1, alignItems: 'center', width: '100%', justifyContent: 'space-between' }}>
                      <Box sx={{ display: 'flex', gap: 1, alignItems: 'center' }}>
                        <PriorityBadge priority={email.priority} />
                        {email.actionRequired && (
                          <Chip 
                            label="Action Required" 
                            size="small"
                            color="error"
                            variant="outlined"
                          />
                        )}
                      </Box>
                      {email.threadId && email.from_email && (
                        <IconButton
                          onClick={() => {
                            setSelectedEmail({
                              ...email,
                              from_email: email.from_email
                            });
                            setShowSmartReplyModal(true);
                          }}
                          color="primary"
                          size="small"
                          title="Generate Smart Reply"
                        >
                          <SmartToyIcon />
                        </IconButton>
                      )}
                    </Box>
                    <Typography variant="subtitle1" sx={{ fontWeight: 500 }}>
                      {email.subject}
                    </Typography>
                    <Typography variant="body2" color="text.secondary">
                      From: {email.from}
                    </Typography>
                    {email.snippet && (
                      <Typography 
                        variant="body2" 
                        color="text.secondary" 
                        sx={{ 
                          mt: 1,
                          display: '-webkit-box',
                          WebkitLineClamp: 2,
                          WebkitBoxOrient: 'vertical',
                          overflow: 'hidden',
                          textOverflow: 'ellipsis'
                        }}
                      >
                        {email.snippet}
                      </Typography>
                    )}
                  </ListItem>
                  <Divider />
                </React.Fragment>
              ))}
              {(!summaryData?.emails?.important || summaryData.emails.important.length === 0) && (
                <ListItem>
                  <ListItemText primary="No recent emails" />
                </ListItem>
              )}
            </List>
          </DashboardCard>
        </Grid>
      </Grid>

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
