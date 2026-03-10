import React, { useState, useEffect } from 'react';
import { View, Text, StyleSheet, TouchableOpacity, ScrollView, Alert, Dimensions } from 'react-native';
import { Ionicons } from '@expo/vector-icons';
import AsyncStorage from '@react-native-async-storage/async-storage';
import axios from 'axios';
import { Theme, GlobalStyles } from '../theme';
import { API_BASE_URL } from '../api';

const { width } = Dimensions.get('window');

export default function SettingsScreen({ navigation }) {
    const [profile, setProfile] = useState(null);
    const [ahpId, setAhpId] = useState('');

    useEffect(() => {
        const fetchProfile = async () => {
            try {
                const token = await AsyncStorage.getItem('token');
                const response = await axios.get(`${API_BASE_URL}/patient/profile`, {
                    headers: { Authorization: `Bearer ${token}` }
                });
                setProfile(response.data);
                const storedAhp = await AsyncStorage.getItem('ahp_id');
                setAhpId(storedAhp || '');
            } catch (err) {
                console.log("Settings fetch error", err);
            }
        };
        fetchProfile();
    }, []);

    const handleLogout = async () => {
        Alert.alert('TERMINATE SESSION', 'ARE YOU SURE YOU WANT TO LOGOUT?', [
            { text: 'CANCEL', style: 'cancel' },
            {
                text: 'LOGOUT',
                style: 'destructive',
                onPress: async () => {
                    await AsyncStorage.removeItem('token');
                    navigation.reset({ index: 0, routes: [{ name: 'Login' }] });
                }
            }
        ]);
    };

    const SettingItem = ({ label, onPress }) => (
        <TouchableOpacity style={styles.settingItem} onPress={onPress}>
            <Text style={styles.settingLabel}>{label}</Text>
            <Ionicons name="arrow-forward" size={18} color="#FFFFFF" />
        </TouchableOpacity>
    );

    return (
        <View style={GlobalStyles.screen}>
            <ScrollView contentContainerStyle={styles.scrollContent}>
                {/* Profile Header */}
                <View style={styles.header}>
                    <Text style={styles.massiveName}>{profile?.full_name?.toUpperCase() || 'RAVI SHARMA'}</Text>
                    <Text style={styles.ahpId}>{ahpId || 'AHP-000000-XXX'}</Text>
                </View>

                {/* Terminate Session Button */}
                <TouchableOpacity style={styles.logoutButton} onPress={handleLogout}>
                    <Text style={styles.logoutText}>TERMINATE SESSION</Text>
                </TouchableOpacity>

                {/* Settings Items */}
                <View style={styles.settingsList}>
                    <SettingItem label="ACCOUNT SETTINGS" onPress={() => { }} />
                    <SettingItem label="PRIVACY & SHARING" onPress={() => navigation.navigate('SharingSettings')} />
                    <SettingItem label="DATA LOGS" onPress={() => navigation.navigate('AccessHistory')} />
                    <SettingItem label="SYSTEM NOTIFICATIONS" onPress={() => navigation.navigate('Notifications')} />
                    <SettingItem label="LANGUAGE SETTINGS" onPress={() => { }} />
                </View>

                {/* Footer */}
                <View style={styles.footer}>
                    <Text style={styles.footerText}>ELEX.AI V4.0.1 — ENCRYPTED</Text>
                </View>

                <View style={{ height: 100 }} />
            </ScrollView>
        </View>
    );
}

const styles = StyleSheet.create({
    scrollContent: {
        paddingHorizontal: 30,
        paddingTop: 80,
    },
    header: {
        marginBottom: 50,
    },
    massiveName: {
        fontFamily: Theme.fonts.heading,
        color: Theme.colors.primary,
        fontSize: 32,
        letterSpacing: -1,
    },
    ahpId: {
        fontFamily: Theme.fonts.label,
        color: Theme.colors.secondary,
        fontSize: 12,
        marginTop: 5,
        letterSpacing: 2,
    },
    logoutButton: {
        backgroundColor: '#FFFFFF',
        height: 60,
        alignItems: 'center',
        justifyContent: 'center',
        marginBottom: 60,
        borderRadius: 0,
    },
    logoutText: {
        fontFamily: Theme.fonts.headingSemi,
        color: '#000000',
        fontSize: 14,
        letterSpacing: 1,
    },
    settingsList: {
        borderTopWidth: 1,
        borderTopColor: '#1A1A1A',
    },
    settingItem: {
        flexDirection: 'row',
        justifyContent: 'space-between',
        alignItems: 'center',
        paddingVertical: 25,
        borderBottomWidth: 1,
        borderBottomColor: '#1A1A1A',
    },
    settingLabel: {
        fontFamily: Theme.fonts.label,
        color: Theme.colors.primary,
        fontSize: 12,
        letterSpacing: 1,
    },
    footer: {
        marginTop: 60,
        alignItems: 'center',
    },
    footerText: {
        fontFamily: Theme.fonts.label,
        color: Theme.colors.secondary,
        fontSize: 10,
        letterSpacing: 1,
    }
});
