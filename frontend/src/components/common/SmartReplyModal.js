import React, { useState, useCallback } from 'react';
import PropTypes from 'prop-types';
import {
  Dialog,
  DialogTitle,
  DialogContent,
  DialogActions,
  Button,
  Typography,
  Box,
  TextField,
  Card,
  CardContent,
  CircularProgress,
  Snackbar,
  Alert,
} from '@mui/material';
import { styled } from '@mui/material/styles';
import EditIcon from '@mui/icons-material/Edit';
import SendIcon from '@mui/icons-material/Send';
import { summary } from '../../utils/api';
import logger from '../../utils/logger';

const ReplyCard = styled(Card)(({ theme }) => ({
  marginBottom: theme.spacing(2),
  borderRadius: '8px',
  cursor: 'pointer',
  transition: 'all 0.2s ease',
  border: `1px solid ${theme.palette.grey[300]}`,
  '&:hover': {
    transform: 'translateY(-2px)',
    boxShadow: theme.shadows[4],
    borderColor: theme.palette.primary.main,
  },
}));

const ThreadPreview = styled(Box)(({ theme }) => ({
  padding: theme.spacing(2),
  backgroundColor: theme.palette.grey[50],
  borderRadius: '8px',
  marginBottom: theme.spacing(3),
  maxHeight: '200px',
  overflow: 'auto',
}));

const SmartReplyModal = ({ open, email, onClose }) => {
  const [loading, setLoading] = useState(false);
  const [replies, setReplies] = useState([]);
  const [selectedReply, setSelectedReply] = useState(null);
  const [editedReply, setEditedReply] = useState('');
  const [isEditing, setIsEditing] = useState(false);
  const [sending, setSending] = useState(false);
  const [error, setError] = useState(null);
  const [success, setSuccess] = useState(false);
  const [thread, setThread] = useState(null);

  const handleClose = () => {
    setReplies([]);
    setSelectedReply(null);
    setEditedReply('');
    setIsEditing(false);
    setError(null);
    onClose();
  };

  const generateReplies = useCallback(async () => {
    try {
      setLoading(true);
      setError(null);
      logger.info('Generating smart replies for email:', { threadId: email?.threadId });
      const response = await summary.getSmartReplies(email.threadId);
      setReplies(response.data.replies);
      setThread(response.data.thread);
      logger.info('Smart replies generated successfully');
    } catch (err) {
      logger.error('Failed to generate smart replies:', err);
      setError('Failed to generate replies. Please try again.');
    } finally {
      setLoading(false);
    }
  }, [email]);

  const handleReplySelect = (reply) => {
    setSelectedReply(reply);
    setEditedReply(reply);
    setIsEditing(true);
  };

  const handleSend = async () => {
    try {
      setSending(true);
      setError(null);
      logger.info('Sending email reply');
      
      await summary.sendReply({
        threadId: email.threadId,
        reply: editedReply,
        to: email.from,
        subject: `Re: ${email.subject}`
      });
      
      setSuccess(true);
      logger.info('Reply sent successfully');
      setTimeout(handleClose, 2000);
    } catch (err) {
      logger.error('Failed to send reply:', err);
      setError('Failed to send reply. Please try again.');
    } finally {
      setSending(false);
    }
  };

  React.useEffect(() => {
    if (open && email) {
      generateReplies();
    }
  }, [open, email, generateReplies]);

  return (
    <>
      <Dialog 
        open={open} 
        onClose={handleClose} 
        maxWidth="md" 
        fullWidth
        PaperProps={{
          sx: { borderRadius: '12px' }
        }}
      >
        <DialogTitle>
          <Typography variant="h6" component="div">
            Smart Reply
          </Typography>
          <Typography variant="subtitle2" color="text.secondary">
            {email?.subject}
          </Typography>
        </DialogTitle>
        <DialogContent>
          {thread && (
            <ThreadPreview>
              <Typography variant="subtitle2" gutterBottom>
                Thread Preview:
              </Typography>
              {thread.messages.map((msg) => (
                <Box key={`${msg.id}-${msg.date}`} sx={{ mb: 1 }}>
                  <Typography variant="caption" color="text.secondary">
                    From: {msg.from}
                  </Typography>
                  <Typography variant="body2">
                    {msg.snippet}
                  </Typography>
                </Box>
              ))}
            </ThreadPreview>
          )}

          {loading ? (
            <Box sx={{ display: 'flex', justifyContent: 'center', py: 4 }}>
              <CircularProgress />
            </Box>
          ) : isEditing ? (
            <TextField
              fullWidth
              multiline
              rows={4}
              value={editedReply}
              onChange={(e) => setEditedReply(e.target.value)}
              variant="outlined"
              placeholder="Edit your reply..."
              sx={{ mt: 2 }}
            />
          ) : (
            <Box>
              <Typography variant="subtitle2" gutterBottom>
                Choose a reply:
              </Typography>
              {replies.map((reply) => (
                <ReplyCard 
                  key={reply}
                  onClick={() => handleReplySelect(reply)}
                  variant="outlined"
                >
                  <CardContent>
                    <Typography>{reply}</Typography>
                  </CardContent>
                </ReplyCard>
              ))}
            </Box>
          )}
        </DialogContent>
        <DialogActions sx={{ px: 3, pb: 2 }}>
          <Button onClick={handleClose} disabled={sending}>
            Cancel
          </Button>
          {isEditing && !sending && (
            <Button 
              startIcon={<EditIcon />}
              onClick={() => setIsEditing(false)}
            >
              Choose Another
            </Button>
          )}
          {selectedReply && (
            <Button
              variant="contained"
              onClick={handleSend}
              disabled={!editedReply || sending}
              startIcon={sending ? <CircularProgress size={20} /> : <SendIcon />}
            >
              {sending ? 'Sending...' : 'Send Reply'}
            </Button>
          )}
        </DialogActions>
      </Dialog>

      <Snackbar
        open={success}
        autoHideDuration={3000}
        onClose={() => setSuccess(false)}
      >
        <Alert severity="success" elevation={6} variant="filled">
          Reply sent successfully!
        </Alert>
      </Snackbar>

      <Snackbar
        open={Boolean(error)}
        autoHideDuration={5000}
        onClose={() => setError(null)}
      >
        <Alert severity="error" elevation={6} variant="filled">
          {error}
        </Alert>
      </Snackbar>
    </>
  );
};

SmartReplyModal.propTypes = {
  open: PropTypes.bool.isRequired,
  email: PropTypes.shape({
    id: PropTypes.string.isRequired,
    threadId: PropTypes.string.isRequired,
    subject: PropTypes.string.isRequired,
    from: PropTypes.string.isRequired,
    date: PropTypes.string.isRequired,
    snippet: PropTypes.string
  }),
  onClose: PropTypes.func.isRequired
};

export default SmartReplyModal;