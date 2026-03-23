import React from 'react';
import { Typography, Grid, Card, CardContent, Divider, Box, Button, Chip, Avatar, IconButton } from '@mui/material';
import { useNavigate } from 'react-router-dom';

// Icons
import EventIcon from '@mui/icons-material/Event';
import PeopleIcon from '@mui/icons-material/People';
import MedicationIcon from '@mui/icons-material/Medication';
import WarningAmberIcon from '@mui/icons-material/WarningAmber';
import QrCodeScannerIcon from '@mui/icons-material/QrCodeScanner';
import LocalHospitalIcon from '@mui/icons-material/LocalHospital';
import FolderSharedIcon from '@mui/icons-material/FolderShared';
import ArrowForwardIosIcon from '@mui/icons-material/ArrowForwardIos';
import { API_BASE_URL } from '../api';

export default function HomeDashboard({ onOpenScan }) {
    const navigate = useNavigate();
    const [patients, setPatients] = React.useState([]);
    const [profile, setProfile] = React.useState(null);
    const [stats, setStats] = React.useState({
        patients_count: 0,
        schedule_count: 0,
        alerts_count: 0,
        pending_rx_count: 0
    });
    const [isLoading, setIsLoading] = React.useState(true);

    React.useEffect(() => {
        const fetchData = async () => {
            const token = localStorage.getItem('token');
            if (!token) return;

            try {
                // Fetch Patients
                const patientsRes = await fetch(`${API_BASE_URL}/doctor/my-patients`, {
                    headers: { 'Authorization': `Bearer ${token}` }
                });
                if (patientsRes.ok) setPatients(await patientsRes.json());

                // Fetch Profile
                const profileRes = await fetch(`${API_BASE_URL}/doctor/profile/me`, {
                    headers: { 'Authorization': `Bearer ${token}` }
                });
                if (profileRes.ok) setProfile(await profileRes.json());

                // Fetch Stats
                const statsRes = await fetch(`${API_BASE_URL}/doctor/stats`, {
                    headers: { 'Authorization': `Bearer ${token}` }
                });
                if (statsRes.ok) setStats(await statsRes.json());

            } catch (error) {
                console.error("Dashboard fetch error:", error);
            } finally {
                setIsLoading(false);
            }
        };
        fetchData();
    }, []);

    // Derived Stats
    const appointmentsToday = stats.schedule_count;
    const pendingPrescriptions = stats.pending_rx_count;
    const urgentAlertsCount = stats.alerts_count;

    return (
        <Box sx={{ maxWidth: 1400, mx: 'auto' }}>
            {/* Header */}
            <Box sx={{ mb: 4 }}>
                <Typography variant="h4" fontWeight="bold" sx={{ color: '#fff' }}>
                    Good afternoon, {profile ? `Dr. ${profile.last_name}` : 'Doctor'}
                </Typography>
                <Typography variant="body1" sx={{ color: 'rgba(255,255,255,0.7)', mt: 0.5 }}>
                    You have {appointmentsToday} consultations scheduled for today · {pendingPrescriptions} pending prescriptions · {urgentAlertsCount} urgent alerts.
                </Typography>
            </Box>

            {/* Stats Row (4 cards) */}
            <Grid container spacing={3} sx={{ mb: 4 }}>
                {/* Card 1 - Appointments */}
                <Grid item xs={12} sm={6} md={3}>
                    <StatCard
                        title="Today's Appointments"
                        value={appointmentsToday}
                        change={appointmentsToday === 0 ? "No visits yet" : "▲ from yesterday"}
                        color="#0d9488" // Teal
                        icon={<EventIcon fontSize="large" sx={{ opacity: 0.2, color: '#0d9488' }} />}
                    />
                </Grid>
                {/* Card 2 - Active Patients */}
                <Grid item xs={12} sm={6} md={3}>
                    <StatCard
                        title="My Active Patients"
                        value={stats.patients_count}
                        change="+ on record"
                        color="#3b82f6" // Blue
                        icon={<PeopleIcon fontSize="large" sx={{ opacity: 0.2, color: '#3b82f6' }} />}
                    />
                </Grid>
                {/* Card 3 - Pending Prescriptions */}
                <Grid item xs={12} sm={6} md={3}>
                    <StatCard
                        title="Pending Prescriptions"
                        value={pendingPrescriptions}
                        change={pendingPrescriptions === 0 ? "Up to date" : "Needs review"}
                        color="#f59e0b" // Amber
                        icon={<MedicationIcon fontSize="large" sx={{ opacity: 0.2, color: '#f59e0b' }} />}
                    />
                </Grid>
                {/* Card 4 - Urgent Alerts */}
                <Grid item xs={12} sm={6} md={3}>
                    <StatCard
                        title="Urgent Alerts"
                        value={urgentAlertsCount}
                        change={urgentAlertsCount === 0 ? "All clear ✓" : "Requires attention"}
                        color={urgentAlertsCount === 0 ? "#10b981" : "#ef4444"} // Green or Red
                        icon={<WarningAmberIcon fontSize="large" sx={{ opacity: 0.2, color: urgentAlertsCount === 0 ? '#10b981' : '#ef4444' }} />}
                    />
                </Grid>
            </Grid>

            {/* Two-column section */}
            <Grid container spacing={3} sx={{ mb: 4 }}>
                {/* Left Column: Today's Appointments */}
                <Grid item xs={12} md={7} lg={8}>
                    <Card elevation={0} sx={{ border: '1px solid #e5e7eb', height: '100%', borderRadius: 2 }}>
                        <Box sx={{ p: 2.5, display: 'flex', justifyContent: 'space-between', alignItems: 'center', borderBottom: '1px solid #e5e7eb' }}>
                            <Typography variant="h6" fontWeight="bold" sx={{ color: '#1f2937' }}>Recent Consultations</Typography>
                            <Button
                                endIcon={<ArrowForwardIosIcon sx={{ fontSize: 12 }} />}
                                onClick={() => navigate('/patients')}
                                sx={{ textTransform: 'none', fontWeight: 600 }}
                            >
                                View all
                            </Button>
                        </Box>
                        <Box>
                            {isLoading ? (
                                <Box sx={{ p: 4, textAlign: 'center' }}>
                                    <Typography color="text.secondary">Loading patients...</Typography>
                                </Box>
                            ) : patients.length === 0 ? (
                                <Box sx={{ p: 4, textAlign: 'center' }}>
                                    <Typography color="text.secondary">No active patient consultations found.</Typography>
                                </Box>
                            ) : (
                                patients.slice(0, 5).map((p) => (
                                    <AppointmentRow
                                        key={p.ahp_id}
                                        name={p.name}
                                        time={new Date(p.granted_at).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })}
                                        status={p.access_level === 'full' ? 'Active' : 'Restricted'}
                                        statusColor="success"
                                        id={p.ahp_id}
                                        condition="AHP Patient"
                                    />
                                ))
                            )}
                        </Box>
                    </Card>
                </Grid>

                {/* Right Column: Quick Actions & Stats */}
                <Grid item xs={12} md={5} lg={4}>
                    {/* Quick Actions Card */}
                    <Card elevation={0} sx={{ border: '1px solid #e5e7eb', mb: 3, borderRadius: 2 }}>
                        <Box sx={{ p: 2.5, borderBottom: '1px solid #e5e7eb' }}>
                            <Typography variant="h6" fontWeight="bold" sx={{ color: '#1f2937' }}>Quick Actions</Typography>
                        </Box>
                        <Box sx={{ p: 2 }}>
                            <Grid container spacing={1.5}>
                                <Grid item xs={6}>
                                    <QuickActionButton
                                        label="Scan QR"
                                        icon={<QrCodeScannerIcon />}
                                        onClick={onOpenScan}
                                        color="#0d9488"
                                    />
                                </Grid>
                                <Grid item xs={6}>
                                    <QuickActionButton
                                        label="Write Rx"
                                        icon={<MedicationIcon />}
                                        onClick={() => navigate('/prescriptions')}
                                        color="#3b82f6"
                                    />
                                </Grid>
                                <Grid item xs={6}>
                                    <QuickActionButton
                                        label="Emergency"
                                        icon={<LocalHospitalIcon />}
                                        onClick={() => { }} // TODO: implement emergency lookup
                                        color="#ef4444"
                                    />
                                </Grid>
                                <Grid item xs={6}>
                                    <QuickActionButton
                                        label="Records"
                                        icon={<FolderSharedIcon />}
                                        onClick={() => navigate('/history')}
                                        color="#6366f1"
                                    />
                                </Grid>
                            </Grid>
                        </Box>
                    </Card>

                    {/* Today's Patient Stats Card */}
                    <Card elevation={0} sx={{ border: '1px solid #e5e7eb', borderRadius: 2 }}>
                        <Box sx={{ p: 2.5, borderBottom: '1px solid #e5e7eb' }}>
                            <Typography variant="h6" fontWeight="bold" sx={{ color: '#1f2937' }}>Today's Stats</Typography>
                        </Box>
                        <Box sx={{ p: 2 }}>
                            <Grid container rowSpacing={2} columnSpacing={1}>
                                <Grid item xs={6}>
                                    <MiniStat label="Patients Seen" value={stats.patients_count} />
                                </Grid>
                                <Grid item xs={6}>
                                    <MiniStat label="Allergy Flags" value={stats.alerts_count} color={stats.alerts_count > 0 ? "#ef4444" : "#111827"} />
                                </Grid>
                                <Grid item xs={6}>
                                    <MiniStat label="Rx Sent" value={stats.pending_rx_count} />
                                </Grid>
                                <Grid item xs={6}>
                                    <MiniStat label="Next Visit" value="Pending" />
                                </Grid>
                            </Grid>
                        </Box>
                    </Card>
                </Grid>
            </Grid>

            {/* Urgent Alert Panel (Full Width) */}
            {urgentAlertsCount > 0 && (
                <Card elevation={0} sx={{ border: '1px solid #fca5a5', bgcolor: '#fef2f2', borderRadius: 2 }}>
                    <Box sx={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', p: 3, flexWrap: 'wrap', gap: 2 }}>
                        <Box sx={{ display: 'flex', gap: 2, alignItems: 'center', flex: 1, minWidth: 300 }}>
                            <Box sx={{ p: 1, bgcolor: '#fee2e2', borderRadius: '50%', display: 'flex' }}>
                                <WarningAmberIcon sx={{ color: '#dc2626', fontSize: 32 }} />
                            </Box>
                            <Box>
                                <Typography variant="h6" fontWeight="bold" sx={{ color: '#b91c1c' }}>
                                    Drug Interaction Alert — Rahul Sharma
                                </Typography>
                                <Typography variant="body2" sx={{ color: '#7f1d1d', mt: 0.5 }}>
                                    New prescription includes Amoxicillin. Patient's AHP profile shows a Severe allergy to Penicillin. This requires immediate review.
                                </Typography>
                            </Box>
                        </Box>
                        <Box sx={{ display: 'flex', gap: 1.5 }}>
                            <Button variant="outlined" color="error" sx={{ bgcolor: 'white' }}>
                                Flag & Hold
                            </Button>
                            <Button variant="contained" color="error" onClick={() => navigate('/patient/AHP-IN-9284-7731')}>
                                View Patient
                            </Button>
                        </Box>
                    </Box>
                </Card>
            )}
        </Box>
    );
}

// Subcomponents

const StatCard = ({ title, value, change, color, icon }) => (
    <Card
        className="glass-card"
        elevation={0}
        sx={{
            height: '100%',
            position: 'relative',
            overflow: 'hidden',
            transition: 'all 0.3s cubic-bezier(0.16, 1, 0.3, 1)',
            '&:hover': {
                transform: 'translateY(-5px)',
                boxShadow: `0 12px 40px 0 rgba(0, 0, 0, 0.2), 0 0 20px rgba(13, 148, 136, 0.2)`,
                borderColor: 'rgba(255, 255, 255, 0.5)',
            }
        }}
    >
        <Box sx={{ position: 'absolute', top: 16, right: 16 }}>
            {icon}
        </Box>
        <CardContent sx={{ p: 3 }}>
            <Typography variant="h4" fontWeight="bold" sx={{ color: '#1e293b', mb: 1, fontFamily: 'Outfit' }}>{value}</Typography>
            <Typography variant="body2" fontWeight="600" sx={{ color: '#64748b', mb: 1 }}>{title}</Typography>
            <Typography variant="caption" sx={{ color: color, fontWeight: '900', letterSpacing: 0.5 }}>{change}</Typography>
        </CardContent>
    </Card>
);

const AppointmentRow = ({ name, time, status, statusColor, id, condition }) => {
    const navigate = useNavigate();

    // Convert status to a color dot
    const getStatusColor = (color) => {
        switch (color) {
            case 'error': return '#ef4444';
            case 'warning': return '#f59e0b';
            case 'success': return '#10b981';
            default: return '#6b7280';
        }
    };

    return (
        <Box
            sx={{
                p: 2.5,
                borderBottom: '1px solid #e5e7eb',
                display: 'flex',
                alignItems: 'center',
                justifyContent: 'space-between',
                transition: 'background-color 0.2s',
                '&:hover': { bgcolor: '#f9fafb', cursor: 'pointer' },
                '&:last-child': { borderBottom: 'none' }
            }}
            onClick={() => navigate(`/patient/${id}`)}
        >
            <Box sx={{ display: 'flex', alignItems: 'center', gap: 2 }}>
                <Box sx={{ width: 12, display: 'flex', justifyContent: 'center' }}>
                    <Box sx={{ width: 10, height: 10, borderRadius: '50%', bgcolor: getStatusColor(statusColor) }} />
                </Box>
                <Avatar sx={{ bgcolor: '#dbeafe', color: '#1e40af', fontWeight: 'bold' }}>{name.charAt(0)}</Avatar>
                <Box>
                    <Typography variant="subtitle2" fontWeight="bold" sx={{ color: '#111827' }}>{name}</Typography>
                    <Typography variant="caption" sx={{ color: '#6b7280' }}>{condition} · <span style={{ fontFamily: 'monospace' }}>{id}</span></Typography>
                </Box>
            </Box>
            <Box sx={{ textAlign: 'right' }}>
                <Typography variant="subtitle2" fontWeight="bold" sx={{ color: '#1f2937' }}>{time}</Typography>
                <Chip size="small" label={status} color={statusColor} sx={{ height: 20, fontSize: '0.7rem', mt: 0.5, fontWeight: 'bold' }} />
            </Box>
        </Box>
    );
};

const QuickActionButton = ({ label, icon, onClick, color }) => (
    <Button
        fullWidth
        className="glass-card"
        variant="outlined"
        onClick={onClick}
        sx={{
            display: 'flex',
            flexDirection: 'column',
            py: 2,
            border: 'none',
            color: '#1e293b',
            background: 'rgba(255, 255, 255, 0.4)',
            transition: 'all 0.2s',
            '&:hover': {
                background: 'rgba(255, 255, 255, 0.8)',
                transform: 'scale(1.02)',
                boxShadow: `0 4px 12px rgba(0,0,0,0.1)`
            }
        }}
    >
        <Box sx={{ color: color, mb: 1, display: 'flex' }}>
            {icon}
        </Box>
        <Typography variant="caption" fontWeight="900" sx={{ textTransform: 'none', letterSpacing: 0.5 }}>{label}</Typography>
    </Button>
);

const MiniStat = ({ label, value, color = '#111827' }) => (
    <Box>
        <Typography variant="h5" fontWeight="bold" sx={{ color: color }}>{value}</Typography>
        <Typography variant="caption" sx={{ color: '#6b7280', fontWeight: 600 }}>{label}</Typography>
    </Box>
);
