import { Platform } from 'react-native';
import axios from 'axios';

// --- OFFLINE DEVELOPMENT TOGGLE ---
// Set this to true to work on the UI/Logic without a running backend.
export const USE_MOCK_API = true;

const DEV_IP = '192.168.0.20';
const PORT = '8000';

export const API_BASE_URL = Platform.OS === 'web'
    ? `http://${typeof window !== 'undefined' ? window.location.hostname : 'localhost'}:${PORT}`
    : `http://${DEV_IP}:${PORT}`;

export const WS_BASE_URL = Platform.OS === 'web'
    ? `ws://${typeof window !== 'undefined' ? window.location.hostname : 'localhost'}:${PORT}`
    : `ws://${DEV_IP}:${PORT}`;

// --- MOCK DATA ENGINE ---
const MOCK_DATA = {
    '/patient/login-ahp': {
        access_token: 'mock_token_ext_123',
        ahp_id: 'AHP-9988-X',
        role: 'patient'
    },
    '/auth/login': {
        access_token: 'mock_token_123',
        refresh_token: 'mock_refresh_456',
        user: { first_name: 'John', last_name: 'Doe', role: 'patient' }
    },
    '/patient/dashboard': {
        patient: { first_name: 'John', ahp_id: 'AHP-9988-X' },
        summary: {
            overall: "Your health is stable. Blood pressure is within normal ranges.",
            conditions: ["Type 2 Diabetes", "Hypertension"],
            medications: ["Metformin 500mg", "Amlodipine 5mg"]
        },
        recent_vitals: [
            { type: 'BP', value: '120/80', date: '2026-03-10' },
            { type: 'Glucose', value: '95 mg/dL', date: '2026-03-09' }
        ],
        alerts: [
            { type: 'info', message: 'Annual checkup due in 5 days.' }
        ]
    },
    '/patient/records': [
        { id: 1, type: 'Document', title: 'Blood Report', date: '2026-03-05', ai_summary: 'Overall healthy.' },
        { id: 2, type: 'Scan', title: 'Chest X-Ray', date: '2026-02-20', ai_summary: 'Clear lungs.' }
    ]
};

// --- AXIOS GLOBAL MOCK INTERCEPTOR ---
if (USE_MOCK_API) {
    axios.interceptors.request.use(async (config) => {
        // Intercept all API calls
        if (config.url.startsWith(API_BASE_URL) || config.url.includes('/api/v1')) {
            console.log(`[Mock Interceptor] Intercepting: ${config.url}`);

            // Find matching data
            let match = { status: 'success', data: {} };
            for (const path in MOCK_DATA) {
                if (config.url.includes(path)) {
                    match = MOCK_DATA[path];
                    break;
                }
            }

            // Return a resolved promise that looks like an axios response
            return Promise.reject({
                isMock: true,
                response: {
                    data: match,
                    status: 200,
                    statusText: 'OK',
                    headers: {},
                    config: config
                }
            });
        }
        return config;
    });

    // Handle the "rejection" which is our mock data
    axios.interceptors.response.use(
        (response) => response,
        (error) => {
            if (error.isMock) {
                return Promise.resolve(error.response);
            }
            return Promise.reject(error);
        }
    );
}

console.log(`[Config] Isolated Mode: ${USE_MOCK_API ? 'ENABLED (Global Mocking active)' : 'DISABLED'}`);
