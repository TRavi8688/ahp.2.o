import React, { useState } from 'react';
import { AppBar, Toolbar, Typography, IconButton, Badge, Avatar, Box, InputBase, Menu, MenuItem } from '@mui/material';
import { useLocation } from 'react-router-dom';

import NotificationsIcon from '@mui/icons-material/Notifications';
import CameraAltIcon from '@mui/icons-material/CameraAlt';
import SearchIcon from '@mui/icons-material/Search';

export default function Topbar({ onLogout, onOpenScan }) {
    const location = useLocation();
    const [anchorEl, setAnchorEl] = useState(null);

    const handleProfileClick = (event) => setAnchorEl(event.currentTarget);
    const handleProfileClose = () => setAnchorEl(null);

    // Dynamic Title based on route
    const getPageTitle = () => {
        const path = location.pathname;
        if (path === '/') return 'Dashboard';
        if (path.startsWith('/patients')) return 'My Patients';
        if (path.startsWith('/schedule')) return 'Schedule';
        if (path.startsWith('/prescriptions')) return 'Prescriptions';
        if (path.startsWith('/history')) return 'Records Shared';
        if (path.startsWith('/analytics')) return 'Analytics';
        if (path.startsWith('/alerts')) return 'Alerts';
        if (path.startsWith('/settings')) return 'Settings';
        if (path.startsWith('/patient/')) return 'Patient Detail';
        return 'AHP Portal';
    };

    return (
        <AppBar position="sticky" elevation={0} sx={{ bgcolor: 'white', color: 'text.primary', borderBottom: '1px solid #e5e7eb', height: 56, justifyContent: 'center' }}>
            <Toolbar sx={{ minHeight: '56px !important', px: 3 }}>
                {/* Left - Title */}
                <Box sx={{ width: '250px' }}>
                    <Typography variant="subtitle1" fontWeight="bold">
                        {getPageTitle()}
                    </Typography>
                </Box>

                {/* Center - Search Bar */}
                <Box sx={{ flexGrow: 1, display: 'flex', justifyContent: 'center' }}>
                    <Box sx={{
                        display: 'flex',
                        alignItems: 'center',
                        bgcolor: '#f3f4f6',
                        borderRadius: 2,
                        px: 2,
                        py: 0.5,
                        width: '100%',
                        maxWidth: 400
                    }}>
                        <SearchIcon sx={{ color: '#9ca3af', fontSize: 20, mr: 1 }} />
                        <InputBase
                            placeholder="Search patient name or AHP ID..."
                            sx={{ flex: 1, fontSize: '0.875rem' }}
                        />
                    </Box>
                </Box>

                {/* Right - Actions */}
                <Box sx={{ display: 'flex', alignItems: 'center', gap: 1.5, width: '250px', justifyContent: 'flex-end' }}>
                    <IconButton color="default" onClick={onOpenScan} size="small" sx={{ color: '#4b5563', bgcolor: '#f3f4f6' }}>
                        <CameraAltIcon fontSize="small" />
                    </IconButton>

                    <IconButton color="default" size="small" sx={{ color: '#4b5563' }}>
                        <Badge badgeContent={2} color="error">
                            <NotificationsIcon fontSize="small" />
                        </Badge>
                    </IconButton>

                    <Avatar
                        onClick={handleProfileClick}
                        sx={{ bgcolor: '#3b82f6', width: 32, height: 32, cursor: 'pointer', ml: 1, fontSize: '0.875rem' }}
                    >
                        GS
                    </Avatar>

                    <Menu
                        anchorEl={anchorEl}
                        open={Boolean(anchorEl)}
                        onClose={handleProfileClose}
                        transformOrigin={{ horizontal: 'right', vertical: 'top' }}
                        anchorOrigin={{ horizontal: 'right', vertical: 'bottom' }}
                    >
                        <MenuItem onClick={handleProfileClose}>View Profile</MenuItem>
                        <MenuItem onClick={handleProfileClose}>Change Password</MenuItem>
                        <MenuItem onClick={() => { handleProfileClose(); onLogout(); }}>Sign Out</MenuItem>
                    </Menu>
                </Box>
            </Toolbar>
        </AppBar>
    );
}
