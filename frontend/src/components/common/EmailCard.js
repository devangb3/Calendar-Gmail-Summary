import React from 'react';
import PropTypes from 'prop-types';
import {
  Card,
  CardContent,
  Typography,
  IconButton,
  Box,
  Tooltip,
} from '@mui/material';
import { styled } from '@mui/material/styles';
import SmartToyIcon from '@mui/icons-material/SmartToy';
import { format } from 'date-fns';

const StyledCard = styled(Card)(({ theme }) => ({
  marginBottom: theme.spacing(2),
  borderRadius: '12px',
  border: `1px solid ${theme.palette.grey[200]}`,
  '&:hover': {
    boxShadow: theme.shadows[4],
  },
}));

const EmailMeta = styled(Typography)(({ theme }) => ({
  color: theme.palette.text.secondary,
  fontSize: '0.875rem',
}));

const EmailCard = ({ email, onSmartReply }) => {
  const formatDate = (dateString) => {
    try {
      return format(new Date(dateString), 'MMM d, yyyy h:mm a');
    } catch {
      return dateString;
    }
  };

  return (
    <StyledCard>
      <CardContent>
        <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', mb: 1 }}>
          <Box>
            <Typography variant="h6" gutterBottom>
              {email.subject}
            </Typography>
            <EmailMeta>
              From: {email.from}
            </EmailMeta>
            <EmailMeta>
              {formatDate(email.date)}
            </EmailMeta>
          </Box>
          <Tooltip title="Generate Smart Reply">
            <IconButton 
              onClick={() => onSmartReply(email)} 
              color="primary"
              sx={{ 
                '&:hover': { 
                  backgroundColor: 'rgba(63, 81, 181, 0.08)' 
                } 
              }}
            >
              <SmartToyIcon />
            </IconButton>
          </Tooltip>
        </Box>
        <Typography 
          variant="body1" 
          color="text.primary"
          sx={{ 
            mt: 2,
            whiteSpace: 'pre-line',
            maxHeight: '100px',
            overflow: 'hidden',
            textOverflow: 'ellipsis',
          }}
        >
          {email.snippet}
        </Typography>
      </CardContent>
    </StyledCard>
  );
};

EmailCard.propTypes = {
  email: PropTypes.shape({
    id: PropTypes.string.isRequired,
    threadId: PropTypes.string.isRequired,
    subject: PropTypes.string.isRequired,
    from: PropTypes.string.isRequired,
    date: PropTypes.string.isRequired,
    snippet: PropTypes.string.isRequired
  }).isRequired,
  onSmartReply: PropTypes.func.isRequired
};

export default EmailCard;