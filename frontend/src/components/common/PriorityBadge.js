import React from 'react';
import { Chip } from '@mui/material';
import PropTypes from 'prop-types';

const priorityColors = {
  HIGH: {
    bg: '#fde8e8',
    text: '#e02424',
    border: '#fbd5d5'
  },
  MEDIUM: {
    bg: '#fdf6b2',
    text: '#c27803',
    border: '#fce96a'
  },
  LOW: {
    bg: '#def7ec',
    text: '#057a55',
    border: '#bcf0da'
  }
};

function PriorityBadge({ priority = 'LOW', size = 'small' }) {
  const colors = priorityColors[priority] || priorityColors.LOW;
  
  return (
    <Chip
      label={priority.charAt(0) + priority.slice(1).toLowerCase()}
      size={size}
      sx={{
        backgroundColor: colors.bg,
        color: colors.text,
        border: `1px solid ${colors.border}`,
        fontWeight: 500,
        '& .MuiChip-label': {
          px: 1,
        },
      }}
    />
  );
}

PriorityBadge.propTypes = {
  priority: PropTypes.oneOf(['HIGH', 'MEDIUM', 'LOW']),
  size: PropTypes.oneOf(['small', 'medium']),
};

export default PriorityBadge;