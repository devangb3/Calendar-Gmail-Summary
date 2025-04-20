import React from 'react';
import { Paper, Box, Typography } from '@mui/material';
import { styled } from '@mui/material/styles';

const StyledPaper = styled(Paper)(({ theme }) => ({
  padding: theme.spacing(3),
  borderRadius: '16px',
  background: '#fff',
  boxShadow: '0 4px 20px 0 rgba(0, 0, 0, 0.05)',
  border: '1px solid rgba(63, 81, 181, 0.08)',
  height: '100%',
  display: 'flex',
  flexDirection: 'column',
}));

const DashboardCard = ({ title, icon, children }) => {
  return (
    <StyledPaper>
      <Box sx={{ display: 'flex', alignItems: 'center', mb: 2 }}>
        {icon && (
          <Box sx={{ mr: 1.5, color: 'primary.main', display: 'flex' }}>
            {icon}
          </Box>
        )}
        <Typography variant="h6" component="h2" color="primary">
          {title}
        </Typography>
      </Box>
      {children}
    </StyledPaper>
  );
};

export default DashboardCard;