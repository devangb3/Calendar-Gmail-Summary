import React from 'react';
import { Link as RouterLink, useLocation } from 'react-router-dom';
import {
  Drawer,
  List,
  ListItemButton,
  ListItemIcon,
  ListItemText,
  Toolbar,
  Box,
  Typography,
} from '@mui/material';
import DashboardIcon from '@mui/icons-material/Dashboard';
import EventIcon from '@mui/icons-material/Event';
import EmailIcon from '@mui/icons-material/Email';
import AssignmentIcon from '@mui/icons-material/Assignment';

const drawerWidth = 240;

const menuItems = [
  { text: 'Dashboard', icon: <DashboardIcon />, path: '/' },
  { text: 'Calendar', icon: <EventIcon />, path: '/calendar' },
  { text: 'Emails', icon: <EmailIcon />, path: '/emails' },
  { text: 'Tasks', icon: <AssignmentIcon />, path: '/tasks' },
];

function AppSidebar() {
  const location = useLocation();

  return (
    <Drawer
      variant="permanent"
      sx={{
        width: drawerWidth,
        flexShrink: 0,
        [`& .MuiDrawer-paper`]: {
          width: drawerWidth,
          boxSizing: 'border-box',
          borderRight: 'none',
          backgroundColor: '#f8f9fa',
        },
      }}
    >
      <Toolbar sx={{ display: 'flex', alignItems: 'center', justifyContent: 'center', py: 2 }}>
        <Typography variant="h6" noWrap component="div" color="primary" fontWeight="bold">
          Daily Digest
        </Typography>
      </Toolbar>
      <Box sx={{ overflow: 'auto', px: 1 }}>
        <List>
          {menuItems.map((item) => (
            <ListItemButton
              key={item.text}
              component={RouterLink}
              to={item.path}
              sx={{
                borderRadius: '8px',
                marginBottom: '4px',
                backgroundColor: location.pathname === item.path ? 'rgba(63, 81, 181, 0.12)' : 'transparent',
                color: location.pathname === item.path ? 'primary.main' : 'grey.800',
                '&:hover': {
                  backgroundColor: 'rgba(63, 81, 181, 0.08)',
                },
                '& .MuiListItemIcon-root': {
                  color: location.pathname === item.path ? 'primary.main' : 'grey.700',
                },
              }}
            >
              <ListItemIcon sx={{ minWidth: '40px' }}>
                {item.icon}
              </ListItemIcon>
              <ListItemText 
                primary={item.text}
                primaryTypographyProps={{
                  fontWeight: location.pathname === item.path ? 600 : 400,
                }}
              />
            </ListItemButton>
          ))}
        </List>
      </Box>
    </Drawer>
  );
}

export default AppSidebar;