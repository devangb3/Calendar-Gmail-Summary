import React, { useState, useEffect } from 'react';
import { Box, Container, Typography, Paper, CircularProgress, Alert } from '@mui/material';
import CalendarInvites from '../common/CalendarInvites';
import { calendar } from '../../utils/api';
import logger from '../../utils/logger';

function CalendarPage() {
  const [invites, setInvites] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  const fetchInvites = async () => {
    try {
      setLoading(true);
      setError(null);
      const response = await calendar.getPendingInvites();
      setInvites(response.data?.pending_invites || []);
    } catch (err) {
      logger.error('Error fetching pending invites:', err);
      setError(err.message || 'Failed to fetch pending invites');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchInvites();
  }, []);

  const handleInviteResponded = (inviteId) => {
    // Remove the responded invite from the list
    setInvites(currentInvites => currentInvites.filter(invite => invite.id !== inviteId));
  };

  let content;
  if (loading) {
    content = (
      <Box sx={{ display: 'flex', justifyContent: 'center', py: 4 }}>
        <CircularProgress />
      </Box>
    );
  } else if (error) {
    content = <Alert severity="error" sx={{ mb: 2 }}>{error}</Alert>;
  } else {
    content = <CalendarInvites invites={invites} onInviteResponded={handleInviteResponded} />;
  }

  return (
    <Box sx={{ py: 3 }}>
      <Container maxWidth="lg">
        <Typography variant="h4" gutterBottom sx={{ mb: 4 }}>
          Calendar Invites
        </Typography>
        
        <Paper 
          elevation={0}
          sx={{ 
            p: 3, 
            mb: 3, 
            borderRadius: 4,
            backgroundColor: 'rgba(255, 255, 255, 0.8)',
            backdropFilter: 'blur(20px)'
          }}
        >
          {content}
        </Paper>
      </Container>
    </Box>
  );
}

export default CalendarPage;