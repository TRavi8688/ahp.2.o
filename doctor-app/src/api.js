// Central API configuration for Doctor App
const PORT = '8000';

// On web (React), we use the current hostname
export const API_BASE_URL = `http://${window.location.hostname}:${PORT}`;
export const WS_BASE_URL = `ws://${window.location.hostname}:${PORT}`;

console.log(`[Doctor Config] API Base URL: ${API_BASE_URL}`);
