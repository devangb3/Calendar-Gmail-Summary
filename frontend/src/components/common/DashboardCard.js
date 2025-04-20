import React from 'react';
import { Paper, Typography, Box } from '@mui/material';
import PropTypes from 'prop-types';

function DashboardCard({ title, subtitle, children, action, elevation = 0 }) {
  return (
    <Paper
      elevation={elevation}
      sx={{
        p: 3,
        height: '100%',
        borderRadius: 4,
        backgroundColor: 'rgba(255, 255, 255, 0.8)',
        backdropFilter: 'blur(20px)',
        display: 'flex',
        flexDirection: 'column',
      }}
    >
      <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', mb: 2 }}>
        <Box>
          {title && (
            <Typography variant="h6" gutterBottom={!!subtitle}>
              {title}
            </Typography>
          )}
          {subtitle && (
            <Typography variant="body2" color="text.secondary">
              {subtitle}
            </Typography>
          )}
        </Box>
        {action && <Box>{action}</Box>}
      </Box>
      <Box sx={{ flexGrow: 1 }}>{children}</Box>
    </Paper>
  );
}

DashboardCard.propTypes = {
  title: PropTypes.string,
  subtitle: PropTypes.string,
  children: PropTypes.node,
  action: PropTypes.node,
  elevation: PropTypes.number,
};

export default DashboardCard;