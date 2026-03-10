import React, { useState } from 'react';
import { Container, Typography, TextField, Button, Box, Paper, Grid, Divider, Select, MenuItem, FormControl, InputLabel, Alert, Tabs, Tab, RadioGroup, FormControlLabel, Radio, CircularProgress } from '@mui/material';
import { useNavigate } from 'react-router-dom';
import { useTranslation } from 'react-i18next';
import SmartphoneIcon from '@mui/icons-material/Smartphone';
import EmailIcon from '@mui/icons-material/Email';
import LockIcon from '@mui/icons-material/Lock';
import { API_BASE_URL } from '../api';

export default function LoginScreen() {
    const { t, i18n } = useTranslation();
    const navigate = useNavigate();

    const [loginMode, setLoginMode] = useState('otp'); // 'otp' | 'password'
    const [identifier, setIdentifier] = useState('');
    const [passwordOrOtp, setPasswordOrOtp] = useState('');
    const [otpChannel, setOtpChannel] = useState('sms'); // 'sms' | 'email'
    const [otpSent, setOtpSent] = useState(false);

    const [isLoading, setIsLoading] = useState(false);
    const [errorMsg, setErrorMsg] = useState('');
    const [successMsg, setSuccessMsg] = useState('');

    const handleSendOTP = async () => {
        setIsLoading(true);
        setErrorMsg('');
        setSuccessMsg('');
        try {
            const response = await fetch(`${API_BASE_URL}/doctor/send-otp`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ identifier, channel: otpChannel })
            });
            const data = await response.json();
            if (!response.ok) throw new Error(data.detail || 'Failed to send OTP');
            setOtpSent(true);
            setSuccessMsg(`OTP sent to your ${otpChannel === 'sms' ? 'phone' : 'email'}.`);
        } catch (error) {
            setErrorMsg(error.message);
        } finally {
            setIsLoading(false);
        }
    };

    const handleLogin = async (e) => {
        e.preventDefault();
        setIsLoading(true);
        setErrorMsg('');

        try {
            const formData = new URLSearchParams();
            formData.append('identifier', identifier);
            formData.append('password_or_otp', passwordOrOtp);
            formData.append('is_otp', loginMode === 'otp' ? 'true' : 'false');

            const response = await fetch(`${API_BASE_URL}/doctor/token`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/x-www-form-urlencoded' },
                body: formData.toString()
            });

            const data = await response.json();

            if (!response.ok) {
                const errorDetail = typeof data.detail === 'string'
                    ? data.detail
                    : (Array.isArray(data.detail) ? data.detail.map(e => e.msg).join(', ') : JSON.stringify(data.detail));
                throw new Error(errorDetail || 'Login failed.');
            }

            localStorage.setItem('isAuthenticated', 'true');
            localStorage.setItem('token', data.access_token);
            window.location.href = '/';
        } catch (error) {
            setErrorMsg(error.message);
        } finally {
            setIsLoading(false);
        }
    };

    return (
        <Box sx={{ minHeight: '100vh', display: 'flex', bgcolor: '#f8fafc' }}>
            <Grid container>
                {/* Branding Side */}
                <Grid item xs={12} md={6} sx={{
                    bgcolor: '#0f172a',
                    color: 'white',
                    display: 'flex',
                    flexDirection: 'column',
                    p: 6,
                    justifyContent: 'center',
                    position: 'relative'
                }}>
                    <Box sx={{ display: 'flex', alignItems: 'center', mb: 3 }}>
                        <Box sx={{ width: 60, height: 60, bgcolor: '#38bdf8', borderRadius: 2, mr: 2, display: 'flex', alignItems: 'center', justifyContent: 'center' }}>
                            <img src="/logo.png" alt="Logo" style={{ width: '80%' }} />
                        </Box>
                        <Typography variant="h3" fontWeight="bold" letterSpacing="-1px">Nirixa <span style={{ color: '#38bdf8' }}>Terminal</span></Typography>
                    </Box>
                    <Typography variant="h5" sx={{ fontWeight: 300, color: '#94a3b8', maxWidth: 400 }}>
                        Professional healthcare interface for secure patient data access.
                    </Typography>

                    <Box sx={{ mt: 10, display: 'flex', gap: 3 }}>
                        <Box sx={{ p: 3, bgcolor: 'rgba(255,255,255,0.05)', borderRadius: 2, flex: 1 }}>
                            <Typography variant="subtitle2" color="#38bdf8" fontWeight="bold">SECURE CHANNEL</Typography>
                            <Typography variant="body2" color="#94a3b8">Dual-factor authentication via encrypted SMS or Email.</Typography>
                        </Box>
                        <Box sx={{ p: 3, bgcolor: 'rgba(255,255,255,0.05)', borderRadius: 2, flex: 1 }}>
                            <Typography variant="subtitle2" color="#38bdf8" fontWeight="bold">AI VERIFIED</Typography>
                            <Typography variant="body2" color="#94a3b8">Real-time medical license analysis and registry check.</Typography>
                        </Box>
                    </Box>
                </Grid>

                {/* Login Form Side */}
                <Grid item xs={12} md={6} sx={{ display: 'flex', alignItems: 'center', justifyContent: 'center', p: 4 }}>
                    <Container maxWidth="xs">
                        <Paper elevation={0} sx={{ p: 5, borderRadius: 4, border: '1px solid #e2e8f0' }}>
                            <Typography variant="h4" fontWeight="bold" sx={{ mb: 1, color: '#1e293b' }}>Doctor Login</Typography>
                            <Typography variant="body2" color="text.secondary" sx={{ mb: 4 }}>
                                Access your clinical dashboard securely.
                            </Typography>

                            <Tabs
                                value={loginMode}
                                onChange={(e, val) => { setLoginMode(val); setOtpSent(false); setErrorMsg(''); }}
                                variant="fullWidth"
                                sx={{ mb: 4, bgcolor: '#f1f5f9', borderRadius: 2, p: 0.5, '& .MuiTabs-indicator': { height: '100%', borderRadius: 1.5, zIndex: 0, bgcolor: 'white', boxShadow: '0 2px 4px rgba(0,0,0,0.05)' } }}
                            >
                                <Tab label="OTP Login" value="otp" sx={{ zIndex: 1, fontWeight: 'bold', textTransform: 'none' }} />
                                <Tab label="Password" value="password" sx={{ zIndex: 1, fontWeight: 'bold', textTransform: 'none' }} />
                            </Tabs>

                            <form onSubmit={handleLogin}>
                                {errorMsg && <Alert severity="error" sx={{ mb: 3, borderRadius: 2 }}>{errorMsg}</Alert>}
                                {successMsg && <Alert severity="success" sx={{ mb: 3, borderRadius: 2 }}>{successMsg}</Alert>}

                                <TextField
                                    fullWidth
                                    label="Registration Email or Phone"
                                    variant="outlined"
                                    sx={{ mb: 3 }}
                                    required
                                    value={identifier}
                                    onChange={(e) => setIdentifier(e.target.value)}
                                    InputProps={{
                                        startAdornment: identifier.includes('@') ? <EmailIcon sx={{ mr: 1, color: '#94a3b8' }} /> : <SmartphoneIcon sx={{ mr: 1, color: '#94a3b8' }} />
                                    }}
                                />

                                {loginMode === 'otp' ? (
                                    <>
                                        {!otpSent ? (
                                            <Box sx={{ mb: 3 }}>
                                                <Typography variant="caption" fontWeight="bold" color="text.secondary" sx={{ mb: 1, display: 'block' }}>CHOOSE VERIFICATION CHANNEL</Typography>
                                                <RadioGroup row value={otpChannel} onChange={(e) => setOtpChannel(e.target.value)}>
                                                    <FormControlLabel
                                                        value="sms"
                                                        control={<Radio size="small" />}
                                                        label={<Typography variant="body2">SMS (Twilio)</Typography>}
                                                    />
                                                    <FormControlLabel
                                                        value="email"
                                                        control={<Radio size="small" />}
                                                        label={<Typography variant="body2">Email (Gmail Corp)</Typography>}
                                                    />
                                                </RadioGroup>
                                                <Button
                                                    fullWidth
                                                    variant="outlined"
                                                    size="large"
                                                    onClick={handleSendOTP}
                                                    disabled={isLoading || !identifier}
                                                    sx={{ mt: 2, py: 1.5, borderRadius: 2, fontWeight: 'bold' }}
                                                >
                                                    {isLoading ? <CircularProgress size={24} /> : 'Get Verification Code'}
                                                </Button>
                                            </Box>
                                        ) : (
                                            <TextField
                                                fullWidth
                                                label="6-Digit OTP"
                                                variant="outlined"
                                                sx={{ mb: 3 }}
                                                required
                                                autoFocus
                                                value={passwordOrOtp}
                                                onChange={(e) => setPasswordOrOtp(e.target.value)}
                                                helperText="Enter the code sent to your device."
                                            />
                                        )}
                                    </>
                                ) : (
                                    <TextField
                                        fullWidth
                                        label="Secure Password"
                                        type="password"
                                        variant="outlined"
                                        sx={{ mb: 3 }}
                                        required
                                        value={passwordOrOtp}
                                        onChange={(e) => setPasswordOrOtp(e.target.value)}
                                        InputProps={{
                                            startAdornment: <LockIcon sx={{ mr: 1, color: '#94a3b8' }} />
                                        }}
                                    />
                                )}

                                <Button
                                    type="submit"
                                    fullWidth
                                    variant="contained"
                                    size="large"
                                    disabled={isLoading || (loginMode === 'otp' && !otpSent)}
                                    sx={{ py: 1.8, borderRadius: 2, fontWeight: 'bold', bgcolor: '#0f172a', '&:hover': { bgcolor: '#1e293b' } }}
                                >
                                    {isLoading ? 'Processing...' : 'Secure Authorization'}
                                </Button>

                                <Box sx={{ mt: 4, textAlign: 'center' }}>
                                    <Typography variant="body2" color="text.secondary">
                                        Don't have a professional account?
                                    </Typography>
                                    <Button
                                        color="primary"
                                        sx={{ fontWeight: 'bold', mt: 1 }}
                                        onClick={() => navigate('/verify')}
                                    >
                                        Start Practitioner Registration
                                    </Button>
                                </Box>
                            </form>
                        </Paper>
                    </Container>
                </Grid>
            </Grid>
        </Box>
    );
}
