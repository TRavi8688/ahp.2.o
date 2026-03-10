import React, { useState } from 'react';
import { Container, Typography, TextField, Button, Box, Paper, Grid, Alert, Stepper, Step, StepLabel, LinearProgress, Divider } from '@mui/material';
import { useNavigate } from 'react-router-dom';
import CloudUploadIcon from '@mui/icons-material/CloudUpload';
import CheckCircleIcon from '@mui/icons-material/CheckCircle';
import VerifiedUserIcon from '@mui/icons-material/VerifiedUser';

const STEPS = ['Professional Profile', 'Credential Upload', 'AI Analysis'];

export default function SignupScreen() {
    const navigate = useNavigate();
    const [activeStep, setActiveStep] = useState(0);
    const [isLoading, setIsLoading] = useState(false);
    const [errorMsg, setErrorMsg] = useState('');
    const [registrationResult, setRegistrationResult] = useState(null);

    // Form State
    const [formData, setFormData] = useState({
        email: '',
        password: '',
        first_name: '',
        last_name: '',
        specialty: '',
        license_number: '',
        hospital_affiliation: ''
    });
    const [licenseFile, setLicenseFile] = useState(null);
    const [licensePreview, setLicensePreview] = useState(null);

    const handleChange = (e) => {
        setFormData({ ...formData, [e.target.name]: e.target.value });
    };

    const handleFileChange = (e) => {
        const file = e.target.files[0];
        if (file) {
            setLicenseFile(file);
            const reader = new FileReader();
            reader.onloadend = () => setLicensePreview(reader.result);
            reader.readAsDataURL(file);
        }
    };

    const handleNext = () => {
        if (activeStep < STEPS.length - 1) {
            setActiveStep(activeStep + 1);
        }
    };

    const handleBack = () => {
        setActiveStep(activeStep - 1);
    };

    const handleSignup = async () => {
        setIsLoading(true);
        setErrorMsg('');

        const data = new FormData();
        Object.keys(formData).forEach(key => data.append(key, formData[key]));
        data.append('license_file', licenseFile);

        try {
            const response = await fetch('http://localhost:8000/doctor/signup', {
                method: 'POST',
                body: data
            });

            const result = await response.json();
            if (!response.ok) throw new Error(result.detail || 'Registration failed');

            setRegistrationResult(result);
            setActiveStep(2); // Jump to final step
        } catch (error) {
            setErrorMsg(error.message);
            setActiveStep(1); // Go back to fix
        } finally {
            setIsLoading(false);
        }
    };

    return (
        <Box sx={{ minHeight: '100vh', display: 'flex', flexWrap: 'wrap', bgcolor: '#f8fafc' }}>
            {/* Left Column: Progress Context */}
            <Box sx={{
                width: { xs: '100%', md: '300px' },
                bgcolor: '#0f172a',
                color: 'white',
                p: 4,
                display: 'flex',
                flexDirection: 'column'
            }}>
                <Box sx={{ mb: 6, display: 'flex', alignItems: 'center' }}>
                    <VerifiedUserIcon sx={{ color: '#38bdf8', mr: 1, fontSize: 32 }} />
                    <Typography variant="h5" fontWeight="bold">Nirixa</Typography>
                </Box>

                <Stepper activeStep={activeStep} orientation="vertical" sx={{ '& .MuiStepLabel-label': { color: 'rgba(255,255,255,0.5)' }, '& .MuiStepLabel-label.Mui-active': { color: 'white', fontWeight: 'bold' }, '& .MuiStepLabel-label.Mui-completed': { color: '#38bdf8' } }}>
                    {STEPS.map((label) => (
                        <Step key={label}>
                            <StepLabel>{label}</StepLabel>
                        </Step>
                    ))}
                </Stepper>

                <Box sx={{ mt: 'auto' }}>
                    <Typography variant="caption" sx={{ opacity: 0.5 }}>
                        Registration involves strictly regulated clinical validation protocols.
                    </Typography>
                </Box>
            </Box>

            {/* Main Surface */}
            <Box sx={{ flex: 1, p: 4, display: 'flex', justifyContent: 'center', alignItems: 'center' }}>
                <Container maxWidth="sm">
                    <Paper elevation={0} sx={{ p: 5, borderRadius: 4, border: '1px solid #e2e8f0' }}>

                        {activeStep === 0 && (
                            <Box>
                                <Typography variant="h4" fontWeight="bold" sx={{ mb: 1 }}>Basic Information</Typography>
                                <Typography variant="body2" color="text.secondary" sx={{ mb: 4 }}>Verify your identity to start practicing on the Nirixa Terminal.</Typography>

                                <Grid container spacing={2}>
                                    <Grid item xs={6}>
                                        <TextField fullWidth label="First Name" name="first_name" value={formData.first_name} onChange={handleChange} required />
                                    </Grid>
                                    <Grid item xs={6}>
                                        <TextField fullWidth label="Last Name" name="last_name" value={formData.last_name} onChange={handleChange} required />
                                    </Grid>
                                    <Grid item xs={12}>
                                        <TextField fullWidth label="Practice Email" name="email" value={formData.email} onChange={handleChange} required />
                                    </Grid>
                                    <Grid item xs={12}>
                                        <TextField fullWidth label="Secure Password" name="password" type="password" value={formData.password} onChange={handleChange} required />
                                    </Grid>
                                    <Grid item xs={12}>
                                        <Divider sx={{ my: 1 }} />
                                    </Grid>
                                    <Grid item xs={12}>
                                        <Button fullWidth variant="contained" size="large" onClick={handleNext} disabled={!formData.email || !formData.password} sx={{ bgcolor: '#0f172a', py: 1.5 }}>
                                            Continue to Credentials
                                        </Button>
                                    </Grid>
                                </Grid>
                            </Box>
                        )}

                        {activeStep === 1 && (
                            <Box>
                                <Typography variant="h4" fontWeight="bold" sx={{ mb: 1 }}>Credentialing</Typography>
                                <Typography variant="body2" color="text.secondary" sx={{ mb: 4 }}>Mandatory medical license verification for clinical safety.</Typography>

                                {errorMsg && <Alert severity="error" sx={{ mb: 3 }}>{errorMsg}</Alert>}

                                <Grid container spacing={2}>
                                    <Grid item xs={12}>
                                        <TextField fullWidth label="Specialty (e.g. Cardiology)" name="specialty" value={formData.specialty} onChange={handleChange} required />
                                    </Grid>
                                    <Grid item xs={12}>
                                        <TextField fullWidth label="License / Registration Number" name="license_number" value={formData.license_number} onChange={handleChange} required />
                                    </Grid>
                                    <Grid item xs={12}>
                                        <TextField fullWidth label="Hospital Affiliation" name="hospital_affiliation" value={formData.hospital_affiliation} onChange={handleChange} required />
                                    </Grid>

                                    <Grid item xs={12}>
                                        <Box sx={{ mt: 2 }}>
                                            <Typography variant="subtitle2" fontWeight="bold" sx={{ mb: 1 }}>Upload Scanned License</Typography>
                                            <Button
                                                component="label"
                                                variant="outlined"
                                                fullWidth
                                                startIcon={<CloudUploadIcon />}
                                                sx={{ py: licensePreview ? 0 : 4, borderStyle: 'dashed', overflow: 'hidden' }}
                                            >
                                                {licensePreview ? (
                                                    <img src={licensePreview} alt="Preview" style={{ width: '100%', maxHeight: '150px', objectFit: 'contain' }} />
                                                ) : "Select License File (JPG/PNG)"}
                                                <input type="file" hidden accept="image/*" onChange={handleFileChange} />
                                            </Button>
                                        </Box>
                                    </Grid>

                                    <Grid item xs={12} sx={{ mt: 2, display: 'flex', gap: 2 }}>
                                        <Button fullWidth variant="outlined" size="large" onClick={handleBack}>Back</Button>
                                        <Button fullWidth variant="contained" size="large" disabled={!licenseFile || isLoading} onClick={handleSignup} sx={{ bgcolor: '#0f172a' }}>
                                            {isLoading ? "Running AI Check..." : "Verify & Sign Up"}
                                        </Button>
                                    </Grid>
                                </Grid>
                                {isLoading && <LinearProgress sx={{ mt: 3, borderRadius: 2 }} />}
                            </Box>
                        )}

                        {activeStep === 2 && registrationResult && (
                            <Box sx={{ textAlign: 'center' }}>
                                <CheckCircleIcon sx={{ color: '#10b981', fontSize: 64, mb: 2 }} />
                                <Typography variant="h4" fontWeight="bold" sx={{ mb: 1 }}>Registration Submitted</Typography>

                                <Alert severity={registrationResult.status === 'success' ? "success" : "info"} sx={{ mb: 4, textAlign: 'left' }}>
                                    {registrationResult.message}
                                </Alert>

                                <Typography variant="body2" color="text.secondary" sx={{ mb: 4 }}>
                                    {registrationResult.status === 'success'
                                        ? "AI has successfully verified your credentials. You can now log in."
                                        : "Your license is under manual review. You will receive an email once verified."}
                                </Typography>

                                <Button fullWidth variant="contained" size="large" onClick={() => navigate('/login')} sx={{ bgcolor: '#0f172a', py: 1.5 }}>
                                    Go to Login Securely
                                </Button>
                            </Box>
                        )}

                    </Paper>
                </Container>
            </Box>
        </Box>
    );
}
