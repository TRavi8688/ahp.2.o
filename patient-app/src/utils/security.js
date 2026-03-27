import * as SecureStore from 'expo-secure-store';
import * as LocalAuthentication from 'expo-local-authentication';
import * as ScreenCapture from 'expo-screen-capture';
import { Alert, Platform } from 'react-native';

const TOKEN_KEY = 'mulajna_auth_token'; 
const AHP_ID_KEY = 'mulajna_ahp_id';

export const SecurityUtils = {
    // --- Secure Token Management ---
    async saveToken(token) {
        try {
            await SecureStore.setItemAsync(TOKEN_KEY, token);
        } catch (e) {
            console.error('[Security] Save Error:', e);
        }
    },

    async getToken() {
        try {
            return await SecureStore.getItemAsync(TOKEN_KEY);
        } catch (e) {
            console.error('[Security] Fetch Error:', e);
            return null;
        }
    },

    async deleteToken() {
        try {
            await SecureStore.deleteItemAsync(TOKEN_KEY);
        } catch (e) {
            console.error('[Security] Delete Error:', e);
        }
    },

    async saveAhpId(id) {
        try {
            await SecureStore.setItemAsync(AHP_ID_KEY, id);
        } catch (e) {
            console.error('[Security] ID Save Error:', e);
        }
    },

    async getAhpId() {
        try {
            return await SecureStore.getItemAsync(AHP_ID_KEY);
        } catch (e) {
            return null;
        }
    },

    // --- Biometric Authentication (100M User Standard) ---
    async isBiometricAvailable() {
        const hasHardware = await LocalAuthentication.hasHardwareAsync();
        const isEnrolled = await LocalAuthentication.isEnrolledAsync();
        const supportedTypes = await LocalAuthentication.supportedAuthenticationTypesAsync();
        return hasHardware && isEnrolled && supportedTypes.length > 0;
    },

    async authenticateWithBiometrics() {
        try {
            const available = await this.isBiometricAvailable();
            if (!available) return false;

            const result = await LocalAuthentication.authenticateAsync({
                promptMessage: 'Secure Access to Mulajna',
                fallbackLabel: 'Use Device Passcode',
                cancelLabel: 'Cancel',
                disableDeviceFallback: false,
            });

            return result.success;
        } catch (e) {
            console.error('[Security] Biometric critical failure:', e);
            return false;
        }
    },

    // --- Data Protection (Anti-Leak) ---
    async enableScreenshotProtection() {
        try {
            if (Platform.OS === 'android') {
                await ScreenCapture.preventScreenCaptureAsync();
            } else if (Platform.OS === 'ios') {
                // For iOS, we use a listener in the screen component to blur content
                // This utility just ensures the system-level flag is recognized
                await ScreenCapture.preventScreenCaptureAsync(); 
            }
        } catch (e) {
            console.warn('[Security] Protection suppressed:', e);
        }
    },

    async disableScreenshotProtection() {
        try {
            await ScreenCapture.allowScreenCaptureAsync();
        } catch (e) {
            // Silently ignore
        }
    }
};
