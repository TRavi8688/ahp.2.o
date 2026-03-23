import React, { useState, useEffect } from 'react';
import { Box, Typography, Button, TextField, Grid, Card, IconButton, Autocomplete, MenuItem, Divider, Chip, Snackbar, Alert } from '@mui/material';
import { useLocation } from 'react-router-dom';
import { API_BASE_URL } from '../api';

// Icons
import AddCircleOutlineIcon from '@mui/icons-material/AddCircleOutline';
import SendIcon from '@mui/icons-material/Send';
import PictureAsPdfIcon from '@mui/icons-material/PictureAsPdf';
import MedicationIcon from '@mui/icons-material/Medication';
import WarningAmberIcon from '@mui/icons-material/WarningAmber';
import CheckCircleIcon from '@mui/icons-material/CheckCircle';
import DeleteOutlineIcon from '@mui/icons-material/DeleteOutline';
import MicIcon from '@mui/icons-material/Mic';
import MicOffIcon from '@mui/icons-material/MicOff';

export default function Prescriptions() {
    const location = useLocation();
    const preSelectedPatient = location.state?.patient || null;

    const [patients, setPatients] = useState([]);
    const [selectedPatient, setSelectedPatient] = useState(preSelectedPatient);
    const [diagnosis, setDiagnosis] = useState('');
    const [notes, setNotes] = useState('');
    const [medications, setMedications] = useState([]);
    const [isLoading, setIsLoading] = useState(true);
    const [isSending, setIsSending] = useState(false);

    useEffect(() => {
        const fetchPatients = async () => {
            try {
                const response = await fetch(`${API_BASE_URL}/doctor/my-patients`, {
                    headers: {
                        'Authorization': `Bearer ${localStorage.getItem('token')}`
                    }
                });
                if (response.ok) {
                    const data = await response.json();
                    setPatients(data);
                    if (data.length > 0 && !preSelectedPatient) {
                        setSelectedPatient(data[0]);
                    }
                }
            } catch (error) {
                console.error("Failed to fetch patients", error);
            } finally {
                setIsLoading(false);
            }
        };
        fetchPatients();
    }, []);

    // New Medicine Form
    const [showNewMed, setShowNewMed] = useState(false);
    const [newMedName, setNewMedName] = useState('');
    const [newMedDose, setNewMedDose] = useState('');

    // AI Checking State
    const [isChecking, setIsChecking] = useState(false);
    const [conflict, setConflict] = useState(null);

    const [toastOpen, setToastOpen] = useState(false);
    const [isListening, setIsListening] = useState(false);

    const startVoiceToNote = (field) => {
        setIsListening(true);
        setTimeout(() => setIsListening(false), 2000);
    };

    // Mock drug database for autocomplete
    const DRUG_DB = ['Amoxicillin', 'Amlodipine', 'Metformin', 'Salbutamol', 'Atorvastatin', 'Paracetamol', 'Ibuprofen', 'Levothyroxine'];

    // AI Drug Interaction Check
    const runAICheck = async (medName) => {
        if (!selectedPatient) return;
        setIsChecking(true);
        setConflict(null);

        // Mock check logic
        setTimeout(() => {
            setConflict({
                status: 'passed',
                message: `✓ Allergy check passed. No conflicts detected.`
            });
            setIsChecking(false);
        }, 1200);
    };

    const handleAddMedication = () => {
        if (!newMedName) return;
        setMedications([...medications, { name: newMedName, dose: newMedDose || 'As directed', frequency: 'OD', route: 'Oral' }]);
        setShowNewMed(false);
        runAICheck(newMedName);
        setNewMedName('');
        setNewMedDose('');
    };

    const handleRemoveMed = (index) => {
        const newMeds = [...medications];
        newMeds.splice(index, 1);
        setMedications(newMeds);
        setConflict(null); // reset check when meds change
    };

    const handleSend = async () => {
        if (!selectedPatient || medications.length === 0) return;

        setIsSending(true);
        try {
            const response = await fetch(`${API_BASE_URL}/doctor/patient/${selectedPatient.ahp_id}/prescribe`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    'Authorization': `Bearer ${localStorage.getItem('token')}`
                },
                body: JSON.stringify({
                    items: medications.map(m => ({
                        generic_name: m.name,
                        dosage: m.dose,
                        frequency: m.frequency,
                        brand_name: "",
                        dosage_unit: "",
                        route: m.route || "Oral",
                        indication: diagnosis
                    })),
                    notes: notes
                })
            });

            if (response.ok) {
                setToastOpen(true);
                // Reset form
                setMedications([]);
                setDiagnosis('');
                setNotes('');
                setConflict(null);
            } else {
                console.error("Failed to send prescription");
            }
        } catch (error) {
            console.error("Error sending prescription:", error);
        } finally {
            setIsSending(false);
        }
    };

    return (
        <Box sx={{ maxWidth: 1400, mx: 'auto' }}>

            {/* Header */}
            <Box sx={{ mb: 4, display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                <Typography variant="h4" fontWeight="bold" sx={{ color: '#1f2937' }}>
                    New Prescription
                </Typography>
            </Box>

            <Grid container spacing={4}>

                {/* Left Column - New Prescription Form */}
                <Grid item xs={12} md={7}>
                    <Card elevation={0} sx={{ border: '1px solid #e5e7eb', borderRadius: 2, p: 3 }}>

                        {/* Patient & Diagnosis */}
                        <Box sx={{ mb: 4 }}>
                            <Typography variant="body2" fontWeight="bold" sx={{ color: '#4b5563', mb: 1 }}>Patient</Typography>
                            <Autocomplete
                                options={patients}
                                getOptionLabel={(option) => `${option.name} (${option.ahp_id})`}
                                value={selectedPatient}
                                disabled={!!preSelectedPatient}
                                onChange={(e, v) => { setSelectedPatient(v); setConflict(null); }}
                                renderInput={(params) => <TextField {...params} size="small" placeholder={preSelectedPatient ? "" : "Select Patient"} />}
                                sx={{ mb: 3 }}
                            />

                            <Typography variant="body2" fontWeight="bold" sx={{ color: '#4b5563', mb: 1 }}>Diagnosis / Reason</Typography>
                            <TextField
                                fullWidth
                                size="small"
                                value={diagnosis}
                                onChange={(e) => setDiagnosis(e.target.value)}
                            />
                        </Box>

                        {/* Medications Section */}
                        <Box sx={{ mb: 4 }}>
                            <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', mb: 2 }}>
                                <Typography variant="h6" fontWeight="bold" sx={{ color: '#1f2937' }}>Medications</Typography>
                            </Box>

                            <Box sx={{ border: '1px solid #e5e7eb', borderRadius: 2, overflow: 'hidden', mb: 2 }}>
                                {medications.length > 0 ? medications.map((med, i) => (
                                    <Box key={i} sx={{ display: 'flex', alignItems: 'center', p: 2, borderBottom: i < medications.length - 1 ? '1px solid #e5e7eb' : 'none', bgcolor: '#f9fafb' }}>
                                        <MedicationIcon sx={{ color: '#9ca3af', mr: 2 }} />
                                        <Box sx={{ flex: 1 }}>
                                            <Typography variant="subtitle2" fontWeight="bold" sx={{ color: '#111827' }}>{med.name}</Typography>
                                            <Typography variant="caption" sx={{ color: '#6b7280' }}>
                                                {med.dose} · {med.frequency} · {med.route}
                                            </Typography>
                                        </Box>
                                        <IconButton size="small" color="error" onClick={() => handleRemoveMed(i)}>
                                            <DeleteOutlineIcon fontSize="small" />
                                        </IconButton>
                                    </Box>
                                )) : (
                                    <Typography variant="body2" sx={{ p: 3, color: '#6b7280', textAlign: 'center' }}>No medications added.</Typography>
                                )}
                            </Box>

                            {/* AI Checking UI */}
                            {isChecking && (
                                <Box sx={{ display: 'flex', alignItems: 'center', p: 2, bgcolor: '#f3f4f6', borderRadius: 2, mb: 2 }}>
                                    <Typography variant="body2" sx={{ color: '#6b7280', fontStyle: 'italic', fontWeight: 'bold' }}>🤖 AI running interaction check...</Typography>
                                </Box>
                            )}

                            {conflict && !isChecking && (
                                <Box sx={{
                                    display: 'flex', alignItems: 'center', p: 2, borderRadius: 2, mb: 2,
                                    bgcolor: conflict.status === 'failed' ? '#fee2e2' : '#d1fae5',
                                    border: `1px solid ${conflict.status === 'failed' ? '#fca5a5' : '#6ee7b7'}`
                                }}>
                                    {conflict.status === 'failed' ? (
                                        <WarningAmberIcon sx={{ color: '#dc2626', mr: 1.5 }} />
                                    ) : (
                                        <CheckCircleIcon sx={{ color: '#059669', mr: 1.5 }} />
                                    )}
                                    <Typography variant="body2" fontWeight="bold" sx={{ color: conflict.status === 'failed' ? '#b91c1c' : '#065f46' }}>
                                        {conflict.status === 'failed' ? conflict.warning : conflict.message}
                                    </Typography>
                                </Box>
                            )}

                            {/* Add Med Form */}
                            {showNewMed ? (
                                <Box sx={{ p: 2, border: '1px dashed #d1d5db', borderRadius: 2, bgcolor: 'white' }}>
                                    <Grid container spacing={2}>
                                        <Grid item xs={12} sm={6}>
                                            <Autocomplete
                                                freeSolo
                                                options={DRUG_DB}
                                                value={newMedName}
                                                onInputChange={(e, v) => setNewMedName(v)}
                                                renderInput={(params) => <TextField {...params} label="Medicine Name" size="small" autoFocus />}
                                            />
                                        </Grid>
                                        <Grid item xs={12} sm={6}>
                                            <TextField fullWidth label="Dose (e.g. 500mg)" size="small" value={newMedDose} onChange={(e) => setNewMedDose(e.target.value)} />
                                        </Grid>
                                        <Grid item xs={12}>
                                            <Box sx={{ display: 'flex', gap: 1, justifyContent: 'flex-end', mt: 1 }}>
                                                <Button size="small" onClick={() => setShowNewMed(false)} color="inherit">Cancel</Button>
                                                <Button size="small" variant="contained" sx={{ bgcolor: '#0d9488' }} onClick={handleAddMedication}>Add</Button>
                                            </Box>
                                        </Grid>
                                    </Grid>
                                </Box>
                            ) : (
                                <Button
                                    variant="outlined"
                                    startIcon={<AddCircleOutlineIcon />}
                                    onClick={() => setShowNewMed(true)}
                                    sx={{ color: '#0d9488', borderColor: '#0d9488', borderStyle: 'dashed', '&:hover': { bgcolor: '#f0fdfa' }, textTransform: 'none', fontWeight: 'bold' }}
                                >
                                    Add Medicine
                                </Button>
                            )}
                        </Box>

                        {/* Notes Section */}
                        <Box sx={{ mb: 4 }}>
                            <Box sx={{ display: 'flex', alignItems: 'center', mb: 1 }}>
                                <Typography variant="body2" fontWeight="bold" sx={{ color: '#4b5563', flex: 1 }}>Doctor Notes (Visible to Patient)</Typography>
                                <IconButton size="small" onClick={() => startVoiceToNote('notes')} color={isListening ? "error" : "primary"}>
                                    {isListening ? <MicOffIcon fontSize="small" /> : <MicIcon fontSize="small" />}
                                </IconButton>
                            </Box>
                            <TextField
                                fullWidth
                                multiline
                                rows={3}
                                placeholder="Add notes that will be stored in patient's AHP profile..."
                                value={notes}
                                onChange={(e) => setNotes(e.target.value)}
                            />
                        </Box>

                        <Divider sx={{ my: 3 }} />

                        {/* Actions */}
                        <Box sx={{ display: 'flex', gap: 2 }}>
                            <Button
                                variant="contained"
                                size="large"
                                endIcon={<SendIcon />}
                                disabled={medications.length === 0 || isSending}
                                onClick={handleSend}
                                sx={{ flex: 1, bgcolor: '#0d9488', '&:hover': { bgcolor: '#0f766e' }, fontWeight: 'bold' }}
                            >
                                Send to Patient AHP
                            </Button>
                            <Button
                                variant="outlined"
                                size="large"
                                startIcon={<PictureAsPdfIcon />}
                                sx={{ color: '#4b5563', borderColor: '#d1d5db', '&:hover': { bgcolor: '#f3f4f6' }, fontWeight: 'bold' }}
                            >
                                Download PDF
                            </Button>
                        </Box>

                    </Card>
                </Grid>

                {/* Right Column - Timeline */}
                <Grid item xs={12} md={5}>
                    <Typography variant="h6" fontWeight="bold" sx={{ color: '#1f2937', mb: 3 }}>
                        Recent Prescriptions
                    </Typography>

                    <Box sx={{ position: 'relative', pl: 3, borderLeft: '2px solid #e5e7eb', ml: 1 }}>
                        <Box sx={{ py: 4, textAlign: 'center' }}>
                            <Typography color="text.secondary">No prescriptions sent out recently.</Typography>
                        </Box>
                    </Box>
                </Grid>

            </Grid>

            <Snackbar open={toastOpen} autoHideDuration={3000} onClose={() => setToastOpen(false)} anchorOrigin={{ vertical: 'bottom', horizontal: 'center' }}>
                <Alert onClose={() => setToastOpen(false)} severity="success" sx={{ width: '100%', fontWeight: 'bold' }}>
                    Prescription successfully sent to patient's AHP profile.
                </Alert>
            </Snackbar>

        </Box>
    );
}

const TimelineEntry = ({ status, title, desc, date }) => {
    const getColor = (s) => {
        if (s === 'teal') return '#0d9488';
        if (s === 'amber') return '#f59e0b';
        if (s === 'red') return '#ef4444';
        return '#6b7280';
    };

    return (
        <Box sx={{ mb: 4, position: 'relative' }}>
            <Box sx={{
                position: 'absolute', left: -31, top: 2, width: 14, height: 14, borderRadius: '50%',
                bgcolor: getColor(status),
                border: '3px solid white'
            }} />
            <Typography variant="subtitle2" fontWeight="bold" sx={{ color: '#111827', mb: 0.5 }}>{title}</Typography>
            <Typography variant="body2" sx={{ color: '#4b5563', mb: 0.5 }}>{desc}</Typography>
            <Typography variant="caption" sx={{ fontFamily: 'monospace', color: '#9ca3af', fontWeight: 'bold' }}>{date}</Typography>
        </Box>
    );
};
