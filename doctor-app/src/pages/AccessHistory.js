import React, { useState } from 'react';
import { Box, Typography, Tabs, Tab, Table, TableBody, TableCell, TableContainer, TableHead, TableRow, Paper, Chip, Button } from '@mui/material';

export default function AccessHistory() {
    const [tabIndex, setTabIndex] = useState(0);
    const [records, setRecords] = useState([]);
    const [isLoading, setIsLoading] = useState(true);

    React.useEffect(() => {
        const fetchRecords = async () => {
            try {
                const response = await fetch('http://localhost:8000/doctor/access-history', {
                    headers: {
                        'Authorization': `Bearer ${localStorage.getItem('token')}`
                    }
                });
                if (response.ok) {
                    const data = await response.json();
                    setRecords(data);
                }
            } catch (error) {
                console.error("Failed to fetch access history", error);
            } finally {
                setIsLoading(false);
            }
        };
        fetchRecords();
    }, []);

    const handleTabChange = (event, newValue) => {
        setTabIndex(newValue);
    };

    const getFilteredRecords = () => {
        if (tabIndex === 0) return records;
        const types = ['all', 'lab', 'rx', 'discharge', 'imaging'];
        return records.filter(r => r.typeRaw === types[tabIndex]);
    };

    const getTypeColor = (type) => {
        // Fallback for types that might not match exactly
        if (!type) return { bg: '#f3f4f6', color: '#4b5563' };

        switch (type.toLowerCase()) {
            case 'lab': return { bg: '#ccfbf1', color: '#0f766e' };
            case 'rx':
            case 'prescription': return { bg: '#dcfce7', color: '#15803d' };
            case 'discharge': return { bg: '#fef3c7', color: '#b45309' };
            case 'imaging':
            case 'radiology': return { bg: '#dbeafe', color: '#1d4ed8' };
            default: return { bg: '#f3f4f6', color: '#4b5563' };
        }
    };

    return (
        <Box sx={{ maxWidth: 1400, mx: 'auto' }}>
            {/* Header */}
            <Box sx={{ mb: 3 }}>
                <Typography variant="h4" fontWeight="bold" sx={{ color: '#1f2937' }}>
                    Records Shared
                </Typography>
                <Typography variant="body1" sx={{ color: '#6b7280', mt: 0.5 }}>
                    Medical files explicitly shared by patients with this clinic.
                </Typography>
            </Box>

            {/* Filter Tab Strip */}
            <Box sx={{ borderBottom: 1, borderColor: 'divider', mb: 4 }}>
                <Tabs value={tabIndex} onChange={handleTabChange} TabIndicatorProps={{ sx: { bgcolor: '#0d9488' } }}>
                    <Tab label="All Records" sx={{ fontWeight: 'bold', '&.Mui-selected': { color: '#0d9488' } }} />
                    <Tab label="Lab Reports" sx={{ fontWeight: 'bold', '&.Mui-selected': { color: '#0d9488' } }} />
                    <Tab label="Prescriptions" sx={{ fontWeight: 'bold', '&.Mui-selected': { color: '#0d9488' } }} />
                    <Tab label="Discharge" sx={{ fontWeight: 'bold', '&.Mui-selected': { color: '#0d9488' } }} />
                    <Tab label="Imaging" sx={{ fontWeight: 'bold', '&.Mui-selected': { color: '#0d9488' } }} />
                </Tabs>
            </Box>

            {/* Records Table */}
            <TableContainer component={Paper} elevation={0} sx={{ border: '1px solid #e5e7eb', borderRadius: 2 }}>
                <Table>
                    <TableHead sx={{ bgcolor: '#f9fafb' }}>
                        <TableRow>
                            <TableCell sx={{ fontWeight: 'bold', color: '#4b5563', width: '20%' }}>Patient</TableCell>
                            <TableCell sx={{ fontWeight: 'bold', color: '#4b5563', width: '15%' }}>Record Type</TableCell>
                            <TableCell sx={{ fontWeight: 'bold', color: '#4b5563', width: '35%' }}>AI Summary</TableCell>
                            <TableCell sx={{ fontWeight: 'bold', color: '#4b5563', width: '10%' }}>Date</TableCell>
                            <TableCell sx={{ fontWeight: 'bold', color: '#4b5563', width: '10%' }}>Status</TableCell>
                            <TableCell align="right" sx={{ fontWeight: 'bold', color: '#4b5563', width: '10%' }}>Action</TableCell>
                        </TableRow>
                    </TableHead>
                    <TableBody>
                        {getFilteredRecords().map((row) => {
                            const isRevoked = row.status === 'revoked';
                            const tColor = getTypeColor(row.typeRaw);
                            return (
                                <TableRow key={row.id} sx={{ '&:last-child td, &:last-child th': { border: 0 }, bgcolor: isRevoked ? '#f9fafb' : 'white', opacity: isRevoked ? 0.6 : 1 }}>

                                    {/* Patient */}
                                    <TableCell>
                                        <Typography variant="subtitle2" fontWeight="bold" sx={{ color: '#111827' }}>{row.patient_name}</Typography>
                                        <Typography variant="caption" sx={{ fontFamily: 'monospace', color: '#6b7280' }}>{row.ahp_id}</Typography>
                                    </TableCell>

                                    {/* Record Type */}
                                    <TableCell>
                                        <Chip label={row.type} size="small" sx={{ bgcolor: tColor.bg, color: tColor.color, fontWeight: 'bold' }} />
                                    </TableCell>

                                    {/* AI Summary */}
                                    <TableCell>
                                        <Typography variant="body2" sx={{ color: isRevoked ? '#ef4444' : '#374151', fontStyle: isRevoked ? 'italic' : 'normal', fontWeight: isRevoked ? 'bold' : 'normal' }}>
                                            {row.ai_summary}
                                        </Typography>
                                    </TableCell>

                                    {/* Date */}
                                    <TableCell>
                                        <Typography variant="body2" sx={{ fontFamily: 'monospace', color: '#4b5563' }}>{row.date}</Typography>
                                    </TableCell>

                                    {/* Status */}
                                    <TableCell>
                                        <Chip
                                            label={isRevoked ? "Revoked" : "Active consent"}
                                            size="small"
                                            sx={{
                                                bgcolor: isRevoked ? '#fee2e2' : '#dcfce7',
                                                color: isRevoked ? '#b91c1c' : '#15803d',
                                                fontWeight: 'bold',
                                                border: `1px solid ${isRevoked ? '#fca5a5' : '#86efac'}`
                                            }}
                                        />
                                    </TableCell>

                                    {/* Action */}
                                    <TableCell align="right">
                                        <Button
                                            variant="outlined"
                                            size="small"
                                            disabled={isRevoked}
                                            sx={{ color: '#0d9488', borderColor: '#0d9488', textTransform: 'none', fontWeight: 'bold', '&:disabled': { borderColor: '#d1d5db' } }}
                                        >
                                            View
                                        </Button>
                                    </TableCell>

                                </TableRow>
                            );
                        })}
                        {getFilteredRecords().length === 0 && (
                            <TableRow>
                                <TableCell colSpan={6} align="center" sx={{ py: 4 }}>
                                    <Typography variant="body1" sx={{ color: '#6b7280' }}>No records found in this category.</Typography>
                                </TableCell>
                            </TableRow>
                        )}
                    </TableBody>
                </Table>
            </TableContainer>

        </Box>
    );
}
