import React, { useState } from 'react';
import PropTypes from 'prop-types';
import {
  List,
  ListItem,
  Typography,
  Box,
  Button,
  Divider,
  Chip,
  CircularProgress,
} from '@mui/material';
import CheckCircleIcon from '@mui/icons-material/CheckCircle';
import CancelIcon from '@mui/icons-material/Cancel';
import AccessTimeIcon from '@mui/icons-material/AccessTime';
import VideocamIcon from '@mui/icons-material/Videocam';
import GroupIcon from '@mui/icons-material/Group';
import RoomIcon from '@mui/icons-material/Room';
import { calendar } from '../../utils/api';
import logger from '../../utils/logger';

function CalendarInvites({ invites = [], onInviteResponded }) {
  const [respondingTo, setRespondingTo] = useState(null);

  const handleResponse = async (inviteId, accept) => {
    try {
      setRespondingTo(inviteId);
      if (accept) {
        await calendar.acceptInvite(inviteId);
      } else {
        await calendar.declineInvite(inviteId);
      }
      if (onInviteResponded) {
        onInviteResponded(inviteId, accept);
      }
    } catch (err) {
      logger.error('Error responding to invite:', err);
    } finally {
      setRespondingTo(null);
    }
  };

  const parseDateSafely = (dateObj) => {
    if (!dateObj) return null;
    try {
      // Handle both string dates and Google Calendar date objects
      const dateString = dateObj.dateTime || dateObj.date || dateObj;
      const date = new Date(dateString);
      if (isNaN(date.getTime())) {
        return null;
      }
      return date;
    } catch (e) {
      logger.error('Error parsing date:', dateObj, e);
      return null;
    }
  };

  const formatTime = (dateString) => {
    const date = parseDateSafely(dateString);
    if (!date) return 'Time not available';
    
    return new Intl.DateTimeFormat('en-US', {
      hour: 'numeric',
      minute: '2-digit',
      hour12: true,
    }).format(date);
  };

  const formatDate = (dateString) => {
    const date = parseDateSafely(dateString);
    if (!date) return 'Date not available';

    const today = new Date();
    const tomorrow = new Date(today);
    tomorrow.setDate(tomorrow.getDate() + 1);

    if (date.toDateString() === today.toDateString()) {
      return 'Today';
    } else if (date.toDateString() === tomorrow.toDateString()) {
      return 'Tomorrow';
    } else {
      return new Intl.DateTimeFormat('en-US', {
        weekday: 'long',
        month: 'short',
        day: 'numeric',
      }).format(date);
    }
  };

  // Group events by date, handling invalid dates
  const groupedInvites = invites.reduce((acc, invite) => {
    if (!invite.start) {
      // Handle invites without start time
      if (!acc['Unscheduled']) {
        acc['Unscheduled'] = [];
      }
      acc['Unscheduled'].push(invite);
      return acc;
    }

    const date = formatDate(invite.start.dateTime || invite.start.date);
    if (!acc[date]) {
      acc[date] = [];
    }
    acc[date].push(invite);
    return acc;
  }, {});

  if (invites.length === 0) {
    return (
      <Box sx={{ textAlign: 'center', py: 4 }}>
        <Typography color="text.secondary">
          No pending calendar invites
        </Typography>
      </Box>
    );
  }

  return (
    <List sx={{ width: '100%', bgcolor: 'transparent' }}>
      {Object.entries(groupedInvites).map(([date, dateInvites], index) => (
        <React.Fragment key={date}>
          {index > 0 && <Divider sx={{ my: 2 }} />}
          <Typography
            variant="subtitle1"
            sx={{
              fontWeight: 600,
              mb: 2,
              color: (theme) => theme.palette.text.primary,
            }}
          >
            {date}
          </Typography>
          {dateInvites.map((invite) => (
            <ListItem
              key={invite.id}
              alignItems="flex-start"
              sx={{
                mb: 2,
                bgcolor: 'rgba(255, 255, 255, 0.6)',
                borderRadius: 2,
                '&:hover': {
                  bgcolor: 'rgba(255, 255, 255, 0.8)',
                },
              }}
            >
              <Box sx={{ display: 'flex', flexDirection: 'column', width: '100%' }}>
                <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', mb: 1 }}>
                  <Typography variant="subtitle1" component="div" sx={{ fontWeight: 500 }}>
                    {invite.summary || 'Untitled Event'}
                  </Typography>
                  <Box sx={{ display: 'flex', gap: 1 }}>
                    <Button
                      variant="outlined"
                      color="primary"
                      size="small"
                      startIcon={respondingTo === invite.id ? <CircularProgress size={16} /> : <CheckCircleIcon />}
                      onClick={() => handleResponse(invite.id, true)}
                      disabled={respondingTo !== null}
                      sx={{ borderRadius: 2 }}
                    >
                      Accept
                    </Button>
                    <Button
                      variant="outlined"
                      color="error"
                      size="small"
                      startIcon={respondingTo === invite.id ? <CircularProgress size={16} /> : <CancelIcon />}
                      onClick={() => handleResponse(invite.id, false)}
                      disabled={respondingTo !== null}
                      sx={{ borderRadius: 2 }}
                    >
                      Decline
                    </Button>
                  </Box>
                </Box>

                <Box sx={{ display: 'flex', alignItems: 'center', gap: 2, mb: 1 }}>
                  <Box sx={{ display: 'flex', alignItems: 'center', gap: 0.5 }}>
                    <AccessTimeIcon fontSize="small" color="action" />
                    <Typography variant="body2" color="text.secondary">
                      {formatTime(invite.start?.dateTime || invite.start?.date)} - 
                      {formatTime(invite.end?.dateTime || invite.end?.date)}
                    </Typography>
                  </Box>
                  {invite.location && (
                    <Box sx={{ display: 'flex', alignItems: 'center', gap: 0.5 }}>
                      <RoomIcon fontSize="small" color="action" />
                      <Typography variant="body2" color="text.secondary">
                        {invite.location}
                      </Typography>
                    </Box>
                  )}
                </Box>

                <Box sx={{ display: 'flex', gap: 1, alignItems: 'center', flexWrap: 'wrap' }}>
                  {invite.hangoutLink && (
                    <Chip
                      icon={<VideocamIcon />}
                      label="Online Meeting"
                      size="small"
                      sx={{ bgcolor: 'rgba(63, 81, 181, 0.08)' }}
                    />
                  )}
                  {invite.attendees?.length > 0 && (
                    <Chip
                      icon={<GroupIcon />}
                      label={`${invite.attendees.length} attendee${invite.attendees.length === 1 ? '' : 's'}`}
                      size="small"
                      sx={{ bgcolor: 'rgba(63, 81, 181, 0.08)' }}
                    />
                  )}
                </Box>
              </Box>
            </ListItem>
          ))}
        </React.Fragment>
      ))}
    </List>
  );
}

CalendarInvites.propTypes = {
  invites: PropTypes.arrayOf(PropTypes.shape({
    id: PropTypes.string,
    summary: PropTypes.string,
    start: PropTypes.shape({
      dateTime: PropTypes.string,
      date: PropTypes.string,
    }),
    end: PropTypes.shape({
      dateTime: PropTypes.string,
      date: PropTypes.string,
    }),
    location: PropTypes.string,
    hangoutLink: PropTypes.string,
    attendees: PropTypes.array,
  })),
  onInviteResponded: PropTypes.func,
};

export default CalendarInvites;