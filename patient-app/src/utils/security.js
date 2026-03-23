import AsyncStorage from '@react-native-async-storage/async-storage';
import * as LocalAuthentication from 'expo-local-authentication';
import * as ScreenCapture from 'expo-screen-capture';
import { Alert, Platform } from 'react-native';

const TOKEN_KEY = 'token'; 
const AHP_ID_KEY = 'ahp_id';
const BIOMETRIC_ENABLED_KEY = 'biometric_enabled';

export const SecurityUtils = {
    // --- Token Management (Unified using AsyncStorage) ---
    async saveToken(token) {
        try {
            await AsyncStorage.setItem(TOKEN_KEY, token);
        } catch (e) {
            console.error('Storage Error:', e);
        }
    },

    async getToken() {
        try {
            return await AsyncStorage.getItem(TOKEN_KEY);
        } catch (e) {
            console.error('Storage Error:', e);
            return null;
        }
    },

    async deleteToken() {
        try {
            await AsyncStorage.removeItem(TOKEN_KEY);
        } catch (e) {
            console.error('Storage Error:', e);
        }
    },

    async saveAhpId(id) {
        try {
            await AsyncStorage.setItem(AHP_ID_KEY, id);
        } catch (e) {
            console.error('Storage Error:', e);
        }
    },

    async getAhpId() {
        try {
            return await AsyncStorage.getItem(AHP_ID_KEY);
        } catch (e) {
            console.error('Storage Error:', e);
            return null;
        }
    },

    // --- Biometric Authentication ---
    async isBiometricAvailable() {
        const hasHardware = await LocalAuthentication.hasHardwareAsync();
        const isEnrolled = await LocalAuthentication.isEnrolledAsync();
        return hasHardware && isEnrolled;
    },

    async authenticateWithBiometrics() {
        try {
            const available = await this.isBiometricAvailable();
            if (!available) return false;

            const result = await LocalAuthentication.authenticateAsync({
                promptMessage: 'Authenticate to access Mulajna',
                fallbackLabel: 'Enter Passcode',
                disableDeviceFallback: false,
            });

            return result.success;
        } catch (e) {
            console.error('Biometric Error:', e);
            return false;
        }
    },

    // --- Screenshot Prevention ---
    async enableScreenshotProtection() {
        if (Platform.OS === 'android') {
            await ScreenCapture.preventScreenCaptureAsync();
        } else if (Platform.OS === 'ios') {
            // iOS doesn't support blocking screenshots, but we can detect them
            // In a real app, you would add a listener here to warn or obscure the UI
        }
    },

    async disableScreenshotProtection() {
        if (Platform.OS === 'android') {
            await ScreenCapture.allowScreenCaptureAsync();
        }
    }
};
