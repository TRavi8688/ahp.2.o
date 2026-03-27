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
        <Box sx={{ maxWidth: 1400, mx: 'auto', height: 'calc(100vh - 120px)', display: 'flex', flexDirection: 'column', background: 'transparent' }}>

            {/* Header / Nav Hub */}
            <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', mb: 5 }}>
                <Box>
                    <Typography variant="h3" sx={{ fontWeight: 900, color: '#fff', fontFamily: 'Outfit', letterSpacing: '-1.5px', mb: 1 }}>Clinical Schedule</Typography>
                    <Typography variant="body1" sx={{ color: '#64748b', fontWeight: 600, letterSpacing: 0.5 }}>SYNCHRONIZED PRACTITIONER FLOW</Typography>
                </Box>

                <Box sx={{ display: 'flex', alignItems: 'center', gap: 3, bgcolor: 'rgba(255,255,255,0.02)', p: 1, px: 3, borderRadius: '24px', border: '1px solid rgba(255,255,255,0.05)' }}>
                    <IconButton size="small" sx={{ color: '#fff', '&:hover': { bgcolor: 'rgba(255,255,255,0.05)' } }}>
                        <ArrowBackIosNewIcon fontSize="small" />
                    </IconButton>
                    <Typography variant="subtitle1" sx={{ fontWeight: 800, color: '#fff', minWidth: 160, textAlign: 'center', fontFamily: 'Outfit' }}>
                        OCT 14 — OCT 18
                    </Typography>
                    <IconButton size="small" sx={{ color: '#fff', '&:hover': { bgcolor: 'rgba(255,255,255,0.05)' } }}>
                        <ArrowForwardIosIcon fontSize="small" />
                    </IconButton>
                </Box>

                <Button 
                    variant="contained" 
                    startIcon={<AddIcon />} 
                    sx={{ 
                        bgcolor: '#0d9488', 
                        boxShadow: '0 8px 25px rgba(13, 148, 136, 0.3)',
                        '&:hover': { bgcolor: '#0f766e', transform: 'translateY(-2px)' }, 
                        textTransform: 'none', 
                        fontWeight: 900,
                        borderRadius: '16px',
                        px: 4,
                        py: 1.5,
                        transition: 'all 0.2s'
                    }}
                >
                    Provision Slot
                </Button>
            </Box>

            {/* Calendar Intelligence Grid */}
            <Card className="glass-card" elevation={0} sx={{ 
                flex: 1, 
                border: '1px solid rgba(255,255,255,0.05)', 
                borderRadius: '32px', 
                display: 'flex', 
                flexDirection: 'column',
                bgcolor: 'rgba(255,255,255,0.01)',
                backdropFilter: 'blur(40px)',
                overflow: 'hidden'
            }}>
                <Grid container sx={{ height: '100%' }}>
                    {days.map((dayObj, index) => (
                        <Grid item xs={12} md={2.4} key={dayObj.day} sx={{ 
                            borderRight: index < 4 ? '1px solid rgba(255,255,255,0.03)' : 'none', 
                            display: 'flex', 
                            flexDirection: 'column',
                            transition: 'all 0.3s',
                            '&:hover': { bgcolor: 'rgba(255,255,255,0.01)' }
                        }}>

                            {/* Column Cluster Header */}
                            <Box sx={{ 
                                p: 3, 
                                textAlign: 'center', 
                                borderBottom: '1px solid rgba(255,255,255,0.03)', 
                                bgcolor: dayObj.isToday ? 'rgba(13, 148, 136, 0.05)' : 'transparent',
                                position: 'relative'
                            }}>
                                {dayObj.isToday && (
                                    <Box sx={{ 
                                        position: 'absolute', top: 0, left: 0, right: 0, height: 4, bgcolor: '#0d9488',
                                        boxShadow: '0 0 15px #0d9488'
                                    }} />
                                )}
                                <Typography variant="caption" sx={{ color: dayObj.isToday ? '#0d9488' : '#64748b', fontWeight: 900, display: 'block', mb: 1, letterSpacing: 1.5 }}>
                                    {dayObj.day}
                                </Typography>
                                <Typography
                                    variant="h4"
                                    sx={{
                                        fontWeight: 900,
                                        color: dayObj.isToday ? '#fff' : '#475569',
                                        fontFamily: 'Outfit',
                                        transition: 'all 0.3s'
                                    }}
                                >
                                    {dayObj.date}
                                </Typography>
                            </Box>

                            {/* Column Node Body */}
                            <Box sx={{ flex: 1, p: 2, overflowY: 'auto' }}>
                                {appointments[dayObj.day].map((apt, i) => (
                                    <Box
                                        key={i}
                                        onClick={() => apt.id ? navigate(`/patient/${apt.id}`) : null}
                                        sx={{
                                            p: 2.5,
                                            mb: 2,
                                            bgcolor: 'rgba(255,255,255,0.02)',
                                            border: '1px solid rgba(255,255,255,0.05)',
                                            borderLeft: `4px solid ${getColorHex(apt.color)}`,
                                            borderRadius: '16px',
                                            cursor: apt.id ? 'pointer' : 'default',
                                            transition: 'all 0.2s cubic-bezier(0.16, 1, 0.3, 1)',
                                            '&:hover': {
                                                bgcolor: 'rgba(255,255,255,0.04)',
                                                transform: apt.id ? 'scale(1.02)' : 'none',
                                                boxShadow: '0 10px 20px rgba(0,0,0,0.2)'
                                            }
                                        }}
                                    >
                                        <Typography variant="subtitle2" sx={{ fontWeight: 900, color: '#fff', mb: 1, fontFamily: 'Outfit' }}>
                                            {apt.patient || apt.title}
                                        </Typography>
                                        <Box sx={{ display: 'flex', alignItems: 'center', mb: 1, gap: 1 }}>
                                            <WatchLaterIcon sx={{ fontSize: 14, color: '#64748b' }} />
                                            <Typography variant="caption" sx={{ color: '#64748b', fontWeight: 700, fontFamily: 'monospace' }}>
                                                {apt.time}
                                            </Typography>
                                        </Box>
                                        <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
                                            <Box sx={{ width: 6, height: 6, borderRadius: '50%', bgcolor: getColorHex(apt.color) }} />
                                            <Typography variant="caption" sx={{ color: getColorHex(apt.color), fontWeight: 900, fontSize: '0.65rem', letterSpacing: 0.5 }}>
                                                {apt.type.toUpperCase()}
                                            </Typography>
                                        </Box>
                                    </Box>
                                ))}
                                {appointments[dayObj.day].length === 0 && (
                                    <Box sx={{ py: 4, textAlign: 'center' }}>
                                        <Typography variant="caption" sx={{ color: 'rgba(255,255,255,0.02)', fontWeight: 900, letterSpacing: 2 }}>VAULT EMPTY</Typography>
                                    </Box>
                                )}
                            </Box>
                        </Grid>
                    ))}
                </Grid>
            </Card>

        </Box>
    );
}
