import React, { useState } from 'react';
import { Box, Container, Typography, Paper, Grid, List, ListItem, Checkbox, ListItemText, IconButton } from '@mui/material';
import DashboardCard from '../common/DashboardCard';
import CheckCircleIcon from '@mui/icons-material/CheckCircle';
import DeleteOutlineIcon from '@mui/icons-material/DeleteOutline';
import PropTypes from 'prop-types';

function TaskItem({ task, onComplete, onDelete }) {
  return (
    <ListItem
      sx={{
        borderBottom: '1px solid',
        borderColor: 'divider',
        py: 2,
        '&:last-child': {
          borderBottom: 'none',
        },
      }}
    >
      <Checkbox
        checked={task.completed}
        onChange={() => onComplete(task.id)}
        icon={<CheckCircleIcon />}
        checkedIcon={<CheckCircleIcon color="primary" />}
      />
      <ListItemText
        primary={task.title}
        secondary={task.source}
        sx={{
          '& .MuiListItemText-primary': {
            textDecoration: task.completed ? 'line-through' : 'none',
            color: task.completed ? 'text.secondary' : 'text.primary',
          },
        }}
      />
      <IconButton onClick={() => onDelete(task.id)} size="small" color="error">
        <DeleteOutlineIcon />
      </IconButton>
    </ListItem>
  );
}

TaskItem.propTypes = {
  task: PropTypes.shape({
    id: PropTypes.oneOfType([PropTypes.string, PropTypes.number]).isRequired,
    title: PropTypes.string.isRequired,
    source: PropTypes.string,
    completed: PropTypes.bool.isRequired,
  }).isRequired,
  onComplete: PropTypes.func.isRequired,
  onDelete: PropTypes.func.isRequired,
};

function TasksPage() {
  const [tasks, setTasks] = useState([]);

  const handleComplete = (taskId) => {
    setTasks(prevTasks =>
      prevTasks.map(task =>
        task.id === taskId
          ? { ...task, completed: !task.completed }
          : task
      )
    );
  };

  const handleDelete = (taskId) => {
    setTasks(prevTasks => prevTasks.filter(task => task.id !== taskId));
  };

  return (
    <Box sx={{ py: 3 }}>
      <Container maxWidth="lg">
        <Typography variant="h4" gutterBottom sx={{ mb: 4 }}>
          Action Items
        </Typography>

        <Grid container spacing={3}>
          <Grid item xs={12}>
            <Paper 
              elevation={0}
              sx={{ 
                p: 3,
                borderRadius: 4,
                backgroundColor: 'rgba(255, 255, 255, 0.8)',
                backdropFilter: 'blur(20px)'
              }}
            >
              <List sx={{ width: '100%' }}>
                {tasks.map((task) => (
                  <TaskItem
                    key={task.id}
                    task={task}
                    onComplete={handleComplete}
                    onDelete={handleDelete}
                  />
                ))}
                {tasks.length === 0 && (
                  <Typography variant="body1" color="text.secondary" sx={{ textAlign: 'center', py: 4 }}>
                    No action items found
                  </Typography>
                )}
              </List>
            </Paper>
          </Grid>

          <Grid item xs={12} md={6}>
            <DashboardCard title="Email Tasks">
              <Box sx={{ textAlign: 'center', py: 3 }}>
                <Typography variant="h3" color="primary" gutterBottom>
                  {tasks.filter(t => t.source?.includes('From:')).length}
                </Typography>
                <Typography variant="body2" color="text.secondary">
                  Tasks derived from emails
                </Typography>
              </Box>
            </DashboardCard>
          </Grid>

          <Grid item xs={12} md={6}>
            <DashboardCard title="Calendar Tasks">
              <Box sx={{ textAlign: 'center', py: 3 }}>
                <Typography variant="h3" color="primary" gutterBottom>
                  {tasks.filter(t => t.source?.includes('Calendar:')).length}
                </Typography>
                <Typography variant="body2" color="text.secondary">
                  Tasks from calendar events
                </Typography>
              </Box>
            </DashboardCard>
          </Grid>
        </Grid>
      </Container>
    </Box>
  );
}

export default TasksPage;