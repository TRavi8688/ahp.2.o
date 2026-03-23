import React, { useState } from 'react';
import { Container, Typography, TextField, Button, Box, Paper, Grid, Alert, MenuItem } from '@mui/material';
import { useNavigate } from 'react-router-dom';
import { API_BASE_URL } from '../api';
import CloudUploadIcon from '@mui/icons-material/CloudUpload';

const STATE_COUNCILS = [
    "Medical Council of India (MCI) / NMC",
    "Andhra Pradesh Medical Council",
    "Arunachal Pradesh Medical Council",
    "Assam Medical Council",
    "Bihar Medical Council",
    "Chhattisgarh Medical Council",
    "Delhi Medical Council",
    "Goa Medical Council",
    "Gujarat Medical Council",
    "Haryana Medical Council",
    "Himachal Pradesh Medical Council",
    "Jharkhand Medical Council",
    "Karnataka Medical Council",
    "Kerala Medical Council",
    "Madhya Pradesh Medical Council",
    "Maharashtra Medical Council",
    "Odisha Council of Medical Registration",
    "Punjab Medical Council",
    "Rajasthan Medical Council",
    "Tamil Nadu Medical Council",
    "Telangana State Medical Council",
    "Uttar Pradesh Medical Council",
    "Uttarakhand Medical Council",
    "West Bengal Medical Council"
];

export default function VerificationScreen() {
    const navigate = useNavigate();
    const [status, setStatus] = useState('idle'); // idle | submitting | pending | error
    const [errorMessage, setErrorMessage] = useState('');
    
    // Form State
    const [formData, setFormData] = useState({
        full_name: '',
        registration_number: '',
        state_council: '',
        specialty: '',
        experience_years: '',
        hospital_affiliation: ''
    });

    const handleChange = (e) => {
        setFormData({...formData, [e.target.name]: e.target.value});
    };

    const handleSubmit = async (e) => {
        e.preventDefault();
        setStatus('submitting');
        setErrorMessage('');

        try {
            const response = await fetch(`${API_BASE_URL}/doctor/verify`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify({
                    full_name: formData.full_name,
                    registration_number: formData.registration_number,
                    state_council: formData.state_council,
                    specialty: formData.specialty,
                    experience_years: parseInt(formData.experience_years, 10),
                    hospital_affiliation: formData.hospital_affiliation
                })
            });

            const data = await response.json();

            if (!response.ok) {
                throw new Error(data.detail || 'Verification failed. Please check your credentials.');
            }

            setStatus('pending');
            
            // Save token and mark as verified
            localStorage.setItem('isAuthenticated', 'true');
            localStorage.setItem('isVerified', 'true');
            if (data.access_token) {
                localStorage.setItem('token', data.access_token);
            }

            // Mock immediate verification for our demo
            setTimeout(() => {
                window.location.href = '/';
            }, 3000);

        } catch (error) {
            setStatus('error');
            setErrorMessage(error.message);
        }
    };

    if (status === 'pending') {
        return (
            <Container maxWidth="sm" sx={{ mt: 10 }}>
                <Alert severity="success" sx={{ mb: 4, py: 2, fontSize: '1.1rem' }}>
                    <Typography variant="h6" fontWeight="bold">Verification Successful (Mock API)</Typography>
                    Your credentials have been validated against the national registry. You will be redirected shortly...
                </Alert>
            </Container>
        );
    }

    return (
        <Box sx={{ minHeight: '100vh', display: 'flex', bgcolor: '#f4f6f8', py: 6 }}>
            <Container maxWidth="md">
                <Paper elevation={0} sx={{ p: { xs: 3, md: 5 }, borderRadius: 3, border: 1, borderColor: 'divider' }}>
                    <Box sx={{ mb: 4, textAlign: 'center' }}>
                        <Typography variant="h4" fontWeight="bold" gutterBottom>Doctor Verification (One Time)</Typography>
                        <Typography variant="body1" color="text.secondary">
                            To comply with healthcare regulations and prevent fake profiles, all clinicians must be verified against the official medical registry.
                        </Typography>
                    </Box>

                    {status === 'error' && (
                        <Alert severity="error" sx={{ mb: 4 }}>
                            {errorMessage}
                        </Alert>
                    )}

                    <form onSubmit={handleSubmit}>
                        <Grid container spacing={3}>
                            <Grid item xs={12} md={6}>
                                <TextField fullWidth label="Full Legal Name (as on license)" name="full_name" value={formData.full_name} onChange={handleChange} required />
                            </Grid>
                            <Grid item xs={12} md={6}>
                                <TextField fullWidth label="Medical Registration Number" name="registration_number" value={formData.registration_number} onChange={handleChange} required placeholder="e.g. NMC-12345" helperText="Demo: 'NMC-' passes, '123' fails." />
                            </Grid>

                            <Grid item xs={12}>
                                <TextField
                                    select
                                    fullWidth
                                    label="State Medical Council"
                                    name="state_council"
                                    value={formData.state_council}
                                    onChange={handleChange}
                                    required
                                >
                                    {STATE_COUNCILS.map((council) => (
                                        <MenuItem key={council} value={council}>
                                            {council}
                                        </MenuItem>
                                    ))}
                                </TextField>
                            </Grid>

                            <Grid item xs={12} md={6}>
                                <TextField fullWidth label="Primary Specialty" name="specialty" value={formData.specialty} onChange={handleChange} required />
                            </Grid>
                            <Grid item xs={12} md={6}>
                                <TextField fullWidth label="Years of Experience" name="experience_years" type="number" value={formData.experience_years} onChange={handleChange} required />
                            </Grid>

                            <Grid item xs={12}>
                                <TextField fullWidth label="Primary Hospital / Clinic Affiliation" name="hospital_affiliation" value={formData.hospital_affiliation} onChange={handleChange} required />
                            </Grid>

                            <Grid item xs={12} mt={2}>
                                <Typography variant="subtitle1" fontWeight="bold" mb={1}>Upload Medical License (Optional for Real-time API)</Typography>
                                <Button
                                    component="label"
                                    variant="outlined"
                                    startIcon={<CloudUploadIcon />}
                                    sx={{ py: 3, width: '100%', borderStyle: 'dashed', borderWidth: 2 }}
                                >
                                    Select License File (PDF or Image)
                                    <input type="file" hidden accept=".pdf,image/*" />
                                </Button>
                                <Typography variant="caption" color="text.secondary" display="block" mt={1}>
                                    Max file size: 5MB. Must be clearly legible.
                                </Typography>
                            </Grid>

                            <Grid item xs={12} mt={3}>
                                <Button
                                    type="submit"
                                    fullWidth
                                    variant="contained"
                                    color="primary"
                                    size="large"
                                    disabled={status === 'submitting'}
                                    sx={{ py: 2, fontSize: '1.2rem' }}
                                >
                                    {status === 'submitting' ? "Validating with Registry..." : "Verify & Register"}
                                </Button>
                            </Grid>
                        </Grid>
                    </form>

                    <Box textAlign="center" mt={3}>
                        <Button color="inherit" onClick={() => navigate('/login')}>Back to Login</Button>
                    </Box>
                </Paper>
            </Container>
        </Box>
    );
}
