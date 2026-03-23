import React, { useState } from 'react';
import { 
    Container, Typography, TextField, Button, Box, Paper, 
    Grid, Alert, Stepper, Step, StepLabel, LinearProgress, 
    Divider, MenuItem, IconButton, InputAdornment 
} from '@mui/material';
import { useNavigate } from 'react-router-dom';
import CloudUploadIcon from '@mui/icons-material/CloudUpload';
import CheckCircleIcon from '@mui/icons-material/CheckCircle';
import VerifiedUserIcon from '@mui/icons-material/VerifiedUser';
import PhotoCameraIcon from '@mui/icons-material/PhotoCamera';
import Visibility from '@mui/icons-material/Visibility';
import VisibilityOff from '@mui/icons-material/VisibilityOff';
import PersonPinIcon from '@mui/icons-material/PersonPin';
import BadgeIcon from '@mui/icons-material/Badge';
import SecurityIcon from '@mui/icons-material/Security';
import { API_BASE_URL } from '../api';

const STEPS = ['Professional Profile', 'Identity Verification', 'Safety Verification', 'Access Protection'];

const STATE_COUNCILS = [
    "National Medical Commission (NMC)",
    "Andhra Pradesh Medical Council",
    "Delhi Medical Council",
    "Karnataka Medical Council",
    "Maharashtra Medical Council",
    "Tamil Nadu Medical Council",
    "Uttar Pradesh Medical Council",
    "West Bengal Medical Council"
];

export default function SignupScreen() {
    const navigate = useNavigate();
    const [activeStep, setActiveStep] = useState(0);
    const [isLoading, setIsLoading] = useState(false);
    const [errorMsg, setErrorMsg] = useState('');
    const [sessionId, setSessionId] = useState('');
    const [showPassword, setShowPassword] = useState(false);
    const [finalUser, setFinalUser] = useState(null);

    // Form State
    const [formData, setFormData] = useState({
        full_name: '',
        registration_number: '',
        state_medical_council: 'National Medical Commission (NMC)',
        mobile_number: '',
        otp: '',
        password: '',
        confirm_password: ''
    });

    const [files, setFiles] = useState({
        aadhaar: null,
        selfie: null
    });

    const [previews, setPreviews] = useState({
        aadhaar: null,
        selfie: null
    });

    const handleChange = (e) => {
        setFormData({ ...formData, [e.target.name]: e.target.value });
    };

    const handleFileChange = (e, type) => {
        const file = e.target.files[0];
        if (file) {
            setFiles({ ...files, [type]: file });
            const reader = new FileReader();
            reader.onloadend = () => setPreviews({ ...previews, [type]: reader.result });
            reader.readAsDataURL(file);
        }
    };

    // --- Actions ---

    const handleStartVerify = async () => {
        setIsLoading(true);
        setErrorMsg('');
        try {
            const response = await fetch(`${API_BASE_URL}/doctor/verify/start`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({
                    full_name: formData.full_name,
                    registration_number: formData.registration_number,
                    state_medical_council: formData.state_medical_council,
                    mobile_number: formData.mobile_number
                })
            });
            const data = await response.json();
            if (!response.ok) throw new Error(data.detail || 'Basic verification failed');
            
            setSessionId(data.session_id);
            setActiveStep(1);
        } catch (err) {
            setErrorMsg(err.message);
        } finally {
            setIsLoading(false);
        }
    };

    const handleUploadIdentity = async () => {
        if (!files.aadhaar || !files.selfie) {
            setErrorMsg("Please upload both Aadhaar and a live selfie.");
            return;
        }
        setIsLoading(true);
        setErrorMsg('');
        const data = new FormData();
        data.append('aadhaar_file', files.aadhaar);
        data.append('selfie_file', files.selfie);

        try {
            const response = await fetch(`${API_BASE_URL}/doctor/verify/identity?session_id=${sessionId}`, {
                method: 'POST',
                body: data
            });
            const result = await response.json();
            if (!response.ok) throw new Error(result.detail || 'Identity verification failed');
            
            // Automatically send OTP
            await fetch(`${API_BASE_URL}/doctor/verify/send-otp?session_id=${sessionId}`, { method: 'POST' });
            
            setActiveStep(2);
        } catch (err) {
            setErrorMsg(err.message);
        } finally {
            setIsLoading(false);
        }
    };

    const handleSendOTP = async () => {
        setIsLoading(true);
        setErrorMsg('');
        try {
            const response = await fetch(`${API_BASE_URL}/doctor/verify/send-otp?session_id=${sessionId}`, { method: 'POST' });
            if (!response.ok) throw new Error('Failed to resend OTP');
            // Show some success message if needed, but for now just clear error
            setErrorMsg('');
        } catch (err) {
            setErrorMsg(err.message);
        } finally {
            setIsLoading(false);
        }
    };

    const handleVerifyOTP = async () => {
        setIsLoading(true);
        setErrorMsg('');
        try {
            const response = await fetch(`${API_BASE_URL}/doctor/verify/verify-otp`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ session_id: sessionId, otp: formData.otp })
            });
            if (!response.ok) {
                const data = await response.json();
                throw new Error(data.detail || 'Invalid or expired OTP');
            }
            setActiveStep(3);
        } catch (err) {
            setErrorMsg(err.message);
        } finally {
            setIsLoading(false);
        }
    };

    const handleComplete = async () => {
        if (formData.password.length < 8) {
            setErrorMsg("Password must be at least 8 characters");
            return;
        }
        if (formData.password !== formData.confirm_password) {
            setErrorMsg("Passwords do not match");
            return;
        }
        setIsLoading(true);
        setErrorMsg('');
        try {
            const response = await fetch(`${API_BASE_URL}/doctor/verify/complete`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ session_id: sessionId, password: formData.password })
            });
            const data = await response.json();
            if (!response.ok) throw new Error(data.detail || 'Account creation failed');
            
            // Store tokens
            localStorage.setItem('token', data.access_token);
            localStorage.setItem('isAuthenticated', 'true');
            localStorage.setItem('isVerified', 'true');

            // Decode token manually for UI display (mock way)
            const base64Url = data.access_token.split('.')[1];
            const base64 = base64Url.replace(/-/g, '+').replace(/_/g, '/');
            const payload = JSON.parse(window.atob(base64));
            
            setFinalUser(payload.sub);
            setActiveStep(4);
        } catch (err) {
            setErrorMsg(err.message);
        } finally {
            setIsLoading(false);
        }
    };

    return (
        <Box sx={{ minHeight: '100vh', display: 'flex', bgcolor: '#0f172a' }}>
            {/* Left Info Panel */}
            <Box sx={{
                width: { xs: '0', md: '350px' },
                bgcolor: '#1e293b',
                display: { xs: 'none', md: 'flex' },
                flexDirection: 'column',
                p: 5,
                color: 'white',
                borderRight: '1px solid rgba(255,255,255,0.1)'
            }}>
                <Box sx={{ mb: 6, display: 'flex', alignItems: 'center' }}>
                    <VerifiedUserIcon sx={{ color: '#38bdf8', fontSize: 40, mr: 2 }} />
                    <Typography variant="h4" fontWeight="bold" letterSpacing={-1}>Nirixa</Typography>
                </Box>

                <Stepper activeStep={activeStep} orientation="vertical" sx={{ 
                    '& .MuiStepLabel-label': { color: 'rgba(255,255,255,0.4)', fontWeight: 500 },
                    '& .MuiStepLabel-label.Mui-active': { color: 'white', fontWeight: 700 },
                    '& .MuiStepLabel-label.Mui-completed': { color: '#38bdf8' },
                    '& .MuiStepIcon-root': { color: 'rgba(255,255,255,0.1)' },
                    '& .MuiStepIcon-root.Mui-active': { color: '#38bdf8' },
                    '& .MuiStepIcon-root.Mui-completed': { color: '#10b981' },
                }}>
                    {STEPS.map((label) => (
                        <Step key={label}>
                            <StepLabel>{label}</StepLabel>
                        </Step>
                    ))}
                </Stepper>

                <Box sx={{ mt: 'auto', p: 2, bgcolor: 'rgba(255,255,255,0.05)', borderRadius: 3 }}>
                    <Typography variant="caption" sx={{ color: 'rgba(255,255,255,0.5)', display: 'block' }}>
                        Verification is powered by National Health Stack (NHS) and AI-driven forensic analysis to ensure clinician authenticity.
                    </Typography>
                </Box>
            </Box>

            {/* Right Form Panel */}
            <Box sx={{ flex: 1, display: 'flex', justifyContent: 'center', alignItems: 'center', p: 3 }}>
                <Container maxWidth="sm">
                    <Paper elevation={24} sx={{ 
                        p: 5, 
                        borderRadius: 6, 
                        bgcolor: 'rgba(255,255,255,0.95)', 
                        backdropFilter: 'blur(20px)',
                        boxShadow: '0 25px 50px -12px rgba(0, 0, 0, 0.5)'
                    }}>
                        
                        {activeStep === 0 && (
                            <Box>
                                <Typography variant="h4" fontWeight="bold" gutterBottom>Professional Onboarding</Typography>
                                <Typography variant="body2" color="text.secondary" sx={{ mb: 4 }}>Enter your medical registration details to begin the clinical validation process.</Typography>
                                
                                {errorMsg && <Alert severity="error" sx={{ mb: 3, borderRadius: 2 }}>{errorMsg}</Alert>}

                                <Grid container spacing={3}>
                                    <Grid item xs={12}>
                                        <TextField fullWidth label="Full Legal Full Name" name="full_name" value={formData.full_name} onChange={handleChange} variant="filled" />
                                    </Grid>
                                    <Grid item xs={12}>
                                        <TextField fullWidth label="Registration Number" name="registration_number" placeholder="e.g. NMC-12345678" value={formData.registration_number} onChange={handleChange} variant="filled" helperText="Must start with 'NMC-' for validation." />
                                    </Grid>
                                    <Grid item xs={12}>
                                        <TextField select fullWidth label="State Medical Council" name="state_medical_council" value={formData.state_medical_council} onChange={handleChange} variant="filled">
                                            {STATE_COUNCILS.map(c => <MenuItem key={c} value={c}>{c}</MenuItem>)}
                                        </TextField>
                                    </Grid>
                                    <Grid item xs={12}>
                                        <TextField fullWidth label="Mobile Number" name="mobile_number" value={formData.mobile_number} onChange={handleChange} variant="filled" />
                                    </Grid>
                                    <Grid item xs={12}>
                                        <Button fullWidth variant="contained" size="large" onClick={handleStartVerify} disabled={isLoading || !formData.full_name || !formData.registration_number} sx={{ py: 2, borderRadius: 3, bgcolor: '#0f172a', '&:hover': { bgcolor: '#1e293b' } }}>
                                            {isLoading ? "Validating with Registry..." : "Continue to Identity Check"}
                                        </Button>
                                    </Grid>
                                </Grid>
                            </Box>
                        )}

                        {activeStep === 1 && (
                            <Box>
                                <Typography variant="h4" fontWeight="bold" gutterBottom>Identity Matching</Typography>
                                <Typography variant="body2" color="text.secondary" sx={{ mb: 4 }}>Upload your Aadhaar card and a live selfie for AI face matching.</Typography>

                                {errorMsg && <Alert severity="error" sx={{ mb: 3, borderRadius: 2 }}>{errorMsg}</Alert>}

                                <Grid container spacing={3}>
                                    <Grid item xs={12}>
                                        <Box sx={{ border: '2px dashed #cbd5e1', borderRadius: 4, p: 3, textAlign: 'center', position: 'relative' }}>
                                            {previews.aadhaar ? (
                                                <img src={previews.aadhaar} alt="Aadhaar" style={{ maxWidth: '100%', maxHeight: '150px', borderRadius: 8 }} />
                                            ) : (
                                                <Box>
                                                    <BadgeIcon sx={{ fontSize: 48, color: '#94a3b8', mb: 1 }} />
                                                    <Typography variant="subtitle2">Upload Aadhaar Front</Typography>
                                                </Box>
                                            )}
                                            <input type="file" hidden accept="image/*" id="aadhaar-input" onChange={(e) => handleFileChange(e, 'aadhaar')} />
                                            <label htmlFor="aadhaar-input">
                                                <Button component="span" sx={{ mt: 1 }}>Change File</Button>
                                            </label>
                                        </Box>
                                    </Grid>

                                    <Grid item xs={12}>
                                        <Box sx={{ border: '2px dashed #cbd5e1', borderRadius: 4, p: 3, textAlign: 'center' }}>
                                            {previews.selfie ? (
                                                <img src={previews.selfie} alt="Selfie" style={{ maxWidth: '100%', maxHeight: '150px', borderRadius: 8 }} />
                                            ) : (
                                                <Box>
                                                    <PhotoCameraIcon sx={{ fontSize: 48, color: '#94a3b8', mb: 1 }} />
                                                    <Typography variant="subtitle2">Capture/Upload Live Selfie</Typography>
                                                </Box>
                                            )}
                                            <input type="file" hidden accept="image/*" id="selfie-input" onChange={(e) => handleFileChange(e, 'selfie')} />
                                            <label htmlFor="selfie-input">
                                                <Button component="span" sx={{ mt: 1 }}>Change File</Button>
                                            </label>
                                        </Box>
                                    </Grid>

                                    <Grid item xs={12}>
                                        <Button fullWidth variant="contained" size="large" onClick={handleUploadIdentity} disabled={isLoading || !files.aadhaar || !files.selfie} sx={{ py: 2, borderRadius: 3, bgcolor: '#0f172a' }}>
                                            {isLoading ? "AI Analysis in Progress..." : "Run AI Identity Match"}
                                        </Button>
                                    </Grid>
                                </Grid>
                            </Box>
                        )}

                        {activeStep === 2 && (
                            <Box sx={{ textAlign: 'center' }}>
                                <SecurityIcon sx={{ fontSize: 64, color: '#0f172a', mb: 2 }} />
                                <Typography variant="h4" fontWeight="bold" gutterBottom>Mobile Verification</Typography>
                                <Typography variant="body2" color="text.secondary" sx={{ mb: 4 }}>Enter the 6-digit OTP sent to {formData.mobile_number}</Typography>

                                {errorMsg && <Alert severity="error" sx={{ mb: 3, borderRadius: 2 }}>{errorMsg}</Alert>}

                                <TextField fullWidth label="OTP" name="otp" value={formData.otp} onChange={handleChange} sx={{ mb: 4 }} InputProps={{ style: { fontSize: '2rem', textAlign: 'center', letterSpacing: '0.5rem' } }} />

                                <Button fullWidth variant="contained" size="large" onClick={handleVerifyOTP} disabled={isLoading || formData.otp.length < 6} sx={{ py: 2, borderRadius: 3, bgcolor: '#0f172a' }}>
                                    {isLoading ? "Verifying..." : "Verify & Continue"}
                                </Button>
                                
                                <Button variant="text" sx={{ mt: 2 }} onClick={handleSendOTP}>Resend OTP</Button>
                            </Box>
                        )}

                        {activeStep === 3 && (
                            <Box>
                                <Typography variant="h4" fontWeight="bold" gutterBottom>Secure Your Account</Typography>
                                <Typography variant="body2" color="text.secondary" sx={{ mb: 4 }}>Set a strong password to protect your clinical terminal.</Typography>

                                {errorMsg && <Alert severity="error" sx={{ mb: 3, borderRadius: 2 }}>{errorMsg}</Alert>}

                                <Grid container spacing={3}>
                                    <Grid item xs={12}>
                                        <TextField 
                                            fullWidth 
                                            label="Secure Password" 
                                            name="password" 
                                            type={showPassword ? 'text' : 'password'} 
                                            value={formData.password} 
                                            onChange={handleChange} 
                                            variant="filled"
                                            InputProps={{
                                                endAdornment: (
                                                    <InputAdornment position="end">
                                                        <IconButton onClick={() => setShowPassword(!showPassword)} edge="end">
                                                            {showPassword ? <VisibilityOff /> : <Visibility />}
                                                        </IconButton>
                                                    </InputAdornment>
                                                )
                                            }}
                                        />
                                    </Grid>
                                    <Grid item xs={12}>
                                        <TextField fullWidth label="Confirm Password" name="confirm_password" type="password" value={formData.confirm_password} onChange={handleChange} variant="filled" />
                                    </Grid>
                                    <Grid item xs={12}>
                                        <Box sx={{ p: 2, bgcolor: '#f8fafc', borderRadius: 3 }}>
                                            <Typography variant="caption" fontWeight="bold">Security Rules:</Typography>
                                            <Typography variant="caption" display="block">• Minimum 8 characters</Typography>
                                            <Typography variant="caption" display="block">• At least one clinical safety marker</Typography>
                                        </Box>
                                    </Grid>
                                    <Grid item xs={12}>
                                        <Button fullWidth variant="contained" size="large" onClick={handleComplete} disabled={isLoading || !formData.password} sx={{ py: 2, borderRadius: 3, bgcolor: '#0f172a' }}>
                                            {isLoading ? "Initializing Workspace..." : "Complete Registration"}
                                        </Button>
                                    </Grid>
                                </Grid>
                            </Box>
                        )}

                        {activeStep === 4 && (
                            <Box sx={{ textAlign: 'center' }}>
                                <CheckCircleIcon sx={{ fontSize: 80, color: '#10b981', mb: 3 }} />
                                <Typography variant="h4" fontWeight="bold" gutterBottom>Welcome, Dr. {formData.full_name.split(' ').pop()}</Typography>
                                <Typography variant="body1" color="text.secondary" sx={{ mb: 4 }}>Your Nirixa terminal is now active and clinical access is granted.</Typography>
                                
                                <Box sx={{ p: 3, bgcolor: '#0f172a', color: 'white', borderRadius: 4, mb: 4 }}>
                                    <Typography variant="caption" sx={{ opacity: 0.6 }}>YOUR UNIQUE DOCTOR ID (LOGIN USERNAME)</Typography>
                                    <Typography variant="h5" fontWeight="bold" sx={{ mt: 1, letterSpacing: 1 }}>{finalUser}</Typography>
                                </Box>

                                <Button fullWidth variant="contained" size="large" onClick={() => navigate('/')} sx={{ py: 2, borderRadius: 3, bgcolor: '#0f172a' }}>
                                    Enter Dashboard
                                </Button>
                            </Box>
                        )}

                        {isLoading && activeStep < 4 && <LinearProgress sx={{ mt: 4, borderRadius: 2, height: 6 }} />}
                    </Paper>
                </Container>
            </Box>
        </Box>
    );
}
