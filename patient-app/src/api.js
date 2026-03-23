import { Platform } from 'react-native';

// --- API CONFIGURATION ---
export const USE_MOCK_API = false;

// In unified deployment: API is on the same domain, so relative URL works
const FULL_BASE_URL = process.env.EXPO_PUBLIC_API_BASE_URL;

export const API_BASE_URL = FULL_BASE_URL 
    ? `${FULL_BASE_URL}/api/v1`
    : "/api/v1";

export const WS_BASE_URL = FULL_BASE_URL
    ? FULL_BASE_URL.replace(/^http/, 'ws')
    : (typeof window !== 'undefined' ? `${window.location.protocol === 'https:' ? 'wss:' : 'ws:'}//${window.location.host}` : 'ws://localhost:8000');

console.log(`[Patient Config] API Base URL: ${API_BASE_URL}`);
