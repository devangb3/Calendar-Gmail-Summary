import React from 'react';
import { Tooltip, IconButton } from '@mui/material';
import StorageIcon from '@mui/icons-material/Storage';
import CheckCircleOutlineIcon from '@mui/icons-material/CheckCircleOutline';
import ErrorOutlineIcon from '@mui/icons-material/ErrorOutline';
import PropTypes from 'prop-types';

function DatabaseStatus({ status = 'available', showLabel = true }) {
  const getStatusColor = () => {
    switch (status) {
      case 'available':
        return '#10B981'; // success green
      case 'unavailable':
        return '#EF4444'; // error red
      default:
        return '#F59E0B'; // warning yellow
    }
  };

  const getStatusIcon = () => {
    switch (status) {
      case 'available':
        return <CheckCircleOutlineIcon sx={{ color: getStatusColor() }} />;
      case 'unavailable':
        return <ErrorOutlineIcon sx={{ color: getStatusColor() }} />;
      default:
        return <StorageIcon sx={{ color: getStatusColor() }} />;
    }
  };

  const getStatusText = () => {
    switch (status) {
      case 'available':
        return 'Database is connected';
      case 'unavailable':
        return 'Database is disconnected';
      default:
        return 'Checking database status';
    }
  };

  return (
    <Tooltip title={getStatusText()}>
      <IconButton
        size="small"
        sx={{
          p: 0.5,
          bgcolor: `${getStatusColor()}15`,
          '&:hover': {
            bgcolor: `${getStatusColor()}25`,
          },
        }}
      >
        {getStatusIcon()}
      </IconButton>
    </Tooltip>
  );
}

DatabaseStatus.propTypes = {
  status: PropTypes.oneOf(['available', 'unavailable', 'loading']),
  showLabel: PropTypes.bool,
};

export default DatabaseStatus;