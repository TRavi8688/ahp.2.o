import React, { useState } from 'react';
import { Box, Typography, Card, CardContent, Divider, Avatar, Chip, IconButton, InputBase, Button, List, ListItem, Tooltip } from '@mui/material';
import { useNavigate } from 'react-router-dom';
import { API_BASE_URL } from '../api';

// Icons
import SearchIcon from '@mui/icons-material/Search';
import FilterListIcon from '@mui/icons-material/FilterList';
import WarningIcon from '@mui/icons-material/Warning';
import LocalHospitalIcon from '@mui/icons-material/LocalHospital';
import MedicationIcon from '@mui/icons-material/Medication';
import FolderSharedIcon from '@mui/icons-material/FolderShared';
import InfoOutlinedIcon from '@mui/icons-material/InfoOutlined';


export default function PatientList() {
    const navigate = useNavigate();
    const [patients, setPatients] = useState([]);
    const [isLoading, setIsLoading] = useState(true);
    const [selectedPatientId, setSelectedPatientId] = useState(null);
    const [selectedPatientData, setSelectedPatientData] = useState(null);
    const [isLoadingDetail, setIsLoadingDetail] = useState(false);
    const [searchQuery, setSearchQuery] = useState("");

    // Fetch Patient List
    React.useEffect(() => {
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
                }
            } catch (error) {
                console.error("Failed to fetch patients", error);
            } finally {
                setIsLoading(false);
            }
        };
        fetchPatients();
    }, []);

    // Fetch Patient Detail when selected
    React.useEffect(() => {
        if (!selectedPatientId) return;

        const fetchDetail = async () => {
            setIsLoadingDetail(true);
            try {
                const response = await fetch(`${API_BASE_URL}/doctor/patient/${selectedPatientId}`, {
                    headers: {
                        'Authorization': `Bearer ${localStorage.getItem('token')}`
                    }
                });
                if (response.ok) {
                    const data = await response.json();
                    setSelectedPatientData(data);
                }
            } catch (error) {
                console.error("Failed to fetch details", error);
            } finally {
                setIsLoadingDetail(false);
            }
        };
        fetchDetail();
    }, [selectedPatientId]);

    // Filter logic
    const filteredPatients = patients.filter(p =>
        p.name.toLowerCase().includes(searchQuery.toLowerCase()) ||
        p.ahp_id.toLowerCase().includes(searchQuery.toLowerCase())
    );

    const getStatusColor = (status) => {
        if (status === 'urgent') return '#ef4444'; // Red
        if (status === 'followup') return '#f59e0b'; // Amber
        return '#10b981'; // Green
    };

    return (
        <Box sx={{ display: 'flex', height: 'calc(100vh - 120px)', gap: 3, mx: 'auto' }}>

            {/* Left Pane - Patient List */}
            <Box className="glass-card" sx={{ flex: 1, display: 'flex', flexDirection: 'column', overflow: 'hidden', border: '1px solid rgba(255,255,255,0.3)', bgcolor: 'rgba(255,255,255,0.6)' }}>
                {/* Search Header */}
                <Box sx={{ p: 2, borderBottom: '1px solid rgba(0,0,0,0.05)', display: 'flex', gap: 2 }}>
                    <Box sx={{
                        flex: 1,
                        display: 'flex',
                        alignItems: 'center',
                        bgcolor: '#f3f4f6',
                        borderRadius: 2,
                        px: 2,
                        py: 1
                    }}>
                        <SearchIcon sx={{ color: '#9ca3af', mr: 1 }} />
                        <InputBase
                            placeholder="Search by name or AHP ID..."
                            sx={{ flex: 1, fontSize: '0.875rem' }}
                            value={searchQuery}
                            onChange={(e) => setSearchQuery(e.target.value)}
                        />
                    </Box>
                    <Button variant="outlined" startIcon={<FilterListIcon />} sx={{ color: '#4b5563', borderColor: '#d1d5db', textTransform: 'none' }}>
                        Filter
                    </Button>
                </Box>

                {/* List Body */}
                <List sx={{ flex: 1, overflowY: 'auto', p: 0 }}>
                    {isLoading ? (
                        <Box sx={{ p: 4, textAlign: 'center' }}>
                            <Typography color="text.secondary">Loading your patients...</Typography>
                        </Box>
                    ) : filteredPatients.map((patient) => {
                        const isRevoked = patient.access_level === 'revoked';
                        const isSelected = selectedPatientId === patient.ahp_id && !isRevoked;

                        return (
                            <Tooltip title={isRevoked ? "Access revoked by patient" : ""} placement="top" key={patient.ahp_id}>
                                <ListItem
                                    button={!isRevoked}
                                    onClick={() => !isRevoked && setSelectedPatientId(patient.ahp_id)}
                                    sx={{
                                        p: 2.5,
                                        borderBottom: '1px solid #e5e7eb',
                                        bgcolor: isSelected ? '#f0fdfa' : 'white', // light teal if selected
                                        opacity: isRevoked ? 0.4 : 1,
                                        cursor: isRevoked ? 'not-allowed' : 'pointer',
                                        '&:hover': {
                                            bgcolor: isRevoked ? 'white' : isSelected ? '#ccfbf1' : '#f9fafb'
                                        }
                                    }}
                                >
                                    {/* Status Dot */}
                                    <Box sx={{ width: 10, height: 10, borderRadius: '50%', bgcolor: '#10b981', mr: 2, flexShrink: 0 }} />

                                    {/* Avatar */}
                                    <Avatar sx={{ bgcolor: isRevoked ? '#9ca3af' : '#0d9488', width: 48, height: 48, mr: 2, fontWeight: 'bold' }}>
                                        {patient.name.split(' ').map(n => n[0]).join('')}
                                    </Avatar>

                                    {/* Details */}
                                    <Box sx={{ flex: 1 }}>
                                        <Typography variant="subtitle1" fontWeight="bold" sx={{ color: '#111827', lineHeight: 1.2 }}>
                                            {patient.name}
                                        </Typography>
                                        <Typography variant="caption" sx={{ color: '#6b7280', display: 'block', mb: 0.5 }}>
                                            AHP Patient · <span style={{ fontFamily: 'monospace' }}>{patient.ahp_id}</span>
                                        </Typography>

                                        <Box sx={{ display: 'flex', gap: 1, mt: 0.5 }}>
                                            {isRevoked ? (
                                                <Chip size="small" label="Access revoked" sx={{ bgcolor: '#e5e7eb', color: '#4b5563', height: 20, fontSize: '0.7rem' }} />
                                            ) : (
                                                <Chip size="small" label={`Access: ${patient.access_level}`} sx={{ bgcolor: '#ccfbf1', color: '#0f766e', height: 20, fontSize: '0.7rem' }} />
                                            )}
                                        </Box>
                                    </Box>

                                    {/* Date */}
                                    <Box sx={{ alignSelf: 'flex-start', textAlign: 'right' }}>
                                        <Typography variant="caption" sx={{ color: '#6b7280' }}>
                                            {new Date(patient.granted_at).toLocaleDateString()}
                                        </Typography>
                                    </Box>
                                </ListItem>
                            </Tooltip>
                        );
                    })}
                    {!isLoading && filteredPatients.length === 0 && (
                        <Box sx={{ p: 4, textAlign: 'center' }}>
                            <Typography color="text.secondary">No patients found matching your search.</Typography>
                        </Box>
                    )}
                </List>
            </Box>

            {/* Right Pane - Mini Preview */}
            <Box className="glass-card" sx={{ width: 380, flexShrink: 0, bgcolor: 'rgba(255,255,255,0.8)', border: '1px solid rgba(255,255,255,0.3)', display: 'flex', flexDirection: 'column' }}>
                {!selectedPatientData ? (
                    <Box sx={{ display: 'flex', flexDirection: 'column', alignItems: 'center', justifyContent: 'center', height: '100%', p: 4, textAlign: 'center' }}>
                        <FolderSharedIcon sx={{ fontSize: 64, color: '#e5e7eb', mb: 2 }} />
                        <Typography variant="h6" sx={{ color: '#4b5563', fontWeight: 'bold' }}>{isLoadingDetail ? "Loading profile..." : "Select a patient to view profile"}</Typography>
                        <Typography variant="body2" sx={{ color: '#9ca3af', mt: 1 }}>
                            {isLoadingDetail ? "Connecting to AHP network..." : "Click on any active patient from the list."}
                        </Typography>
                    </Box>
                ) : (
                    <>
                        <Box sx={{ p: 4, textAlign: 'center', borderBottom: '1px solid #e5e7eb' }}>
                            <Avatar sx={{ width: 80, height: 80, mx: 'auto', mb: 2, bgcolor: '#0d9488', fontSize: '2rem' }}>
                                {selectedPatientData.profile.name.split(' ').map(n => n[0]).join('')}
                            </Avatar>
                            <Typography variant="h5" fontWeight="bold" sx={{ color: '#111827' }}>{selectedPatientData.profile.name}</Typography>
                            <Box sx={{ display: 'flex', justifyContent: 'center', gap: 1, mt: 1, mb: 1 }}>
                                <Typography variant="body2" sx={{ color: '#4b5563' }}>{selectedPatientData.profile.age}yrs</Typography>
                                <Typography variant="body2" sx={{ color: '#4b5563' }}>•</Typography>
                                <Typography variant="body2" sx={{ color: '#4b5563' }}>{selectedPatientData.profile.gender}</Typography>
                            </Box>
                            <Chip label={selectedPatientData.profile.ahp_id} sx={{ fontFamily: 'monospace', bgcolor: '#f3f4f6', color: '#4b5563', fontWeight: 'bold' }} />
                        </Box>

                        <Box sx={{ p: 3, flex: 1, overflowY: 'auto' }}>
                            {/* Critical Allergies */}
                            {selectedPatientData.allergies.length > 0 && (
                                <Box sx={{ mb: 3 }}>
                                    <Box sx={{ display: 'flex', gap: 1, flexWrap: 'wrap' }}>
                                        {selectedPatientData.allergies.map(alg => (
                                            <Chip key={alg.id} label={`${alg.allergen} Allergy`} icon={<WarningIcon fontSize="small" />} sx={{ bgcolor: '#fee2e2', color: '#b91c1c', fontWeight: 'bold' }} />
                                        ))}
                                    </Box>
                                </Box>
                            )}

                            {/* Active Conditions */}
                            {selectedPatientData.conditions.length > 0 && (
                                <Box sx={{ mb: 3 }}>
                                    <Typography variant="overline" sx={{ color: '#6b7280', fontWeight: 'bold', mb: 1, display: 'block' }}>Active Conditions</Typography>
                                    <Box sx={{ display: 'flex', gap: 1, flexWrap: 'wrap' }}>
                                        {selectedPatientData.conditions.map(cond => (
                                            <Chip key={cond.id} label={cond.name} size="small" sx={{ bgcolor: '#ccfbf1', color: '#0f766e', fontWeight: 600 }} />
                                        ))}
                                    </Box>
                                </Box>
                            )}

                            {/* Current Medications */}
                            <Box sx={{ mb: 3 }}>
                                <Typography variant="overline" sx={{ color: '#6b7280', fontWeight: 'bold', mb: 1, display: 'block' }}>Current Medications</Typography>
                                {selectedPatientData.medications.length > 0 ? (
                                    selectedPatientData.medications.map(med => (
                                        <Box key={med.id} sx={{ display: 'flex', alignItems: 'center', mb: 1 }}>
                                            <MedicationIcon sx={{ color: '#9ca3af', fontSize: 20, mr: 1 }} />
                                            <Typography variant="body2" sx={{ color: '#374151', fontWeight: 500 }}>{med.generic_name} ({med.dosage})</Typography>
                                        </Box>
                                    ))
                                ) : (
                                    <Typography variant="body2" sx={{ color: '#9ca3af' }}>None recorded</Typography>
                                )}
                            </Box>
                        </Box>

                        <Box sx={{ p: 3, borderTop: '1px solid #e5e7eb', display: 'flex', flexDirection: 'column', gap: 1.5 }}>
                            <Button
                                variant="contained"
                                fullWidth
                                onClick={() => navigate(`/patient/${selectedPatientData.profile.ahp_id}`)}
                                sx={{ bgcolor: '#0d9488', '&:hover': { bgcolor: '#0f766e' }, textTransform: 'none', py: 1.2, fontWeight: 'bold' }}
                            >
                                Open Full Profile
                            </Button>
                            <Button
                                variant="outlined"
                                fullWidth
                                onClick={() => navigate('/prescriptions')}
                                startIcon={<MedicationIcon />}
                                sx={{ color: '#0d9488', borderColor: '#0d9488', textTransform: 'none', py: 1.2, fontWeight: 'bold' }}
                            >
                                Write Prescription
                            </Button>
                        </Box>
                    </>
                )}
            </Box>
        </Box>
    );
}
