import React from 'react';
import { Drawer, List, ListItem, ListItemIcon, ListItemText, Typography, Box, Divider, Badge, Button } from '@mui/material';
import { useNavigate, useLocation } from 'react-router-dom';

// Icons
import HomeIcon from '@mui/icons-material/Home';
import PeopleIcon from '@mui/icons-material/People';
import CalendarMonthIcon from '@mui/icons-material/CalendarMonth';
import QrCodeScannerIcon from '@mui/icons-material/QrCodeScanner';
import MedicationIcon from '@mui/icons-material/Medication';
import FolderSharedIcon from '@mui/icons-material/FolderShared';
import BarChartIcon from '@mui/icons-material/BarChart';
import NotificationsIcon from '@mui/icons-material/Notifications';
import SettingsIcon from '@mui/icons-material/Settings';
import WarningAmberIcon from '@mui/icons-material/WarningAmber';

const drawerWidth = 240;

export default function Sidebar({ onOpenScan }) {
    const navigate = useNavigate();
    const location = useLocation();
    const [profile, setProfile] = React.useState(null);
    const [stats, setStats] = React.useState({
        patients_count: 0,
        schedule_count: 0,
        alerts_count: 0,
        pending_rx_count: 0
    });

    React.useEffect(() => {
        const fetchData = async () => {
            const token = localStorage.getItem('token');
            if (!token) return;

            try {
                // Fetch Profile
                const profileRes = await fetch('http://localhost:8000/doctor/profile/me', {
                    headers: { 'Authorization': `Bearer ${token}` }
                });
                if (profileRes.ok) setProfile(await profileRes.json());

                // Fetch Stats
                const statsRes = await fetch('http://localhost:8000/doctor/stats', {
                    headers: { 'Authorization': `Bearer ${token}` }
                });
                if (statsRes.ok) setStats(await statsRes.json());
            } catch (err) {
                console.error("Sidebar fetch error:", err);
            }
        };
        fetchData();
    }, []);

    // Grouped Menu Items
    const menuSections = [
        {
            title: 'Main',
            items: [
                { text: 'Dashboard', icon: <HomeIcon />, path: '/' },
                { text: 'My Patients', icon: <PeopleIcon />, path: '/patients', badge: stats.patients_count },
                { text: 'Schedule', icon: <CalendarMonthIcon />, path: '/schedule', badge: stats.schedule_count },
            ]
        },
        {
            title: 'Patient Access',
            items: [
                { text: 'Scan QR / Enter ID', icon: <QrCodeScannerIcon />, action: onOpenScan },
                { text: 'Prescriptions', icon: <MedicationIcon />, path: '/prescriptions', badge: stats.pending_rx_count },
                { text: 'Records Shared', icon: <FolderSharedIcon />, path: '/history' },
            ]
        },
        {
            title: 'Insights',
            items: [
                { text: 'Analytics', icon: <BarChartIcon />, path: '/analytics' },
                { text: 'Alerts', icon: <NotificationsIcon />, path: '/alerts', badge: stats.alerts_count, badgeColor: 'error' },
            ]
        },
        {
            title: 'Account',
            items: [
                { text: 'Settings', icon: <SettingsIcon />, path: '/settings' },
            ]
        }
    ];

    return (
        <Drawer
            variant="permanent"
            sx={{
                width: drawerWidth,
                flexShrink: 0,
                '& .MuiDrawer-paper': {
                    width: drawerWidth,
                    boxSizing: 'border-box',
                    backgroundColor: '#111827', // Very Dark per spec, but we keep light theme elsewhere if needed, though sidebar can be dark. Using a rich dark tone.
                    color: '#e5e7eb'
                },
            }}
        >
            <Box sx={{ p: 3, display: 'flex', flexDirection: 'column', alignItems: 'center', textAlign: 'center' }}>
                <Box sx={{ display: 'flex', alignItems: 'center', mb: 2 }}>
                    <Box sx={{ width: 32, height: 32, bgcolor: '#0d9488', borderRadius: 1, display: 'flex', alignItems: 'center', justifyContent: 'center', mr: 1 }}>
                        <Typography sx={{ color: 'white', fontWeight: 'bold' }}>⚕</Typography>
                    </Box>
                    <Typography variant="h6" fontWeight="bold" color="white">AHP Doctor</Typography>
                </Box>
                <Typography variant="caption" sx={{ color: '#9ca3af', mb: 3 }}>Clinical Portal</Typography>

                <Box sx={{ display: 'flex', alignItems: 'center', width: '100%', gap: 1.5, bgcolor: 'rgba(255,255,255,0.05)', p: 1.5, borderRadius: 2 }}>
                    <Box sx={{ position: 'relative' }}>
                        <Box sx={{ width: 40, height: 40, borderRadius: '50%', bgcolor: '#3b82f6', display: 'flex', alignItems: 'center', justifyContent: 'center' }}>
                            <Typography fontWeight="bold" color="white">GS</Typography>
                        </Box>
                        <Box sx={{ position: 'absolute', bottom: 0, right: 0, width: 12, height: 12, bgcolor: '#22c55e', borderRadius: '50%', border: '2px solid #111827' }} />
                    </Box>
                    <Box sx={{ textAlign: 'left', flex: 1, overflow: 'hidden' }}>
                        <Typography variant="subtitle2" color="white" fontWeight="bold" noWrap>
                            {profile ? `Dr. ${profile.last_name}` : 'Loading...'}
                        </Typography>
                        <Typography variant="caption" sx={{ color: '#9ca3af' }} noWrap>
                            {profile ? profile.specialty : 'Verified Practitioner'}
                        </Typography>
                    </Box>
                </Box>
            </Box>

            <Divider sx={{ borderColor: 'rgba(255,255,255,0.1)' }} />

            <List sx={{ px: 2, flexGrow: 1, overflowY: 'auto' }}>
                {menuSections.map((section, idx) => (
                    <Box key={idx} sx={{ mb: 2 }}>
                        {/* Section Header */}
                        {/* <Typography variant="overline" sx={{ color: '#6b7280', px: 2, display: 'block', mb: 0.5, fontWeight: 600 }}>{section.title}</Typography> */}
                        {section.items.map((item) => (
                            <ListItem
                                button
                                key={item.text}
                                onClick={() => item.action ? item.action() : navigate(item.path)}
                                sx={{
                                    mb: 0.5,
                                    borderRadius: 1.5,
                                    py: 1,
                                    backgroundColor: location.pathname === item.path ? 'rgba(13, 148, 136, 0.15)' : 'transparent',
                                    borderLeft: location.pathname === item.path ? '3px solid #0d9488' : '3px solid transparent',
                                    '&:hover': {
                                        backgroundColor: 'rgba(255,255,255,0.08)',
                                    }
                                }}
                            >
                                <ListItemIcon sx={{ color: location.pathname === item.path ? '#0d9488' : '#9ca3af', minWidth: 36 }}>
                                    {item.badge ? (
                                        <Badge badgeContent={item.badge} color={item.badgeColor || "primary"} sx={{ '& .MuiBadge-badge': { right: -3, top: 3 } }}>
                                            {item.icon}
                                        </Badge>
                                    ) : item.icon}
                                </ListItemIcon>
                                <ListItemText
                                    primary={item.text}
                                    primaryTypographyProps={{
                                        variant: 'body2',
                                        fontWeight: location.pathname === item.path ? 600 : 400,
                                        color: location.pathname === item.path ? '#fff' : '#d1d5db'
                                    }}
                                />
                            </ListItem>
                        ))}
                    </Box>
                ))}
            </List>

            <Box sx={{ p: 2, borderTop: '1px solid rgba(255,255,255,0.1)' }}>
                <Button
                    fullWidth
                    color="error"
                    variant="text"
                    startIcon={<WarningAmberIcon />}
                    sx={{ justifyContent: 'flex-start', color: '#ef4444', fontWeight: 'bold' }}
                >
                    Emergency Lookup
                </Button>
            </Box>
        </Drawer>
    );
}
