import React from 'react';
import {
  List,
  ListItem,
  Typography,
  Box,
  Button,
  Divider,
  Chip,
} from '@mui/material';
import CheckCircleIcon from '@mui/icons-material/CheckCircle';
import CancelIcon from '@mui/icons-material/Cancel';
import AccessTimeIcon from '@mui/icons-material/AccessTime';
import VideocamIcon from '@mui/icons-material/Videocam';
import GroupIcon from '@mui/icons-material/Group';
import RoomIcon from '@mui/icons-material/Room';

function CalendarInvites({ invites = [] }) {
  const formatTime = (dateString) => {
    return new Intl.DateTimeFormat('en-US', {
      hour: 'numeric',
      minute: '2-digit',
      hour12: true,
    }).format(new Date(dateString));
  };

  const formatDate = (dateString) => {
    const date = new Date(dateString);
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

  // Group events by date
  const groupedInvites = invites.reduce((acc, invite) => {
    const date = formatDate(invite.startTime);
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
          {dateInvites.map((invite, idx) => (
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
                    {invite.title}
                  </Typography>
                  <Box sx={{ display: 'flex', gap: 1 }}>
                    <Button
                      variant="outlined"
                      color="primary"
                      size="small"
                      startIcon={<CheckCircleIcon />}
                      sx={{ borderRadius: 2 }}
                    >
                      Accept
                    </Button>
                    <Button
                      variant="outlined"
                      color="error"
                      size="small"
                      startIcon={<CancelIcon />}
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
                      {formatTime(invite.startTime)} - {formatTime(invite.endTime)}
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
                  {invite.isOnline && (
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

export default CalendarInvites;