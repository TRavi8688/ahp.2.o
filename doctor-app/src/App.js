import React, { useState } from 'react';
import { Route, Routes, Navigate } from 'react-router-dom';
import { Box, CssBaseline, ThemeProvider, createTheme } from '@mui/material';

// Components
import Sidebar from './components/Sidebar';
import Topbar from './components/Topbar';
import ScanModal from './components/ScanModal';

// Pages
import LoginScreen from './pages/LoginScreen';
import SignupScreen from './pages/SignupScreen';
import HomeDashboard from './pages/HomeDashboard';
import PatientDetailView from './pages/PatientDetailView';
import PatientList from './pages/PatientList';
import AccessHistory from './pages/AccessHistory';
import Alerts from './pages/Alerts';
import Settings from './pages/Settings';
import Schedule from './pages/Schedule';
import Prescriptions from './pages/Prescriptions';
import Analytics from './pages/Analytics';

const theme = createTheme({
    palette: {
        primary: { main: '#4C1D95' }, // Deep Indigo
        secondary: { main: '#0D9488' }, // Surgical Teal
        warning: { main: '#F59E0B' }, // Sunset Amber (Guardian)
        background: {
            default: '#1E1B4B', // Dark Deep Indigo
            paper: 'rgba(255, 255, 255, 0.7)' // Glass Effect Placeholder
        },
        text: {
            primary: '#1e293b',
            secondary: '#64748b'
        }
    },
    typography: {
        fontFamily: '"Inter", "Outfit", sans-serif',
        h1: { fontFamily: '"Outfit", sans-serif', fontWeight: 700 },
        h2: { fontFamily: '"Outfit", sans-serif', fontWeight: 700 },
        h3: { fontFamily: '"Outfit", sans-serif', fontWeight: 600 },
        button: { textTransform: 'none', fontWeight: 600 }
    },
    components: {
        MuiCssBaseline: {
            styleOverrides: {
                body: {
                    backgroundColor: '#1E1B4B',
                    backgroundImage: 'radial-gradient(circle at top right, #4C1D95, #1E1B4B)',
                    backgroundAttachment: 'fixed',
                    minHeight: '100vh',
                },
                '.glass-card': {
                    background: 'rgba(255, 255, 255, 0.7)',
                    backdropFilter: 'blur(12px)',
                    WebkitBackdropFilter: 'blur(12px)',
                    border: '1px solid rgba(255, 255, 255, 0.3)',
                    boxShadow: '0 8px 32px 0 rgba(31, 38, 135, 0.37)',
                    borderRadius: '24px',
                }
            }
        },
        MuiPaper: {
            styleOverrides: {
                root: {
                    borderRadius: '24px',
                    boxShadow: '0 8px 32px 0 rgba(0, 0, 0, 0.08)',
                }
            }
        }
    }
});

function App() {
    // Use localStorage to mock authentication state for the UI build
    const isAuthenticated = localStorage.getItem('isAuthenticated') === 'true';
    const isVerified = localStorage.getItem('isVerified') === 'true';

    const [scanModalOpen, setScanModalOpen] = useState(false);

    const handleLogout = () => {
        localStorage.removeItem('isAuthenticated');
        localStorage.removeItem('isVerified');
        localStorage.removeItem('token');
        window.location.href = '/login';
    };

    if (!isAuthenticated) {
        return (
            <ThemeProvider theme={theme}>
                <CssBaseline />
                <Routes>
                    <Route path="/login" element={<LoginScreen />} />
                    <Route path="/verify" element={<SignupScreen />} />
                    <Route path="*" element={<Navigate to="/login" replace />} />
                </Routes>
            </ThemeProvider>
        );
    }

    // Authenticated & Verified Layout
    return (
        <ThemeProvider theme={theme}>
            <CssBaseline />
            <Box sx={{ display: 'flex', height: '100vh', overflow: 'hidden' }}>
                <Sidebar onOpenScan={() => setScanModalOpen(true)} />
                <Box sx={{ flexGrow: 1, display: 'flex', flexDirection: 'column', overflow: 'hidden' }}>
                    <Topbar onLogout={handleLogout} onOpenScan={() => setScanModalOpen(true)} />
                    <Box component="main" sx={{ flexGrow: 1, p: 3, overflow: 'auto' }}>
                        <Routes>
                            <Route path="/" element={<HomeDashboard onOpenScan={() => setScanModalOpen(true)} />} />
                            <Route path="/patient/:id/*" element={<PatientDetailView />} />
                            <Route path="/patients" element={<PatientList />} />
                            <Route path="/schedule" element={<Schedule />} />
                            <Route path="/prescriptions" element={<Prescriptions />} />
                            <Route path="/history" element={<AccessHistory />} />
                            <Route path="/analytics" element={<Analytics />} />
                            <Route path="/alerts" element={<Alerts />} />
                            <Route path="/settings" element={<Settings />} />
                            <Route path="*" element={<Navigate to="/" replace />} />
                        </Routes>
                    </Box>
                </Box>
            </Box>

            <ScanModal open={scanModalOpen} onClose={() => setScanModalOpen(false)} />
        </ThemeProvider>
    );
}

export default App;
