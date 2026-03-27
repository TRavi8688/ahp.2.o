import { Platform } from 'react-native';

// --- PRODUCTION-FIRST API CONFIGURATION ---
const FALLBACK_PROD_URL = "https://api.mulajna.com"; // Replace with real domain when live

// Priority: Env Variable > Web Location > Hardcoded Prod Fallback
const getBaseUrl = () => {
    if (process.env.EXPO_PUBLIC_API_BASE_URL) return process.env.EXPO_PUBLIC_API_BASE_URL;
    
    if (Platform.OS === 'web') {
        const { protocol, host } = window.location;
        return `${protocol}//${host}`;
    }

    return FALLBACK_PROD_URL;
};

const BASE = getBaseUrl();

export const API_BASE_URL = `${BASE}/api/v1`;

export const WS_BASE_URL = BASE.startsWith('https') 
    ? BASE.replace('https', 'wss') 
    : BASE.replace('http', 'ws');

console.log(`[Mulajna Network] Core Endpoint: ${API_BASE_URL}`);
