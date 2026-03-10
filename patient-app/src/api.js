import { Platform } from 'react-native';

const DEV_IP = '192.168.0.20';
const PORT = '8000';

// For web, we use the current hostname (works for localhost OR IP)
// For mobile, we use the workstation IP.
export const API_BASE_URL = Platform.OS === 'web'
    ? `http://${typeof window !== 'undefined' ? window.location.hostname : 'localhost'}:${PORT}`
    : `http://${DEV_IP}:${PORT}`;

export const WS_BASE_URL = Platform.OS === 'web'
    ? `ws://${typeof window !== 'undefined' ? window.location.hostname : 'localhost'}:${PORT}`
    : `ws://${DEV_IP}:${PORT}`;

console.log(`[Config] API Base URL: ${API_BASE_URL}`);
console.log(`[Config] WS Base URL: ${WS_BASE_URL}`);
