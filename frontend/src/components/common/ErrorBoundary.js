import React from 'react';
import { Container, Paper, Typography, Button } from '@mui/material';
import logger from '../../utils/logger';

class ErrorBoundary extends React.Component {
  constructor(props) {
    super(props);
    this.state = { hasError: false, error: null, errorInfo: null };
  }

  static getDerivedStateFromError(error) {
    return { hasError: true };
  }

  componentDidCatch(error, errorInfo) {
    // Log the error
    logger.error('React Error Boundary caught an error:', {
      error: error,
      componentStack: errorInfo.componentStack
    });

    this.setState({
      error: error,
      errorInfo: errorInfo
    });
  }

  handleReload = () => {
    logger.info('User initiated page reload after error');
    window.location.reload();
  };

  render() {
    if (this.state.hasError) {
      return (
        <Container maxWidth="sm" sx={{ mt: 4 }}>
          <Paper sx={{ p: 3, textAlign: 'center' }}>
            <Typography variant="h5" component="h1" gutterBottom color="error">
              Something went wrong
            </Typography>
            <Typography variant="body1" color="text.secondary" paragraph>
              We apologize for the inconvenience. Please try refreshing the page.
            </Typography>
            {process.env.NODE_ENV === 'development' && this.state.error && (
              <Typography 
                variant="body2" 
                component="pre" 
                sx={{ 
                  mt: 2, 
                  p: 2, 
                  bgcolor: 'grey.100', 
                  borderRadius: 1,
                  overflow: 'auto',
                  textAlign: 'left'
                }}
              >
                {this.state.error.toString()}
                {this.state.errorInfo.componentStack}
              </Typography>
            )}
            <Button
              variant="contained"
              color="primary"
              onClick={this.handleReload}
              sx={{ mt: 2 }}
            >
              Reload Page
            </Button>
          </Paper>
        </Container>
      );
    }

    return this.props.children;
  }
}

export default ErrorBoundary;