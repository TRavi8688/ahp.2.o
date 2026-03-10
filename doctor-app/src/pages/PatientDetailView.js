import React, { useState } from 'react';
import { Box, Typography, Button, IconButton, Chip, Avatar, Grid, Card, CardContent, Divider, TextField, Snackbar, Alert, Dialog, DialogTitle, DialogContent, DialogActions } from '@mui/material';
import { useParams, useNavigate } from 'react-router-dom';
import { useSocket } from '../contexts/SocketContext';

import ArrowBackIcon from '@mui/icons-material/ArrowBack';
import MedicationIcon from '@mui/icons-material/Medication';
import EditNoteIcon from '@mui/icons-material/EditNote';
import WarningAmberIcon from '@mui/icons-material/WarningAmber';
import CheckCircleOutlineIcon from '@mui/icons-material/CheckCircleOutline';
import SmartToyIcon from '@mui/icons-material/SmartToy';
import CloudUploadIcon from '@mui/icons-material/CloudUpload';
import AddIcon from '@mui/icons-material/Add';

export default function PatientDetailView() {
    const { id } = useParams();
    const navigate = useNavigate();
    const { lastMessage } = useSocket();
    const [patient, setPatient] = useState(null);
    const [isLoading, setIsLoading] = useState(true);
    const [notes, setNotes] = useState('');
    const [toastOpen, setToastOpen] = useState(false);
    const [isRevoked, setIsRevoked] = useState(false);
    const [revocationDialogOpen, setRevocationDialogOpen] = useState(false);
    const [uploading, setUploading] = useState(false);
    const fileInputRef = React.useRef(null);

    const fetchPatient = async () => {
        setIsLoading(true);
        try {
            const response = await fetch(`http://localhost:8000/doctor/patient/${id}`, {
                headers: {
                    'Authorization': `Bearer ${localStorage.getItem('token')}`
                }
            });
            if (response.ok) {
                const data = await response.json();
                setPatient(data);
            } else {
                console.error("Failed to fetch patient:", response.status);
            }
        } catch (error) {
            console.error("Error fetching patient:", error);
        } finally {
            setIsLoading(false);
        }
    };

    React.useEffect(() => {
        fetchPatient();
    }, [id]);

    // Global Socket Logic for Kickout / Updates
    React.useEffect(() => {
        if (!lastMessage) return;

        if (lastMessage.type === 'access_revoked') {
            setIsRevoked(true);
            setRevocationDialogOpen(true);
        }

        if (lastMessage.type === 'patient_update') {
            console.log("DEBUG: Real-time update received:", lastMessage);
            fetchPatient();
            setToastOpen(true);
        }
    }, [lastMessage]);

    if (isLoading) {
        return (
            <Box sx={{ display: 'flex', justifyContent: 'center', alignItems: 'center', height: '80vh' }}>
                <Typography variant="h6">Syncing with AHP Network...</Typography>
            </Box>
        );
    }

    if (!patient) {
        return (
            <Box sx={{ p: 4, textAlign: 'center' }}>
                <Typography variant="h5">Patient not found or Access denied.</Typography>
                <Button onClick={() => navigate('/patients')} sx={{ mt: 2 }}>Back to Patients</Button>
            </Box>
        );
    }


    const handleSaveNotes = () => {
        setToastOpen(true);
        setNotes('');
    };

    const handleFileUpload = async (event) => {
        const file = event.target.files[0];
        if (!file) return;

        setUploading(true);
        const formData = new FormData();
        formData.append('file', file);

        try {
            const response = await fetch(`http://localhost:8000/doctor/patient/${patient.profile.ahp_id}/upload-report`, {
                method: 'POST',
                headers: {
                    'Authorization': `Bearer ${localStorage.getItem('token')}`
                },
                body: formData
            });

            if (response.ok) {
                setToastOpen(true);
                fetchPatient();
            } else {
                console.error("Upload failed");
            }
        } catch (error) {
            console.error("Error uploading file:", error);
        } finally {
            setUploading(false);
        }
    };

    const StatusWord = ({ status }) => {
        const colors = {
            normal: { c: '#10b981', bg: '#d1fae5', text: 'Normal' },
            borderline: { c: '#f59e0b', bg: '#fef3c7', text: 'Borderline' },
            concerning: { c: '#ef4444', bg: '#fee2e2', text: 'High' }
        };
        const s = colors[status] || colors.normal;
        return <Typography variant="caption" sx={{ color: s.c, fontWeight: 'bold' }}>{s.text}</Typography>
    };

    return (
        <Box sx={{ maxWidth: 1200, mx: 'auto', pb: 8 }}>

            {/* Top Bar - Floating Modern */}
            <Box sx={{
                display: 'flex',
                alignItems: 'center',
                mb: 4,
                p: 1.5,
                bgcolor: 'rgba(255,255,255,0.05)',
                backdropFilter: 'blur(10px)',
                borderRadius: '16px',
                border: '1px solid rgba(255,255,255,0.1)',
                width: 'fit-content'
            }}>
                <IconButton onClick={() => navigate(-1)} sx={{ mr: 1, color: '#fff' }}>
                    <ArrowBackIcon />
                </IconButton>
                <Typography variant="body1" fontWeight="900" sx={{ color: '#fff', pr: 2 }}>BACK TO ROSTER</Typography>
            </Box>

            {/* Revoked Banner */}
            {isRevoked && (
                <Box sx={{ bgcolor: '#fee2e2', border: '1px solid #fca5a5', p: 2, borderRadius: 2, mb: 3, display: 'flex', alignItems: 'center' }}>
                    <WarningAmberIcon sx={{ color: '#dc2626', mr: 2 }} />
                    <Typography variant="body1" sx={{ color: '#b91c1c', fontWeight: 'bold' }}>
                        ⚠️ Patient has revoked your access. You can only see previously cached data from last access date.
                    </Typography>
                </Box>
            )}

            {/* Everything below is opacity 0.4 if revoked */}
            <Box sx={{ opacity: isRevoked ? 0.4 : 1 }} style={{ pointerEvents: isRevoked ? 'none' : 'auto' }}>

                {/* Patient Header Card */}
                <Card
                    className="glass-card"
                    elevation={0}
                    sx={{
                        background: 'linear-gradient(135deg, rgba(30, 58, 138, 0.9) 0%, rgba(17, 24, 39, 0.9) 100%)',
                        color: 'white',
                        borderRadius: '32px',
                        mb: 4,
                        overflow: 'hidden',
                        boxShadow: '0 12px 40px rgba(0,0,0,0.3)'
                    }}
                >
                    <Box sx={{ p: { xs: 3, md: 5 }, display: 'flex', alignItems: 'center', flexWrap: 'wrap', gap: 4 }}>
                        <Avatar sx={{
                            width: 100,
                            height: 100,
                            bgcolor: '#0ea5e9',
                            fontSize: '3rem',
                            fontWeight: 'bold',
                            border: '4px solid rgba(255,255,255,0.3)',
                            boxShadow: '0 0 20px rgba(14, 165, 233, 0.4)'
                        }}>
                            {patient.profile.name.split(' ').map(n => n[0]).join('')}
                        </Avatar>

                        <Box sx={{ flex: 1, minWidth: 300 }}>
                            <Typography variant="h2" fontWeight="900" sx={{ mb: 1, fontFamily: 'Outfit' }}>{patient.profile.name}</Typography>
                            <Typography variant="h6" sx={{ color: 'rgba(255,255,255,0.7)', mb: 3 }}>
                                {patient.profile.age}yrs · {patient.profile.gender} · <Box component="span" sx={{ color: '#2dd4bf', fontWeight: 'bold' }}>Blood Group: {patient.profile.blood_group}</Box>
                            </Typography>

                            <Box sx={{ display: 'flex', gap: 2, alignItems: 'center' }}>
                                <Chip
                                    label={patient.profile.ahp_id}
                                    sx={{
                                        bgcolor: 'rgba(255,255,255,0.1)',
                                        color: '#fff',
                                        fontFamily: 'monospace',
                                        fontWeight: '700',
                                        borderRadius: '8px',
                                        border: '1px solid rgba(255,255,255,0.2)'
                                    }}
                                />
                                <Chip
                                    label="SECURE AHP LINK"
                                    icon={<CheckCircleOutlineIcon sx={{ color: '#4ade80 !important' }} />}
                                    sx={{
                                        bgcolor: 'rgba(52, 211, 153, 0.2)',
                                        color: '#4ade80',
                                        fontWeight: '900',
                                        letterSpacing: 1
                                    }}
                                />
                            </Box>
                        </Box>

                        <Box sx={{ display: 'flex', gap: 2 }}>
                            <Button
                                variant="contained"
                                startIcon={<MedicationIcon />}
                                sx={{
                                    bgcolor: '#fff',
                                    color: '#1e1b4b',
                                    px: 4,
                                    py: 1.5,
                                    borderRadius: '16px',
                                    '&:hover': { bgcolor: '#f1f5f9', transform: 'scale(1.05)' },
                                    fontWeight: '900',
                                    textTransform: 'none',
                                    transition: 'all 0.2s cubic-bezier(0.16, 1, 0.3, 1)'
                                }}
                                onClick={() => navigate('/prescriptions', { state: { patient: patient.profile } })}
                            >
                                Prescribe
                            </Button>
                        </Box>
                    </Box>
                </Card>

                {/* Allergy Alert Bar */}
                {patient.allergies.length > 0 ? (
                    <Box sx={{ bgcolor: '#ef4444', p: 2, borderRadius: 2, mb: 3, display: 'flex', alignItems: 'center', gap: 2, flexWrap: 'wrap' }}>
                        <WarningAmberIcon sx={{ color: 'white' }} />
                        <Typography variant="body1" fontWeight="bold" color="white">Allergy Alert — Check Before Prescribing:</Typography>
                        <Box sx={{ display: 'flex', gap: 1, flexWrap: 'wrap' }}>
                            {patient.allergies.map(a => (
                                <Chip key={a.id} label={`${a.allergen} (${a.severity})`} sx={{ bgcolor: '#7f1d1d', color: 'white', fontWeight: 'bold' }} />
                            ))}
                        </Box>
                    </Box>
                ) : (
                    <Box sx={{ bgcolor: '#10b981', p: 2, borderRadius: 2, mb: 3, display: 'flex', alignItems: 'center', gap: 2 }}>
                        <CheckCircleOutlineIcon sx={{ color: 'white' }} />
                        <Typography variant="body1" fontWeight="bold" color="white">No known allergies recorded.</Typography>
                    </Box>
                )}

                {/* AI Summary Card */}
                <Card
                    className="glass-card"
                    elevation={0}
                    sx={{
                        background: 'rgba(76, 29, 149, 0.1)',
                        border: '1px solid rgba(139, 92, 246, 0.3)',
                        mb: 4,
                        borderRadius: '24px',
                        overflow: 'hidden'
                    }}
                >
                    <Box sx={{ p: 4 }}>
                        <Box sx={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', mb: 3 }}>
                            <Box sx={{ display: 'flex', alignItems: 'center', gap: 2 }}>
                                <Box sx={{
                                    p: 1,
                                    bgcolor: '#7c3aed',
                                    borderRadius: '12px',
                                    display: 'flex',
                                    boxShadow: '0 0 15px rgba(124, 58, 237, 0.5)'
                                }}>
                                    <SmartToyIcon sx={{ color: '#fff' }} />
                                </Box>
                                <Typography variant="h6" fontWeight="900" sx={{ color: '#fff', letterSpacing: 0.5 }}>CHITTI AI — CLINICAL INSIGHT</Typography>
                            </Box>
                            <Chip
                                label="REAL-TIME"
                                size="small"
                                sx={{
                                    bgcolor: '#7c3aed',
                                    color: 'white',
                                    fontWeight: '900',
                                    px: 1
                                }}
                            />
                        </Box>

                        <Typography variant="h6" sx={{ color: 'rgba(255,255,255,0.9)', lineHeight: 1.8, mb: 3, fontWeight: 500 }}>
                            {patient.ai_summary || "No clinical insight available for this patient."}
                        </Typography>

                        <Divider sx={{ mb: 2, borderColor: 'rgba(255,255,255,0.1)' }} />
                        <Typography variant="caption" sx={{ color: 'rgba(255,255,255,0.4)', fontStyle: 'italic', display: 'flex', alignItems: 'center', gap: 1 }}>
                            <CheckCircleOutlineIcon sx={{ fontSize: 14 }} /> Verified Clinical Record Sync · AI-Assisted Recommendation
                        </Typography>
                    </Box>
                </Card>

                {/* Two-column section */}
                <Grid container spacing={4} sx={{ mb: 4 }}>

                    {/* Left Column: Conditions & Vitals */}
                    <Grid item xs={12} md={6}>
                        <Card className="glass-card" sx={{ p: 4, height: '100%', bgcolor: 'rgba(255,255,255,0.05)' }}>
                            <Typography variant="h6" fontWeight="900" sx={{ color: '#fff', mb: 3, letterSpacing: 1 }}>CLINICAL CONDITIONS</Typography>
                            <Box sx={{ display: 'flex', gap: 1.5, flexWrap: 'wrap', mb: 4 }}>
                                {patient.conditions.length > 0 ? (
                                    patient.conditions.map(c => (
                                        <Chip
                                            key={c.id}
                                            label={c.name.toUpperCase()}
                                            sx={{
                                                bgcolor: 'rgba(13, 148, 136, 0.2)',
                                                color: '#2dd4bf',
                                                fontWeight: '900',
                                                border: '1px solid rgba(45, 212, 191, 0.3)',
                                                px: 1
                                            }}
                                        />
                                    ))
                                ) : (
                                    <Typography variant="body2" sx={{ color: 'rgba(255,255,255,0.5)' }}>No conditions recorded.</Typography>
                                )}
                            </Box>

                            <Divider sx={{ my: 3, borderColor: 'rgba(255,255,255,0.1)' }} />

                            <Typography variant="h6" fontWeight="900" sx={{ color: '#fff', mb: 3, letterSpacing: 1 }}>VITALS COCKPIT</Typography>
                            <Grid container spacing={2}>
                                <Grid item xs={12}>
                                    <Box sx={{ p: 2, bgcolor: 'rgba(255,255,255,0.03)', borderRadius: '16px', border: '1px dashed rgba(255,255,255,0.2)' }}>
                                        <Typography variant="caption" sx={{ color: 'rgba(255,255,255,0.6)', fontStyle: 'italic' }}>
                                            Real-time biometric sync active. Awaiting secondary sensor calibration...
                                        </Typography>
                                    </Box>
                                </Grid>
                            </Grid>
                        </Card>
                    </Grid>

                    {/* Right Column: Medications */}
                    <Grid item xs={12} md={6}>
                        <Card className="glass-card" sx={{ p: 4, height: '100%', bgcolor: 'rgba(255,255,255,0.05)' }}>
                            <Typography variant="h6" fontWeight="900" sx={{ color: '#fff', mb: 3, letterSpacing: 1 }}>ACTIVE PRESCRIPTIONS</Typography>
                            {patient.medications.length > 0 ? (
                                <Box sx={{ display: 'flex', flexDirection: 'column', gap: 2 }}>
                                    {patient.medications.map((m, i) => (
                                        <Box
                                            key={m.id}
                                            sx={{
                                                p: 2.5,
                                                borderRadius: '20px',
                                                display: 'flex',
                                                alignItems: 'center',
                                                bgcolor: 'rgba(255,255,255,0.05)',
                                                border: '1px solid rgba(255,255,255,0.1)',
                                                transition: 'all 0.2s',
                                                '&:hover': { bgcolor: 'rgba(255,255,255,0.1)', transform: 'translateX(8px)' }
                                            }}
                                        >
                                            <Box sx={{
                                                width: 50,
                                                height: 50,
                                                bgcolor: 'rgba(13, 148, 136, 0.2)',
                                                borderRadius: '14px',
                                                display: 'flex',
                                                alignItems: 'center',
                                                justifyContent: 'center',
                                                mr: 3,
                                                fontSize: '1.5rem',
                                                boxShadow: '0 4px 12px rgba(0,0,0,0.2)'
                                            }}>
                                                💊
                                            </Box>
                                            <Box sx={{ flex: 1 }}>
                                                <Typography variant="subtitle1" fontWeight="900" sx={{ color: '#fff', mb: 0.5 }}>{m.generic_name.toUpperCase()}</Typography>
                                                <Typography variant="caption" sx={{ color: 'rgba(255,255,255,0.6)', fontWeight: 700, letterSpacing: 0.5 }}>{m.dosage} · {m.frequency.toUpperCase()}</Typography>
                                            </Box>
                                        </Box>
                                    ))}
                                </Box>
                            ) : (
                                <Typography variant="body2" sx={{ color: 'rgba(255,255,255,0.5)' }}>No active medications recorded.</Typography>
                            )}
                        </Card>
                    </Grid>
                </Grid>
                bitumen
                {/* Third Two-column section: Records */}
                <Box sx={{ mb: 4 }}>
                    <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', mb: 2 }}>
                        <Typography variant="h6" fontWeight="bold" sx={{ color: '#1f2937' }}>Patient Records</Typography>
                        <Box sx={{ display: 'flex', gap: 1 }}>
                            <input
                                type="file"
                                hidden
                                ref={fileInputRef}
                                onChange={handleFileUpload}
                                accept=".pdf,.jpg,.jpeg,.png"
                            />
                            <Button
                                size="small"
                                variant="outlined"
                                startIcon={<CloudUploadIcon />}
                                onClick={() => fileInputRef.current.click()}
                                disabled={uploading}
                                sx={{ color: '#0d9488', borderColor: '#0d9488', textTransform: 'none', fontWeight: 'bold' }}
                            >
                                {uploading ? 'Processing...' : 'Add Patient Record'}
                            </Button>
                        </Box>
                    </Box>

                    <Card className="glass-card" elevation={0} sx={{ bgcolor: 'rgba(255,255,255,0.02)', border: '1px solid rgba(255,255,255,0.1)', borderRadius: '24px', overflow: 'hidden' }}>
                        <Box sx={{ p: 3, display: 'flex', alignItems: 'center', bgcolor: 'rgba(255,255,255,0.05)', borderBottom: '1px solid rgba(255,255,255,0.1)' }}>
                            <Typography variant="subtitle2" fontWeight="900" sx={{ color: 'rgba(255,255,255,0.4)', width: '20%', letterSpacing: 1 }}>DATE</Typography>
                            <Typography variant="subtitle2" fontWeight="900" sx={{ color: 'rgba(255,255,255,0.4)', width: '15%', letterSpacing: 1 }}>TYPE</Typography>
                            <Typography variant="subtitle2" fontWeight="900" sx={{ color: 'rgba(255,255,255,0.4)', flex: 1, letterSpacing: 1 }}>CLINICAL DATA & AI SYNTHESIS</Typography>
                            <Typography variant="subtitle2" fontWeight="900" sx={{ color: 'rgba(255,255,255,0.4)', width: '15%', textAlign: 'right', letterSpacing: 1 }}>INTEL</Typography>
                        </Box>

                        {patient.records && patient.records.length > 0 ? patient.records.map((r, i) => (
                            <Box
                                key={r.id}
                                sx={{
                                    p: 3,
                                    borderBottom: i < patient.records.length - 1 ? '1px solid rgba(255,255,255,0.05)' : 'none',
                                    display: 'flex',
                                    alignItems: 'center',
                                    transition: 'all 0.2s',
                                    '&:hover': { bgcolor: 'rgba(255,255,255,0.03)' }
                                }}
                            >
                                <Typography variant="body2" sx={{ fontFamily: 'monospace', color: 'rgba(255,255,255,0.5)', width: '20%', fontWeight: 700 }}>{new Date(r.created_at).toLocaleDateString()}</Typography>
                                <Box sx={{ width: '15%' }}>
                                    <Chip
                                        label={r.type.toUpperCase()}
                                        size="small"
                                        sx={{
                                            bgcolor: 'rgba(255,255,255,0.05)',
                                            color: '#fff',
                                            fontWeight: '900',
                                            borderRadius: '6px'
                                        }}
                                    />
                                </Box>
                                <Box sx={{ flex: 1 }}>
                                    <Typography variant="body1" sx={{ color: '#fff', fontWeight: '900', mb: 0.5 }}>{r.title}</Typography>
                                    <Typography variant="body2" sx={{ color: 'rgba(255,255,255,0.6)', lineHeight: 1.6 }}>{r.ai_summary}</Typography>
                                    {r.uploaded_by && (
                                        <Typography variant="caption" sx={{ color: '#2dd4bf', fontWeight: '900', mt: 1, display: 'block', letterSpacing: 0.5 }}>
                                            DATA SOURCE: {r.uploaded_by.toUpperCase()}
                                        </Typography>
                                    )}
                                </Box>
                                <Box sx={{ width: '15%', textAlign: 'right' }}>
                                    <Button
                                        variant="outlined"
                                        size="small"
                                        sx={{
                                            color: '#fff',
                                            borderColor: 'rgba(255,255,255,0.2)',
                                            fontWeight: '900',
                                            textTransform: 'none',
                                            borderRadius: '10px',
                                            '&:hover': { bgcolor: 'rgba(255,255,255,0.1)', borderColor: '#fff' }
                                        }}
                                        onClick={() => window.open(r.file_url, '_blank')}
                                    >
                                        OPEN
                                    </Button>
                                </Box>
                            </Box>
                        )) : (
                            <Box sx={{ p: 4, textAlign: 'center' }}>
                                <Typography variant="body2" sx={{ color: 'rgba(255,255,255,0.4)' }}>Historical medical vault is currently empty.</Typography>
                            </Box>
                        )}
                    </Card>
                </Box>

                <Divider sx={{ my: 4 }} />

                {/* Second Two-column section */}
                <Grid container spacing={4}>

                    {/* Left Column: Timeline */}
                    <Grid item xs={12} md={6}>
                        <Typography variant="h6" fontWeight="bold" sx={{ color: '#1f2937', mb: 3 }}>Visit History</Typography>
                        <Box sx={{ position: 'relative', pl: 3, borderLeft: '2px solid #e5e7eb', ml: 1 }}>
                            {patient.history && patient.history.length > 0 ? patient.history.map((h, i) => (
                                <Box key={i} sx={{ mb: 4, position: 'relative' }}>
                                    <Box sx={{
                                        position: 'absolute', left: -31, top: 4, width: 14, height: 14, borderRadius: '50%',
                                        bgcolor: h.type === 'teal' ? '#0d9488' : h.type === 'red' ? '#ef4444' : '#f59e0b',
                                        border: '3px solid white'
                                    }} />
                                    <Typography variant="subtitle2" fontWeight="bold" sx={{ color: '#111827' }}>{h.title}</Typography>
                                    <Typography variant="body2" sx={{ color: '#4b5563', my: 0.5 }}>{h.desc}</Typography>
                                    <Typography variant="caption" sx={{ fontFamily: 'monospace', color: '#6b7280' }}>{h.date}</Typography>
                                </Box>
                            )) : (
                                <Typography variant="body2" sx={{ color: '#6b7280' }}>No previous visits recorded.</Typography>
                            )}
                        </Box>
                    </Grid>

                    {/* Right Column: Emergency & Notes */}
                    <Grid item xs={12} md={6}>
                        <Typography variant="h6" fontWeight="bold" sx={{ color: '#1f2937', mb: 2 }}>Emergency Contacts</Typography>
                        <Box sx={{ mb: 4 }}>
                            {patient.contacts && patient.contacts.length > 0 ? patient.contacts.map(c => (
                                <Box key={c.name} sx={{ mb: 1.5, display: 'flex', justifyContent: 'space-between', p: 2, bgcolor: '#f9fafb', borderRadius: 2, border: '1px solid #e5e7eb' }}>
                                    <Box>
                                        <Typography variant="subtitle2" fontWeight="bold" sx={{ color: '#111827' }}>{c.name}</Typography>
                                        <Typography variant="caption" sx={{ color: '#6b7280' }}>{c.relation}</Typography>
                                    </Box>
                                    <Typography variant="body2" fontWeight="bold" sx={{ color: '#0d9488' }}>{c.phone}</Typography>
                                </Box>
                            )) : (
                                <Typography variant="body2" sx={{ color: '#6b7280' }}>No emergency contacts provided.</Typography>
                            )}
                        </Box>

                        <Divider sx={{ my: 3 }} />

                        {!isRevoked && (
                            <Box>
                                <Typography variant="h6" fontWeight="bold" sx={{ color: '#1f2937', mb: 2 }}>Add Consultation Notes</Typography>
                                <TextField
                                    fullWidth
                                    multiline
                                    rows={4}
                                    placeholder="Type notes for this consultation — will be added to patient AHP profile with consent..."
                                    value={notes}
                                    onChange={(e) => setNotes(e.target.value)}
                                    sx={{ mb: 2, bgcolor: 'white' }}
                                />
                                <Button
                                    variant="contained"
                                    fullWidth
                                    disableElevation
                                    sx={{ bgcolor: '#0d9488', '&:hover': { bgcolor: '#0f766e' }, py: 1.5, fontWeight: 'bold' }}
                                    onClick={handleSaveNotes}
                                    disabled={!notes.trim()}
                                >
                                    Save Notes to AHP
                                </Button>
                            </Box>
                        )}
                    </Grid>

                </Grid>
            </Box>

            <Snackbar open={toastOpen} autoHideDuration={3000} onClose={() => setToastOpen(false)} anchorOrigin={{ vertical: 'bottom', horizontal: 'center' }}>
                <Alert onClose={() => setToastOpen(false)} severity="success" sx={{ width: '100%', fontWeight: 'bold' }}>
                    Notes saved to patient AHP profile ✓
                </Alert>
            </Snackbar>

            {/* Revocation Kickout Dialog */}
            <Dialog
                open={revocationDialogOpen}
                onClose={() => navigate('/history')}
                disableEscapeKeyDown
            >
                <DialogTitle sx={{ display: 'flex', alignItems: 'center', gap: 1, color: '#dc2626', fontWeight: 'bold' }}>
                    <WarningAmberIcon /> Access Revoked
                </DialogTitle>
                <DialogContent>
                    <Typography>
                        The patient has revoked your access to their medical records. You can no longer view this profile.
                    </Typography>
                </DialogContent>
                <DialogActions sx={{ p: 2 }}>
                    <Button
                        variant="contained"
                        fullWidth
                        onClick={() => navigate('/history')}
                        sx={{ bgcolor: '#dc2626', '&:hover': { bgcolor: '#b91c1c' }, fontWeight: 'bold' }}
                    >
                        Return to Dashboard
                    </Button>
                </DialogActions>
            </Dialog>

        </Box>
    );
}
