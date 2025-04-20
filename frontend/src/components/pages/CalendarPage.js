import React from 'react';
import { Box, Container, Typography, Paper } from '@mui/material';
import CalendarInvites from '../common/CalendarInvites';

function CalendarPage() {
  return (
    <Box sx={{ py: 3 }}>
      <Container maxWidth="lg">
        <Typography variant="h4" gutterBottom sx={{ mb: 4 }}>
          Calendar
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
          <CalendarInvites />
        </Paper>
      </Container>
    </Box>
  );
}

export default CalendarPage;