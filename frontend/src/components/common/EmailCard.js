import React from 'react';
import {
  Card,
  CardContent,
  Typography,
  Box,
  IconButton,
  Tooltip,
} from '@mui/material';
import ReplyIcon from '@mui/icons-material/Reply';
import StarIcon from '@mui/icons-material/Star';
import PropTypes from 'prop-types';
import PriorityBadge from './PriorityBadge';

function EmailCard({ email, onSmartReply }) {
  // Add null check for the email prop
  if (!email) {
    return null;
  }

  const {
    subject = 'No Subject',
    sender = 'Unknown Sender',
    preview = '',
    timestamp = '',
    priority = 'LOW',
    isImportant = false,
  } = email;

  const formatDate = (timestamp) => {
    if (!timestamp) return '';
    const date = new Date(timestamp);
    return new Intl.DateTimeFormat('en-US', {
      month: 'short',
      day: 'numeric',
      hour: '2-digit',
      minute: '2-digit',
    }).format(date);
  };

  return (
    <Card
      sx={{
        mb: 2,
        borderRadius: 2,
        backgroundColor: 'rgba(255, 255, 255, 0.8)',
        backdropFilter: 'blur(20px)',
        border: '1px solid',
        borderColor: 'divider',
        '&:hover': {
          boxShadow: (theme) => theme.shadows[3],
          transform: 'translateY(-2px)',
          transition: 'all 0.2s ease-in-out',
        },
      }}
    >
      <CardContent>
        <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', mb: 1 }}>
          <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
            <Typography variant="subtitle1" component="div" fontWeight="500">
              {sender}
            </Typography>
            {isImportant && (
              <StarIcon
                fontSize="small"
                sx={{ color: (theme) => theme.palette.warning.main }}
              />
            )}
          </Box>
          <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
            <PriorityBadge priority={priority} />
            <Typography variant="caption" color="text.secondary">
              {formatDate(timestamp)}
            </Typography>
          </Box>
        </Box>

        <Typography variant="h6" gutterBottom sx={{ fontSize: '1rem', fontWeight: 500 }}>
          {subject}
        </Typography>

        <Typography
          variant="body2"
          color="text.secondary"
          sx={{
            display: '-webkit-box',
            WebkitLineClamp: 2,
            WebkitBoxOrient: 'vertical',
            overflow: 'hidden',
            mb: 2,
          }}
        >
          {preview}
        </Typography>

        <Box sx={{ display: 'flex', justifyContent: 'flex-end', alignItems: 'center', gap: 1 }}>
          <Tooltip title="Generate Smart Reply">
            <IconButton
              size="small"
              onClick={() => onSmartReply(email)}
              sx={{
                backgroundColor: (theme) => theme.palette.primary.main + '10',
                '&:hover': {
                  backgroundColor: (theme) => theme.palette.primary.main + '20',
                },
              }}
            >
              <ReplyIcon fontSize="small" color="primary" />
            </IconButton>
          </Tooltip>
        </Box>
      </CardContent>
    </Card>
  );
}

EmailCard.propTypes = {
  email: PropTypes.shape({
    subject: PropTypes.string,
    sender: PropTypes.string,
    preview: PropTypes.string,
    timestamp: PropTypes.string,
    priority: PropTypes.oneOf(['HIGH', 'MEDIUM', 'LOW']),
    isImportant: PropTypes.bool,
  }),
  onSmartReply: PropTypes.func.isRequired,
};

export default EmailCard;