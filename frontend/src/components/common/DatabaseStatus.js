import React from 'react';
import { Chip, Tooltip } from '@mui/material';
import StorageIcon from '@mui/icons-material/Storage';

function DatabaseStatus({ status, showLabel = true }) {
  const getStatusColor = () => {
    switch (status) {
      case 'available':
        return 'success';
      case 'degraded':
        return 'warning';
      case 'unavailable':
        return 'error';
      default:
        return 'default';
    }
  };

  const getStatusLabel = () => {
    switch (status) {
      case 'available':
        return 'Database Connected';
      case 'degraded':
        return 'Database Performance Issues';
      case 'unavailable':
        return 'Database Unavailable';
      default:
        return 'Database Status Unknown';
    }
  };

  const getTooltipMessage = () => {
    switch (status) {
      case 'available':
        return 'Database is connected and working properly';
      case 'degraded':
        return 'Database is experiencing performance issues';
      case 'unavailable':
        return 'Database is currently unavailable. Some features may be limited';
      default:
        return 'Unable to determine database status';
    }
  };

  return (
    <Tooltip title={getTooltipMessage()}>
      <Chip
        icon={<StorageIcon />}
        label={showLabel ? getStatusLabel() : null}
        color={getStatusColor()}
        variant="outlined"
        size="small"
      />
    </Tooltip>
  );
}

export default DatabaseStatus;