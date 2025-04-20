import React, { useState, useEffect } from 'react';
import {
  Dialog,
  DialogTitle,
  DialogContent,
  DialogActions,
  Button,
  Typography,
  Box,
  CircularProgress,
  TextField,
  Chip,
} from '@mui/material';
import PropTypes from 'prop-types';
import AutoAwesomeIcon from '@mui/icons-material/AutoAwesome';
import { summary } from '../../utils/api';
import logger from '../../utils/logger';

function SmartReplyModal({ open, email, onClose }) {
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);
  const [suggestions, setSuggestions] = useState([
    "I'll look into this and get back to you soon.",
    "Thanks for your email. I'm working on it.",
    "Got it, will review and respond shortly."
  ]);
  const [customReply, setCustomReply] = useState('');

  const handleSuggestionClick = (suggestion) => {
    setCustomReply(suggestion);
  };

  const handleSend = async () => {
    if (!customReply.trim()) return;
    
    setLoading(true);
    setError(null);
    
    try {
      await summary.sendReply({
        threadId: email.threadId,
        to: email.from_email,
        reply: customReply.trim()
      });
      onClose();
    } catch (err) {
      setError(err.message || 'Failed to send reply');
      logger.error('Failed to send email reply:', err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    const loadSuggestions = async () => {
      if (email?.threadId) {
        try {
          const response = await summary.getSmartReplies(email.threadId);
          if (response.data?.suggestions) {
            setSuggestions(response.data.suggestions);
          }
        } catch (err) {
          logger.error('Failed to load smart replies:', err);
          // Keep default suggestions on error
        }
      }
    };
    
    if (open) {
      loadSuggestions();
    }
  }, [email?.threadId, open]);

  if (!email) return null;

  return (
    <Dialog 
      open={open} 
      onClose={onClose}
      maxWidth="sm"
      fullWidth
      PaperProps={{
        sx: {
          borderRadius: 2,
          backgroundColor: 'rgba(255, 255, 255, 0.9)',
          backdropFilter: 'blur(20px)',
        }
      }}
    >
      <DialogTitle sx={{ pb: 1 }}>
        <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
          <AutoAwesomeIcon color="primary" />
          <Typography variant="h6">Smart Reply</Typography>
        </Box>
      </DialogTitle>
      <DialogContent>
        <Box sx={{ mb: 3 }}>
          <Typography variant="subtitle2" color="text.secondary" gutterBottom>
            Replying to: {email.sender}
          </Typography>
          <Typography variant="subtitle1" gutterBottom>
            {email.subject}
          </Typography>
        </Box>

        <Typography variant="subtitle2" gutterBottom>
          Suggested Replies:
        </Typography>
        <Box sx={{ display: 'flex', gap: 1, flexWrap: 'wrap', mb: 3 }}>
          {suggestions.map((suggestion) => (
            <Chip
              key={suggestion}
              label={suggestion}
              onClick={() => handleSuggestionClick(suggestion)}
              sx={{
                backgroundColor: 'rgba(63, 81, 181, 0.08)',
                '&:hover': {
                  backgroundColor: 'rgba(63, 81, 181, 0.12)',
                },
              }}
            />
          ))}
        </Box>

        <TextField
          fullWidth
          multiline
          rows={4}
          value={customReply}
          onChange={(e) => setCustomReply(e.target.value)}
          placeholder="Type your reply or click a suggestion above"
          variant="outlined"
          error={Boolean(error)}
          helperText={error}
          sx={{
            '& .MuiOutlinedInput-root': {
              backgroundColor: 'rgba(255, 255, 255, 0.8)',
            },
          }}
        />
      </DialogContent>
      <DialogActions sx={{ p: 2 }}>
        <Button onClick={onClose} color="inherit">
          Cancel
        </Button>
        <Button
          onClick={handleSend}
          variant="contained"
          disabled={!customReply.trim() || loading}
          startIcon={loading && <CircularProgress size={20} />}
        >
          Send Reply
        </Button>
      </DialogActions>
    </Dialog>
  );
}

SmartReplyModal.propTypes = {
  open: PropTypes.bool.isRequired,
  email: PropTypes.shape({
    sender: PropTypes.string.isRequired,
    subject: PropTypes.string.isRequired,
    threadId: PropTypes.string,
    from_email: PropTypes.string,
  }),
  onClose: PropTypes.func.isRequired,
};

export default SmartReplyModal;