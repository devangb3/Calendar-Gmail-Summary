import React from 'react';
import { Chip } from '@mui/material';
import FlagIcon from '@mui/icons-material/Flag';

const priorityColors = {
  HIGH: {
    bg: '#ffebee',
    color: '#d32f2f',
    border: '#ef5350'
  },
  MEDIUM: {
    bg: '#fff3e0',
    color: '#ef6c00',
    border: '#ff9800'
  },
  LOW: {
    bg: '#e8f5e9',
    color: '#2e7d32',
    border: '#66bb6a'
  }
};

const PriorityBadge = ({ priority }) => {
  const colors = priorityColors[priority] || priorityColors.LOW;

  return (
    <Chip
      icon={<FlagIcon style={{ color: colors.color }} />}
      label={priority}
      size="small"
      sx={{
        backgroundColor: colors.bg,
        color: colors.color,
        border: `1px solid ${colors.border}`,
        '& .MuiChip-icon': {
          color: 'inherit'
        }
      }}
    />
  );
};

export default PriorityBadge;