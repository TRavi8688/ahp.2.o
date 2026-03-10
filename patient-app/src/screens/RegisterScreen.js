import React, { useState } from 'react';
import {
    View, Text, StyleSheet, TextInput,
    TouchableOpacity, ActivityIndicator, Alert,
    KeyboardAvoidingView, Platform, ScrollView
} from 'react-native';
import { LinearGradient } from 'expo-linear-gradient';
import { Ionicons } from '@expo/vector-icons';
import axios from 'axios';
import AsyncStorage from '@react-native-async-storage/async-storage';

import { API_BASE_URL } from '../api';

export default function RegisterScreen({ navigation }) {
    const [loading, setLoading] = useState(false);
    const [formData, setFormData] = useState({
        fullName: '',
        age: '',
        gender: '',
        bloodGroup: '',
        phone: '',
        password: '',
        confirmPassword: ''
    });
    const [otp, setOtp] = useState('');
    const [step, setStep] = useState(1); // 1: Details, 2: OTP

    const handleNext = async () => {
        const { fullName, age, phone, password, confirmPassword } = formData;
        if (!fullName || !age || !phone || !password || !confirmPassword) return Alert.alert('Missing Info', 'Please fill in all details including password.');
        if (phone.length < 10) return Alert.alert('Invalid Phone', 'Please enter a valid 10-digit phone number.');
        if (password.length < 6) return Alert.alert('Password too short', 'Password must be at least 6 characters.');
        if (password !== confirmPassword) return Alert.alert('Mismatch', 'Passwords do not match.');

        setLoading(true);
        try {
            // Instant Check for already registered users
            const checkResp = await axios.get(`${API_BASE_URL}/auth/check-user?identifier=${phone}`);
            if (checkResp.data.exists) {
                setLoading(false);
                return Alert.alert(
                    'Already Registered',
                    'This phone number is already linked to an account. Please login instead.',
                    [{ text: 'Go to Login', onPress: () => navigation.navigate('Login') }, { text: 'Change Number', style: 'cancel' }]
                );
            }

            // If new, send OTP
            await axios.post(`${API_BASE_URL}/send-otp`, { identifier: phone, country_code: '+91' });
            setStep(2);
        } catch (err) {
            console.error(err);
            Alert.alert('Error', 'Something went wrong. Please try again.');
        } finally { setLoading(false); }
    };

    const handleVerifyOtp = async () => {
        if (!otp) return Alert.alert('Enter OTP', 'Please enter the 6-digit code sent to your phone.');
        setLoading(true);
        try {
            const resp = await axios.post(`${API_BASE_URL}/verify-otp`, { identifier: formData.phone, otp });
            const { access_token } = resp.data;

            // Immediately complete profile setup
            const names = formData.fullName.split(" ");
            const firstName = names[0] || "Unknown";
            const lastName = names.length > 1 ? names.slice(1).join(" ") : "";

            const setupPayload = {
                phone_number: formData.phone,
                first_name: firstName,
                last_name: lastName,
                date_of_birth: formData.age,
                gender: formData.gender || "Unknown",
                blood_group: formData.bloodGroup || "Unknown",
                password: formData.password,
                conditions: [],
                medications: []
            };

            const setupResp = await axios.post(`${API_BASE_URL}/profile/setup`, setupPayload, {
                headers: { Authorization: `Bearer ${access_token}` }
            });

            const ahp_id = setupResp.data.ahp_id;
            await AsyncStorage.setItem('token', access_token);
            await AsyncStorage.setItem('ahp_id', ahp_id);

            // Navigate to Success Screen instead of Main Dashboard
            navigation.replace('RegistrationSuccess', { ahp_id, fullName: formData.fullName });

        } catch (err) {
            console.error(err);
            Alert.alert('Verification Failed', 'Incorrect OTP. Try 000000.');
        } finally { setLoading(false); }
    };

    return (
        <LinearGradient colors={['#4c1d95', '#1e1b4b']} style={styles.container}>
            <KeyboardAvoidingView behavior={Platform.OS === 'ios' ? 'padding' : 'height'} style={{ flex: 1 }}>
                <ScrollView contentContainerStyle={styles.content} keyboardShouldPersistTaps="handled">

                    {/* Welcome Section */}
                    <View style={styles.welcomeContainer}>
                        <View style={styles.logoIcon}>
                            <Ionicons name="sparkles-outline" size={40} color="#fff" />
                        </View>
                        <Text style={styles.title}>Join ELEX.AI</Text>
                        <Text style={styles.subtitle}>Create your AI Health Passport in seconds.</Text>
                    </View>

                    <View style={styles.card}>
                        <Text style={styles.cardTitle}>{step === 1 ? 'Basic Details' : 'Verify Phone'}</Text>

                        {step === 1 ? (
                            <>
                                <View style={styles.inputBox}>
                                    <Ionicons name="person-outline" size={20} color="#666" style={styles.inputIcon} />
                                    <TextInput
                                        style={styles.input}
                                        placeholder="Full Name"
                                        value={formData.fullName}
                                        onChangeText={(v) => setFormData({ ...formData, fullName: v })}
                                        placeholderTextColor="#aaa"
                                    />
                                </View>
                                <View style={{ flexDirection: 'row', gap: 10 }}>
                                    <View style={[styles.inputBox, { flex: 1 }]}>
                                        <TextInput
                                            style={styles.input}
                                            placeholder="Age"
                                            value={formData.age}
                                            onChangeText={(v) => setFormData({ ...formData, age: v })}
                                            keyboardType="number-pad"
                                            placeholderTextColor="#aaa"
                                        />
                                    </View>
                                    <View style={[styles.inputBox, { flex: 1 }]}>
                                        <TextInput
                                            style={styles.input}
                                            placeholder="Gender (M/F)"
                                            value={formData.gender}
                                            onChangeText={(v) => setFormData({ ...formData, gender: v })}
                                            placeholderTextColor="#aaa"
                                        />
                                    </View>
                                </View>
                                <View style={styles.inputBox}>
                                    <Ionicons name="water-outline" size={20} color="#666" style={styles.inputIcon} />
                                    <TextInput
                                        style={styles.input}
                                        placeholder="Blood Group (e.g. O+)"
                                        value={formData.bloodGroup}
                                        onChangeText={(v) => setFormData({ ...formData, bloodGroup: v })}
                                        placeholderTextColor="#aaa"
                                    />
                                </View>
                                <View style={styles.inputBox}>
                                    <Ionicons name="call-outline" size={20} color="#666" style={styles.inputIcon} />
                                    <TextInput
                                        style={styles.input}
                                        placeholder="Phone Number"
                                        value={formData.phone}
                                        onChangeText={(v) => setFormData({ ...formData, phone: v })}
                                        keyboardType="phone-pad"
                                        maxLength={10}
                                        placeholderTextColor="#aaa"
                                    />
                                </View>
                                <View style={styles.inputBox}>
                                    <Ionicons name="lock-closed-outline" size={20} color="#666" style={styles.inputIcon} />
                                    <TextInput
                                        style={styles.input}
                                        placeholder="Set Password (min 6 chars)"
                                        value={formData.password}
                                        onChangeText={(v) => setFormData({ ...formData, password: v })}
                                        secureTextEntry
                                        placeholderTextColor="#aaa"
                                    />
                                </View>
                                <View style={styles.inputBox}>
                                    <Ionicons name="lock-closed-outline" size={20} color="#666" style={styles.inputIcon} />
                                    <TextInput
                                        style={styles.input}
                                        placeholder="Confirm Password"
                                        value={formData.confirmPassword}
                                        onChangeText={(v) => setFormData({ ...formData, confirmPassword: v })}
                                        secureTextEntry
                                        placeholderTextColor="#aaa"
                                    />
                                </View>
                            </>
                        ) : (
                            <View style={styles.inputBox}>
                                <Ionicons name="key-outline" size={20} color="#666" style={styles.inputIcon} />
                                <TextInput
                                    style={styles.input}
                                    placeholder="Enter 6-digit OTP"
                                    value={otp}
                                    onChangeText={setOtp}
                                    keyboardType="number-pad"
                                    maxLength={6}
                                    placeholderTextColor="#aaa"
                                />
                            </View>
                        )}

                        <TouchableOpacity
                            style={[styles.button, loading && styles.buttonDisabled]}
                            onPress={step === 1 ? handleNext : handleVerifyOtp}
                            disabled={loading}
                        >
                            {loading
                                ? <ActivityIndicator color="#fff" />
                                : <>
                                    <Text style={styles.buttonText}>{step === 1 ? 'Next' : 'Verify & Finish'}</Text>
                                    <Ionicons name="arrow-forward" size={20} color="#fff" style={{ marginLeft: 10 }} />
                                </>
                            }
                        </TouchableOpacity>

                        <TouchableOpacity onPress={() => navigation.navigate('Login')} style={styles.loginLink}>
                            <Text style={styles.loginLinkText}>Already have an account? <Text style={{ fontWeight: 'bold' }}>Login</Text></Text>
                        </TouchableOpacity>
                    </View>

                    <Text style={styles.footerText}>Secure • Private • ELEX.AI</Text>
                </ScrollView>
            </KeyboardAvoidingView>
        </LinearGradient>
    );
}

const styles = StyleSheet.create({
    container: { flex: 1 },
    content: {
        flexGrow: 1,
        padding: 24,
        justifyContent: 'center',
        alignItems: 'center',
    },
    welcomeContainer: {
        alignItems: 'center',
        marginBottom: 20,
    },
    logoIcon: {
        width: 70,
        height: 70,
        borderRadius: 22,
        backgroundColor: 'rgba(255,255,255,0.2)',
        justifyContent: 'center',
        alignItems: 'center',
        marginBottom: 15,
    },
    title: {
        color: '#fff',
        fontSize: 28,
        fontWeight: '900',
        letterSpacing: 1,
    },
    subtitle: {
        color: '#ddd',
        fontSize: 14,
        textAlign: 'center',
        marginTop: 8,
        lineHeight: 20,
        paddingHorizontal: 20,
    },
    features: {
        flexDirection: 'row',
        gap: 12,
        marginBottom: 24,
    },
    featureItem: {
        flexDirection: 'row',
        alignItems: 'center',
        backgroundColor: 'rgba(255,255,255,0.1)',
        paddingHorizontal: 10,
        paddingVertical: 6,
        borderRadius: 20,
        gap: 5,
    },
    featureText: {
        color: '#fff',
        fontSize: 10,
        fontWeight: 'bold',
    },
    card: {
        width: '100%',
        backgroundColor: '#fff',
        borderRadius: 30,
        padding: 24,
        elevation: 20,
        shadowColor: '#000',
        shadowOpacity: 0.3,
        shadowRadius: 15,
    },
    cardTitle: {
        fontSize: 20,
        fontWeight: 'bold',
        color: '#1f2937',
        textAlign: 'center',
        marginBottom: 8,
    },
    cardSubtitle: {
        fontSize: 13,
        color: '#6b7280',
        textAlign: 'center',
        marginBottom: 24,
    },
    inputBox: {
        flexDirection: 'row',
        alignItems: 'center',
        backgroundColor: '#f3f4f6',
        borderRadius: 15,
        paddingHorizontal: 15,
        marginBottom: 14,
        height: 55,
    },
    inputIcon: { marginRight: 10 },
    input: {
        flex: 1,
        fontSize: 16,
        color: '#1f2937',
    },
    button: {
        backgroundColor: '#4c1d95',
        height: 55,
        borderRadius: 15,
        flexDirection: 'row',
        justifyContent: 'center',
        alignItems: 'center',
        marginTop: 6,
    },
    buttonDisabled: { opacity: 0.7 },
    buttonText: {
        color: '#fff',
        fontSize: 16,
        fontWeight: 'bold',
    },
    backButton: {
        marginTop: 16,
        alignItems: 'center',
    },
    backButtonText: {
        color: '#4c1d95',
        fontSize: 14,
        fontWeight: '600',
    },
    loginLink: {
        marginTop: 20,
        alignItems: 'center',
    },
    loginLinkText: {
        color: '#6b7280',
        fontSize: 14,
    },
    footerText: {
        marginTop: 40,
        color: 'rgba(255,255,255,0.5)',
        fontSize: 12,
        fontWeight: 'bold',
        textAlign: 'center',
    },
});
