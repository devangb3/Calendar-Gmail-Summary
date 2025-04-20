import React, { useState, useEffect } from 'react';
import { Box, Container, Typography, Paper, Tabs, Tab } from '@mui/material';
import EmailCard from '../common/EmailCard';
import SmartReplyModal from '../common/SmartReplyModal';
import { summary } from '../../utils/api';
import logger from '../../utils/logger';

function EmailPage() {
  const [selectedTab, setSelectedTab] = useState(0);
  const [selectedEmail, setSelectedEmail] = useState(null);
  const [showSmartReplyModal, setShowSmartReplyModal] = useState(false);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [emails, setEmails] = useState({
    important: [],
    recent: [],
    actionNeeded: []
  });

  useEffect(() => {
    fetchEmails();
  }, []);

  const fetchEmails = async () => {
    try {
      setLoading(true);
      const response = await summary.get();
      const summaryData = JSON.parse(response.data.summary);
      
      // Format emails with required fields for components
      const formatEmails = (emailList) => {
        return emailList.map(email => ({
          ...email,
          sender: email.from || email.sender || 'Unknown Sender',
          subject: email.subject || 'No Subject',
          preview: email.snippet || email.preview || '',
          timestamp: email.date || email.timestamp,
          priority: email.priority || 'LOW',
          isImportant: email.isImportant || false,
          id: email.id || email.threadId,
          threadId: email.threadId
        }));
      };
      
      setEmails({
        important: formatEmails(summaryData.emails?.important || []),
        recent: formatEmails(summaryData.emails?.recent || []),
        actionNeeded: formatEmails(summaryData.emails?.needsAction || [])
      });
    } catch (err) {
      logger.error('Error fetching emails:', err);
      setError(err.message || 'Failed to fetch emails');
    } finally {
      setLoading(false);
    }
  };

  const handleTabChange = (event, newValue) => {
    setSelectedTab(newValue);
  };

  const handleSmartReply = (email) => {
    if (!email?.sender || !email?.subject) {
      logger.warn('Attempted to open smart reply for email without required fields:', email);
      return;
    }
    setSelectedEmail(email);
    setShowSmartReplyModal(true);
  };

  const getEmailsByTab = () => {
    switch (selectedTab) {
      case 0:
        return emails.important;
      case 1:
        return emails.recent;
      case 2:
        return emails.actionNeeded;
      default:
        return [];
    }
  };

  return (
    <Box sx={{ py: 3 }}>
      <Container maxWidth="lg">
        <Typography variant="h4" gutterBottom sx={{ mb: 4 }}>
          Emails
        </Typography>

        <Paper 
          elevation={0}
          sx={{ 
            borderRadius: 4,
            backgroundColor: 'rgba(255, 255, 255, 0.8)',
            backdropFilter: 'blur(20px)'
          }}
        >
          <Tabs
            value={selectedTab}
            onChange={handleTabChange}
            sx={{
              borderBottom: 1,
              borderColor: 'divider',
              px: 2,
              '& .MuiTab-root': {
                textTransform: 'none',
                fontSize: '1rem',
                fontWeight: 500,
              }
            }}
          >
            <Tab label={`Important (${emails.important.length})`} />
            <Tab label={`Recent (${emails.recent.length})`} />
            <Tab label={`Needs Action (${emails.actionNeeded.length})`} />
          </Tabs>

          <Box sx={{ p: 3 }}>
            {loading ? (
              <Typography color="text.secondary" align="center">Loading emails...</Typography>
            ) : error ? (
              <Typography color="error" align="center">{error}</Typography>
            ) : (
              <>
                {getEmailsByTab().map((email) => (
                  <EmailCard
                    key={email.id || email.threadId}
                    email={email}
                    onSmartReply={handleSmartReply}
                  />
                ))}
                {getEmailsByTab().length === 0 && (
                  <Typography color="text.secondary" align="center">
                    No emails found in this category
                  </Typography>
                )}
              </>
            )}
          </Box>
        </Paper>

        {selectedEmail && (
          <SmartReplyModal
            open={showSmartReplyModal}
            email={selectedEmail}
            onClose={() => {
              setShowSmartReplyModal(false);
              setSelectedEmail(null);
            }}
          />
        )}
      </Container>
    </Box>
  );
}

export default EmailPage;