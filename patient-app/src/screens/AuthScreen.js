import React, { useState } from 'react';
import {
    View, Text, StyleSheet, TextInput,
    TouchableOpacity, ActivityIndicator, Alert,
    KeyboardAvoidingView, Platform, ScrollView, Dimensions
} from 'react-native';
import { Ionicons } from '@expo/vector-icons';
import axios from 'axios';
import AsyncStorage from '@react-native-async-storage/async-storage';
import { Theme, GlobalStyles } from '../theme';
import { API_BASE_URL } from '../api';

const { width } = Dimensions.get('window');

export default function AuthScreen({ navigation }) {
    const [loginMode, setLoginMode] = useState('ahp'); // Default to AHP as per Page 3 focus
    const [loading, setLoading] = useState(false);

    // AHP flow
    const [ahpId, setAhpId] = useState('');
    const [password, setPassword] = useState('');
    const [showPassword, setShowPassword] = useState(false);

    // OTP flow
    const [phone, setPhone] = useState('');
    const [otp, setOtp] = useState('');
    const [step, setStep] = useState(1);

    const handleAhpLogin = async () => {
        const ahp = ahpId.trim().toUpperCase();
        if (!ahp.startsWith('AHP-') || ahp.length < 8) {
            return Alert.alert('Invalid AHP ID', 'Format: AHP-XXXXXX-XXX');
        }
        if (password.length < 6) {
            return Alert.alert('Password too short', 'Minimum 6 characters.');
        }

        setLoading(true);
        try {
            const resp = await axios.post(`${API_BASE_URL}/patient/login-ahp`, { ahp_id: ahp, password });
            if (resp.data.access_token) {
                await AsyncStorage.setItem('token', resp.data.access_token);
                await AsyncStorage.setItem('ahp_id', resp.data.ahp_id || '');
                navigation.replace('MainTabs');
            }
        } catch (e) {
            const errorMsg = e.response?.data?.detail || 'Invalid credentials.';
            Alert.alert('Login Failed', errorMsg);
        } finally {
            setLoading(false);
        }
    };

    return (
        <View style={GlobalStyles.screen}>
            <KeyboardAvoidingView behavior={Platform.OS === 'ios' ? 'padding' : 'height'} style={{ flex: 1 }}>

                {/* Top Nav Bar */}
                <View style={styles.topBar}>
                    <TouchableOpacity onPress={() => navigation.goBack()}>
                        <Ionicons name="arrow-back" size={24} color="#FFFFFF" />
                    </TouchableOpacity>
                    <Text style={[styles.topBarTitle]}>PATIENT LOGIN</Text>
                </View>

                <ScrollView contentContainerStyle={styles.scrollContent} keyboardShouldPersistTaps="handled">

                    <View style={styles.headerSection}>
                        <Text style={styles.bigHeading}>WELCOME BACK.</Text>
                        <View style={styles.headingDivider} />
                    </View>

                    <View style={styles.form}>
                        {/* AHP ID FIELD */}
                        <View style={styles.inputGroup}>
                            <Text style={styles.inputLabel}>AHP ID / MOBILE NUMBER</Text>
                            <View style={styles.inputWrapper}>
                                <TextInput
                                    style={styles.brutalistInput}
                                    placeholder="AHP-000000-XXX"
                                    placeholderTextColor="#333"
                                    value={ahpId}
                                    onChangeText={(t) => setAhpId(t.toUpperCase())}
                                    autoCapitalize="characters"
                                />
                            </View>
                        </View>

                        {/* PASSWORD FIELD */}
                        <View style={styles.inputGroup}>
                            <Text style={styles.inputLabel}>PASSWORD</Text>
                            <View style={[styles.inputWrapper, { flexDirection: 'row', alignItems: 'center' }]}>
                                <TextInput
                                    style={[styles.brutalistInput, { flex: 1 }]}
                                    placeholder="••••••••"
                                    placeholderTextColor="#333"
                                    value={password}
                                    onChangeText={setPassword}
                                    secureTextEntry={!showPassword}
                                />
                                <TouchableOpacity onPress={() => setShowPassword(!showPassword)} style={{ paddingRight: 15 }}>
                                    <Ionicons name={showPassword ? "eye-off" : "eye"} size={20} color="#555" />
                                </TouchableOpacity>
                            </View>
                        </View>

                        {/* SIGN IN BUTTON */}
                        <TouchableOpacity
                            style={styles.signInButton}
                            onPress={handleAhpLogin}
                            disabled={loading}
                        >
                            {loading ? (
                                <ActivityIndicator color="#000" />
                            ) : (
                                <Text style={styles.signInButtonText}>SIGN IN</Text>
                            )}
                        </TouchableOpacity>
                    </View>

                    {/* Footer Links */}
                    <TouchableOpacity
                        style={styles.footerLink}
                        onPress={() => navigation.navigate('Register')}
                    >
                        <Text style={styles.footerLinkText}>NEW PATIENT? REGISTER →</Text>
                    </TouchableOpacity>

                </ScrollView>
            </KeyboardAvoidingView>
        </View>
    );
}

const styles = StyleSheet.create({
    topBar: {
        flexDirection: 'row',
        alignItems: 'center',
        paddingTop: 60,
        paddingHorizontal: 30,
        gap: 20,
    },
    topBarTitle: {
        fontFamily: Theme.fonts.label,
        color: Theme.colors.secondary,
        fontSize: 12,
        letterSpacing: 2,
    },
    scrollContent: {
        paddingHorizontal: 30,
        paddingTop: 40,
        paddingBottom: 40,
    },
    headerSection: {
        marginBottom: 50,
    },
    bigHeading: {
        fontFamily: Theme.fonts.heading,
        color: Theme.colors.primary,
        fontSize: 36,
        letterSpacing: -1,
    },
    headingDivider: {
        height: 2,
        backgroundColor: '#FFFFFF',
        width: '100%',
        marginTop: 10,
    },
    form: {
        gap: 30,
    },
    inputGroup: {
        gap: 8,
    },
    inputLabel: {
        fontFamily: Theme.fonts.label,
        color: Theme.colors.secondary,
        fontSize: 10,
        letterSpacing: 1,
    },
    inputWrapper: {
        borderWidth: 1,
        borderColor: '#FFFFFF',
        height: 60,
        borderRadius: 0,
        backgroundColor: '#000000',
    },
    brutalistInput: {
        flex: 1,
        paddingHorizontal: 15,
        color: '#FFFFFF',
        fontFamily: Theme.fonts.body,
        fontSize: 16,
    },
    signInButton: {
        backgroundColor: '#FFFFFF',
        height: 60,
        alignItems: 'center',
        justifyContent: 'center',
        marginTop: 10,
    },
    signInButtonText: {
        fontFamily: Theme.fonts.headingSemi,
        color: '#000000',
        fontSize: 18,
        letterSpacing: 2,
    },
    footerLink: {
        marginTop: 60,
        alignItems: 'center',
    },
    footerLinkText: {
        fontFamily: Theme.fonts.label,
        color: Theme.colors.secondary,
        fontSize: 12,
        letterSpacing: 1,
    }
});
