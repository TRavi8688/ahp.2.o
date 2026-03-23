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
                body: JSON.stringify({ 
                    identifier, 
                    method: identifier.includes('@') ? 'email' : 'sms' 
                })
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
        <Box sx={{ minHeight: '100vh', display: 'flex', background: 'linear-gradient(135deg, #050810, #1E1B4B)' }}>
            <Grid container>
                {/* Branding Side */}
                <Grid item xs={12} md={6} sx={{
                    background: 'transparent',
                    color: 'white',
                    display: 'flex',
                    flexDirection: 'column',
                    p: 6,
                    justifyContent: 'center',
                    position: 'relative'
                }}>
                    <Box sx={{ display: 'flex', alignItems: 'center', mb: 3 }}>
                        <Box sx={{ width: 64, height: 64, mr: 2, borderRadius: '32px', overflow: 'hidden', border: '2px solid rgba(99, 102, 241, 0.4)', boxShadow: '0 0 15px rgba(99, 102, 241, 0.2)' }}>
                            <img src="/logo.png" alt="Logo" style={{ width: '100%', height: '100%', objectFit: 'cover' }} />
                        </Box>
                        <Typography variant="h3" fontWeight="bold" letterSpacing="-1px">Mulajna <span style={{ color: '#6366F1' }}>Terminal</span></Typography>
                    </Box>
                    <Typography variant="h5" sx={{ fontWeight: 300, color: '#94a3b8', maxWidth: 400 }}>
                        Professional healthcare interface for secure patient data access.
                    </Typography>

                    <Box sx={{ mt: 10, display: 'flex', gap: 3 }}>
                        <Box sx={{ p: 3, bgcolor: 'rgba(255,255,255,0.05)', borderRadius: 2, flex: 1 }}>
                            <Typography variant="subtitle2" sx={{ color: '#6366F1', fontWeight: 'bold' }}>SECURE CHANNEL</Typography>
                            <Typography variant="body2" color="#94a3b8">Dual-factor authentication via encrypted SMS or Email.</Typography>
                        </Box>
                        <Box sx={{ p: 3, bgcolor: 'rgba(255,255,255,0.05)', borderRadius: 2, flex: 1 }}>
                            <Typography variant="subtitle2" sx={{ color: '#6366F1', fontWeight: 'bold' }}>AI VERIFIED</Typography>
                            <Typography variant="body2" color="#94a3b8">Real-time medical license analysis and registry check.</Typography>
                        </Box>
                    </Box>
                </Grid>

                {/* Login Form Side */}
                <Grid item xs={12} md={6} sx={{ display: 'flex', alignItems: 'center', justifyContent: 'center', p: 4 }}>
                    <Container maxWidth="xs">
                        <Paper elevation={20} sx={{ p: 5, borderRadius: 4, background: 'rgba(15, 23, 42, 0.6)', backdropFilter: 'blur(10px)', border: '1px solid rgba(255, 255, 255, 0.05)', color: 'white' }}>
                            <Typography variant="h4" fontWeight="bold" sx={{ mb: 1, color: '#FFFFFF' }}>Doctor Login</Typography>
                            <Typography variant="body2" sx={{ mb: 4, color: '#94a3b8' }}>
                                Access your clinical dashboard securely.
                            </Typography>

                            <Tabs
                                value={loginMode}
                                onChange={(e, val) => { setLoginMode(val); setOtpSent(false); setErrorMsg(''); }}
                                variant="fullWidth"
                                sx={{ 
                                    mb: 4, 
                                    bgcolor: 'rgba(0, 0, 0, 0.3)', 
                                    borderRadius: 2, 
                                    p: 0.5, 
                                    '& .MuiTabs-indicator': { height: '100%', borderRadius: 1.5, zIndex: 0, bgcolor: '#6366F1', boxShadow: '0 2px 4px rgba(0,0,0,0.2)' },
                                    '& .MuiTab-root': { color: '#94A3B8' },
                                    '& .Mui-selected': { color: '#FFFFFF !important' }
                                }}
                            >
                                <Tab label="OTP Login" value="otp" sx={{ zIndex: 1, fontWeight: 'bold', textTransform: 'none' }} />
                                <Tab label="Password" value="password" sx={{ zIndex: 1, fontWeight: 'bold', textTransform: 'none' }} />
                            </Tabs>

                            <form onSubmit={handleLogin}>
                                {errorMsg && <Alert severity="error" sx={{ mb: 3, borderRadius: 2 }}>{errorMsg}</Alert>}
                                {successMsg && <Alert severity="success" sx={{ mb: 3, borderRadius: 2, bgcolor: 'rgba(34, 197, 94, 0.1)', color: '#4ade80' }}>{successMsg}</Alert>}

                                <TextField
                                    fullWidth
                                    label="Registration Email or Phone"
                                    variant="outlined"
                                    sx={{ 
                                        mb: 3,
                                        '& .MuiOutlinedInput-root': { color: 'white', bgcolor: 'rgba(0,0,0,0.3)', borderRadius: 2, '& fieldset': { borderColor: 'rgba(255,255,255,0.1)' }, '&:hover fieldset': { borderColor: '#6366F1' }, '&.Mui-focused fieldset': { borderColor: '#6366F1' } },
                                        '& .MuiInputLabel-root': { color: '#94a3b8' },
                                        '& .MuiInputLabel-root.Mui-focused': { color: '#6366F1' },
                                    }}
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
                                                <Typography variant="caption" fontWeight="bold" sx={{ mb: 1, display: 'block', color: '#94A3B8' }}>CHOOSE VERIFICATION CHANNEL</Typography>
                                                <RadioGroup row value={otpChannel} onChange={(e) => setOtpChannel(e.target.value)} sx={{ color: 'white' }}>
                                                    <FormControlLabel
                                                        value="sms"
                                                        control={<Radio size="small" sx={{ color: '#94A3B8', '&.Mui-checked': { color: '#6366F1' } }} />}
                                                        label={<Typography variant="body2">Secure SMS</Typography>}
                                                    />
                                                    <FormControlLabel
                                                        value="email"
                                                        control={<Radio size="small" sx={{ color: '#94A3B8', '&.Mui-checked': { color: '#6366F1' } }} />}
                                                        label={<Typography variant="body2">Professional Email</Typography>}
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
                                                sx={{ 
                                                    mb: 3,
                                                    '& .MuiOutlinedInput-root': { color: 'white', bgcolor: 'rgba(0,0,0,0.3)', borderRadius: 2, '& fieldset': { borderColor: 'rgba(255,255,255,0.1)' }, '&:hover fieldset': { borderColor: '#6366F1' }, '&.Mui-focused fieldset': { borderColor: '#6366F1' } },
                                                    '& .MuiInputLabel-root': { color: '#94a3b8' },
                                                    '& .MuiInputLabel-root.Mui-focused': { color: '#6366F1' },
                                                    '& .MuiFormHelperText-root': { color: '#94A3B8' }
                                                }}
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
                                        sx={{ 
                                            mb: 3,
                                            '& .MuiOutlinedInput-root': { color: 'white', bgcolor: 'rgba(0,0,0,0.3)', borderRadius: 2, '& fieldset': { borderColor: 'rgba(255,255,255,0.1)' }, '&:hover fieldset': { borderColor: '#6366F1' }, '&.Mui-focused fieldset': { borderColor: '#6366F1' } },
                                            '& .MuiInputLabel-root': { color: '#94a3b8' },
                                            '& .MuiInputLabel-root.Mui-focused': { color: '#6366F1' },
                                        }}
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
                                    sx={{ py: 1.8, borderRadius: 2, fontWeight: 'bold', bgcolor: '#6366F1', '&:hover': { bgcolor: '#4F46E5' } }}
                                >
                                    {isLoading ? 'Processing...' : 'Secure Authorization'}
                                </Button>

                                <Box sx={{ mt: 4, textAlign: 'center' }}>
                                    <Typography variant="body2" sx={{ color: '#94a3b8' }}>
                                        Don't have a professional account?
                                    </Typography>
                                    <Button
                                        sx={{ fontWeight: 'bold', mt: 1, color: '#6366F1' }}
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
