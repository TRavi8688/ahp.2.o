import React from 'react';
import { Box, Typography, Button, IconButton, Grid, Card } from '@mui/material';
import { useNavigate } from 'react-router-dom';

import ArrowBackIosNewIcon from '@mui/icons-material/ArrowBackIosNew';
import ArrowForwardIosIcon from '@mui/icons-material/ArrowForwardIos';
import AddIcon from '@mui/icons-material/Add';
import WatchLaterIcon from '@mui/icons-material/WatchLater';

export default function Schedule() {
    const navigate = useNavigate();

    // Dynamic weekly structure
    const today = new Date();
    const days = ['MON', 'TUE', 'WED', 'THU', 'FRI'].map((dayName, idx) => {
        const d = new Date(today);
        const dayOffset = idx - ((today.getDay() + 6) % 7); // Calculate diff from Monday
        d.setDate(today.getDate() + dayOffset);
        return {
            day: dayName,
            date: d.getDate().toString(),
            isToday: d.toDateString() === today.toDateString()
        };
    });

    const appointments = {
        'MON': [],
        'TUE': [],
        'WED': [],
        'THU': [],
        'FRI': []
    };

    const getColorHex = (color) => {
        switch (color) {
            case 'teal': return '#0d9488';
            case 'red': return '#ef4444';
            case 'amber': return '#f59e0b';
            case 'purple': return '#8b5cf6';
            default: return '#e5e7eb';
        }
    };

    const getBgHex = (color) => {
        switch (color) {
            case 'teal': return '#f0fdfa';
            case 'red': return '#fef2f2';
            case 'amber': return '#fffbeb';
            case 'purple': return '#f5f3ff';
            default: return '#f9fafb';
        }
    };

    return (
        <Box sx={{ maxWidth: 1400, mx: 'auto', height: 'calc(100vh - 120px)', display: 'flex', flexDirection: 'column' }}>

            {/* Header */}
            <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', mb: 3 }}>
                <Typography variant="h5" fontWeight="bold" sx={{ color: '#1f2937' }}>
                    Schedule
                </Typography>

                <Box sx={{ display: 'flex', alignItems: 'center', gap: 2 }}>
                    <IconButton size="small" sx={{ border: '1px solid #e5e7eb' }}>
                        <ArrowBackIosNewIcon fontSize="small" />
                    </IconButton>
                    <Typography variant="subtitle1" fontWeight="bold" sx={{ color: '#374151', minWidth: 150, textAlign: 'center' }}>
                        Week of Oct 14 - 18
                    </Typography>
                    <IconButton size="small" sx={{ border: '1px solid #e5e7eb' }}>
                        <ArrowForwardIosIcon fontSize="small" />
                    </IconButton>
                </Box>

                <Button variant="contained" startIcon={<AddIcon />} sx={{ bgcolor: '#0d9488', '&:hover': { bgcolor: '#0f766e' }, textTransform: 'none', fontWeight: 'bold' }}>
                    Add Appointment
                </Button>
            </Box>

            {/* Calendar Grid */}
            <Card elevation={0} sx={{ flex: 1, border: '1px solid #e5e7eb', borderRadius: 2, display: 'flex', flexDirection: 'column' }}>
                <Grid container sx={{ height: '100%' }}>
                    {days.map((dayObj, index) => (
                        <Grid item xs={12} md={2.4} key={dayObj.day} sx={{ borderRight: index < 4 ? '1px solid #e5e7eb' : 'none', display: 'flex', flexDirection: 'column' }}>

                            {/* Column Header */}
                            <Box sx={{ p: 2, textAlign: 'center', borderBottom: '1px solid #e5e7eb', bgcolor: dayObj.isToday ? '#f0fdfa' : 'white' }}>
                                <Typography variant="caption" sx={{ color: '#9ca3af', fontWeight: 'bold', display: 'block', mb: 0.5 }}>
                                    {dayObj.day}
                                </Typography>
                                <Typography
                                    variant="h4"
                                    sx={{
                                        fontWeight: 'bold',
                                        color: dayObj.isToday ? '#0d9488' : '#1f2937',
                                        width: 48,
                                        height: 48,
                                        lineHeight: '48px',
                                        mx: 'auto',
                                        borderRadius: '50%',
                                        bgcolor: dayObj.isToday ? '#ccfbf1' : 'transparent'
                                    }}
                                >
                                    {dayObj.date}
                                </Typography>
                            </Box>

                            {/* Column Body / Slots */}
                            <Box sx={{ flex: 1, p: 1.5, bgcolor: dayObj.isToday ? '#f8fafc' : '#f9fafb', overflowY: 'auto' }}>
                                {appointments[dayObj.day].map((apt, i) => (
                                    <Box
                                        key={i}
                                        onClick={() => apt.id ? navigate(`/patient/${apt.id}`) : null}
                                        sx={{
                                            p: 1.5,
                                            mb: 1.5,
                                            bgcolor: getBgHex(apt.color),
                                            borderLeft: `4px solid ${getColorHex(apt.color)}`,
                                            borderRadius: 1,
                                            cursor: apt.id ? 'pointer' : 'default',
                                            transition: 'transform 0.1s',
                                            '&:hover': {
                                                transform: apt.id ? 'translateY(-2px)' : 'none',
                                                boxShadow: apt.id ? '0 4px 6px -1px rgba(0,0,0,0.1)' : 'none'
                                            }
                                        }}
                                    >
                                        <Typography variant="subtitle2" fontWeight="bold" sx={{ color: '#111827', mb: 0.5 }}>
                                            {apt.patient || apt.title}
                                        </Typography>
                                        <Box sx={{ display: 'flex', alignItems: 'center', mb: 0.5 }}>
                                            <WatchLaterIcon sx={{ fontSize: 14, color: '#6b7280', mr: 0.5 }} />
                                            <Typography variant="caption" sx={{ color: '#6b7280', fontWeight: 600 }}>
                                                {apt.time}
                                            </Typography>
                                        </Box>
                                        <Typography variant="caption" sx={{ color: getColorHex(apt.color), fontWeight: 'bold' }}>
                                            {apt.type}
                                        </Typography>
                                    </Box>
                                ))}
                            </Box>
                        </Grid>
                    ))}
                </Grid>
            </Card>

        </Box>
    );
}
