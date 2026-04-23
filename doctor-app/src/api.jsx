// Central API configuration for Doctor App
// In unified deployment: API is on the same domain, so relative URL works perfectly
const BACKEND_URL = import.meta.env.VITE_API_BASE_URL || "";
export const API_BASE_URL = BACKEND_URL ? `${BACKEND_URL}/api/v1` : "/api/v1";
export const WS_BASE_URL = import.meta.env.VITE_WS_BASE_URL || 
    (typeof window !== 'undefined' ? `${window.location.protocol === 'https:' ? 'wss:' : 'ws:'}//${window.location.host}` : 'ws://localhost:8000');

console.log(`[Doctor Config] API Base URL: ${API_BASE_URL}`);
