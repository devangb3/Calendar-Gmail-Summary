import React, { useState, useEffect } from 'react';
import PropTypes from 'prop-types';
import {
  Box,
  Typography,
  Button,
  CircularProgress,
  Alert,
  List,
  ListItem,
  Divider,
  Chip,
  Tooltip,
  ButtonGroup
} from '@mui/material';
import { styled } from '@mui/material/styles';
import CheckIcon from '@mui/icons-material/Check';
import CloseIcon from '@mui/icons-material/Close';
import EventIcon from '@mui/icons-material/Event';
import HelpOutlineIcon from '@mui/icons-material/HelpOutline';
import AccessTimeIcon from '@mui/icons-material/AccessTime';
import { calendar } from '../../utils/api';
import logger from '../../utils/logger';

const InviteItem = styled(ListItem)(({ theme }) => ({
  display: 'flex',
  flexDirection: 'column',
  alignItems: 'flex-start',
  padding: theme.spacing(2),
  '&:hover': {
    backgroundColor: theme.palette.action.hover,
  }
}));

const StatusChip = styled(Chip)(({ responseStatus, theme }) => {
  const colors = {
    needsAction: {
      bg: theme.palette.warning.light,
      color: theme.palette.warning.dark,
      border: theme.palette.warning.main
    },
    tentative: {
      bg: theme.palette.info.light,
      color: theme.palette.info.dark,
      border: theme.palette.info.main
    }
  };
  const style = colors[responseStatus] || colors.needsAction;
  return {
    backgroundColor: style.bg,
    color: style.color,
    border: `1px solid ${style.border}`,
    '& .MuiChip-icon': {
      color: 'inherit'
    }
  };
});

const CalendarInvites = ({ onInviteAccepted }) => {
  const [pendingInvites, setPendingInvites] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [processing, setProcessing] = useState({});

  useEffect(() => {
    fetchPendingInvites();
  }, []);

  const fetchPendingInvites = async () => {
    try {
      setLoading(true);
      setError(null);
      const response = await calendar.getPendingInvites();
      setPendingInvites(response.data.pending_invites || []);
    } catch (err) {
      logger.error('Failed to fetch pending invites:', err);
      setError('Failed to load pending calendar invites');
    } finally {
      setLoading(false);
    }
  };

  const formatDateTime = (dateTimeStr) => {
    try {
      const date = new Date(dateTimeStr);
      return new Intl.DateTimeFormat('en-US', {
        dateStyle: 'medium',
        timeStyle: 'short'
      }).format(date);
    } catch {
      logger.warn(`Invalid date format received: ${dateTimeStr}`);
      return 'Time not specified';
    }
  };

  const getResponseLabel = (status) => {
    switch (status) {
      case 'needsAction':
        return 'Response Needed';
      case 'tentative':
        return 'Tentative';
      default:
        return 'Pending Response';
    }
  };

  const handleAcceptInvite = async (eventId) => {
    try {
      setProcessing(prev => ({ ...prev, [eventId]: true }));
      setError(null);
      
      await calendar.acceptInvite(eventId);
      
      // Remove the accepted invite from the list
      setPendingInvites(current => 
        current.filter(invite => invite.id !== eventId)
      );
      
      // Notify parent component
      if (onInviteAccepted) {
        onInviteAccepted();
      }
      
    } catch (err) {
      logger.error('Failed to accept invite:', err);
      setError('Failed to accept calendar invite');
    } finally {
      setProcessing(prev => ({ ...prev, [eventId]: false }));
    }
  };

  const handleDeclineInvite = async (eventId) => {
    try {
      setProcessing(prev => ({ ...prev, [eventId]: true }));
      setError(null);
      await calendar.declineInvite(eventId);
      
      // Remove the declined invite from the list
      setPendingInvites(current => 
        current.filter(invite => invite.id !== eventId)
      );
      
      // Notify parent component
      if (onInviteAccepted) {
        onInviteAccepted();
      }
      
    } catch (err) {
      logger.error('Failed to decline invite:', err);
      setError('Failed to decline calendar invite');
    } finally {
      setProcessing(prev => ({ ...prev, [eventId]: false }));
    }
  };

  if (loading) {
    return (
      <Box sx={{ display: 'flex', justifyContent: 'center', p: 2 }}>
        <CircularProgress size={24} />
      </Box>
    );
  }

  if (error) {
    return (
      <Alert 
        severity="error" 
        onClose={() => setError(null)}
        action={
          <Button color="inherit" size="small" onClick={fetchPendingInvites}>
            Retry
          </Button>
        }
      >
        {error}
      </Alert>
    );
  }

  if (pendingInvites.length === 0) {
    return (
      <Box sx={{ 
        p: 2, 
        display: 'flex', 
        alignItems: 'center', 
        justifyContent: 'center',
        color: 'text.secondary'
      }}>
        <Typography variant="body2">
          No pending calendar invites
        </Typography>
      </Box>
    );
  }

  return (
    <List>
      {pendingInvites.map((invite, index) => (
        <React.Fragment key={invite.id || index}>
          <InviteItem>
            <Box sx={{ 
              display: 'flex', 
              gap: 1, 
              alignItems: 'center', 
              width: '100%',
              mb: 1,
              justifyContent: 'space-between'
            }}>
              <Box sx={{ display: 'flex', gap: 1, alignItems: 'center' }}>
                <EventIcon color="primary" />
                <Typography variant="subtitle1" sx={{ fontWeight: 500 }}>
                  {invite.summary}
                </Typography>
              </Box>
              <StatusChip
                icon={<HelpOutlineIcon />}
                label={getResponseLabel(invite.responseStatus)}
                responseStatus={invite.responseStatus}
                size="small"
              />
            </Box>
            
            <Box sx={{ display: 'flex', alignItems: 'center', mb: 1, color: 'text.secondary' }}>
              <AccessTimeIcon sx={{ fontSize: 18, mr: 1 }} />
              <Typography variant="body2">
                {formatDateTime(invite.start)} - {formatDateTime(invite.end)}
              </Typography>
            </Box>
            
            {invite.location && (
              <Typography variant="body2" color="text.secondary" sx={{ mb: 1 }}>
                Location: {invite.location}
              </Typography>
            )}
            
            {invite.attendees?.length > 0 && (
              <Box sx={{ display: 'flex', flexWrap: 'wrap', gap: 1, mb: 1 }}>
                {invite.attendees.map((attendee, idx) => (
                  <Tooltip 
                    key={attendee.email || idx}
                    title={attendee.email || ''}
                  >
                    <Chip 
                      label={attendee.name || attendee.email}
                      size="small"
                      variant="outlined"
                    />
                  </Tooltip>
                ))}
              </Box>
            )}
            
            <ButtonGroup variant="contained" sx={{ mt: 1 }}>
              <Button
                color="primary"
                startIcon={processing[invite.id] ? 
                  <CircularProgress size={16} /> : 
                  <CheckIcon />
                }
                onClick={() => handleAcceptInvite(invite.id)}
                disabled={processing[invite.id]}
              >
                {processing[invite.id] ? 'Accepting...' : 'Accept'}
              </Button>
              <Button
                color="error"
                startIcon={processing[invite.id] ? 
                  <CircularProgress size={16} /> : 
                  <CloseIcon />
                }
                onClick={() => handleDeclineInvite(invite.id)}
                disabled={processing[invite.id]}
              >
                {processing[invite.id] ? 'Declining...' : 'Decline'}
              </Button>
            </ButtonGroup>
          </InviteItem>
          {index < pendingInvites.length - 1 && <Divider />}
        </React.Fragment>
      ))}
    </List>
  );
};

CalendarInvites.propTypes = {
  onInviteAccepted: PropTypes.func
};

CalendarInvites.defaultProps = {
  onInviteAccepted: () => {}
};

export default CalendarInvites;