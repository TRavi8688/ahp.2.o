import React, { useState, useEffect } from 'react';
import { View, Text, StyleSheet, ScrollView, TouchableOpacity, RefreshControl, Dimensions, StatusBar as RNStatusBar } from 'react-native';
import { Ionicons } from '@expo/vector-icons';
import axios from 'axios';
import AsyncStorage from '@react-native-async-storage/async-storage';
import { Theme, GlobalStyles } from '../theme';
import { API_BASE_URL } from '../api';

const { width } = Dimensions.get('window');

export default function HomeScreen({ navigation }) {
    const [profile, setProfile] = useState(null);
    const [summary, setSummary] = useState(null);
    const [loading, setLoading] = useState(true);
    const [refreshing, setRefreshing] = useState(false);

    const fetchData = async () => {
        try {
            const token = await AsyncStorage.getItem('token');
            if (!token) {
                navigation.replace('Login');
                return;
            }

            const [profileRes, summaryRes] = await Promise.all([
                axios.get(`${API_BASE_URL}/patient/profile`, { headers: { Authorization: `Bearer ${token}` } }),
                axios.get(`${API_BASE_URL}/patient/clinical-summary`, { headers: { Authorization: `Bearer ${token}` } })
            ]);

            setProfile(profileRes.data);
            setSummary(summaryRes.data);
        } catch (error) {
            console.error('Error fetching dashboard data:', error);
        } finally {
            setLoading(false);
            setRefreshing(false);
        }
    };

    useEffect(() => {
        fetchData();
    }, []);

    const onRefresh = () => {
        setRefreshing(true);
        fetchData();
    };

    const statusDate = new Date().toLocaleDateString('en-GB', { day: '2-digit', month: 'short' }).toUpperCase();

    // Metric Item Component
    const MetricItem = ({ label, value, unit, status, statusColor, isLastRow }) => (
        <View style={[styles.metricCell, isLastRow && { borderBottomWidth: 0 }]}>
            <View style={styles.metricLabelRow}>
                <Text style={styles.metricLabel}>{label}</Text>
                {status && (
                    <Text style={[styles.metricStatus, { color: Theme.colors[statusColor] || statusColor }]}>
                        {status === 'Elevated' ? '↑' : '✓'} {status.toUpperCase()}
                    </Text>
                )}
            </View>
            <Text style={styles.metricValue}>{value}</Text>
            <Text style={styles.metricUnit}>{unit}</Text>
        </View>
    );

    return (
        <View style={GlobalStyles.screen}>
            {/* Status Bar Info (Custom Header) */}
            <View style={styles.statusBarInfo}>
                <Text style={styles.statusBarText}>{statusDate}</Text>
                <Text style={styles.statusBarText}>BATT 98%</Text>
            </View>

            <ScrollView
                refreshControl={<RefreshControl refreshing={refreshing} onRefresh={onRefresh} tintColor="#FFFFFF" />}
                contentContainerStyle={styles.scrollContent}
            >
                {/* Top Section */}
                <View style={styles.topSection}>
                    <View>
                        <Text style={styles.greeting}>GOOD MORNING</Text>
                        <Text style={styles.userName}>{profile?.full_name || 'Ravi Sharma'}</Text>
                    </View>
                    <View style={styles.avatarCircle}>
                        <Text style={styles.avatarText}>RS</Text>
                    </View>
                </View>

                {/* THE SCORE - Hero Element */}
                <View style={styles.scoreHero}>
                    <View style={styles.scoreRow}>
                        <Text style={styles.giantScore}>78</Text>
                        <View style={styles.scoreLabelStack}>
                            <Text style={styles.scoreLabel}>HEALTH SCORE</Text>
                            <Text style={styles.scoreCondition}>Good Condition</Text>
                        </View>
                    </View>
                    {/* Progress Bar */}
                    <View style={styles.progressTrack}>
                        <View style={[styles.progressFill, { width: '78%' }]} />
                    </View>
                </View>

                {/* ALERT BOX */}
                <TouchableOpacity style={styles.alertBox}>
                    <View style={{ flex: 1 }}>
                        <Text style={styles.alertTitle}>BP ELEVATED — REVIEW NOW</Text>
                        <Text style={styles.alertSub}>3 CONSECUTIVE HIGH READINGS · TAP TO ACT</Text>
                    </View>
                    <Ionicons name="arrow-forward" size={20} color="#FFFFFF" />
                </TouchableOpacity>

                <View style={styles.grayDivider} />

                {/* 4-Metric Grid */}
                <View style={styles.metricGrid}>
                    <View style={styles.metricRow}>
                        <MetricItem
                            label="SYSTOLIC/DIASTOLIC"
                            value="128/84"
                            unit="mmHg"
                            status="Elevated"
                            statusColor="warning"
                        />
                        <View style={styles.verticalDivider} />
                        <MetricItem
                            label="HEART RATE"
                            value="76"
                            unit="bpm"
                            status="Normal"
                            statusColor="positive"
                        />
                    </View>
                    <View style={styles.horizontalDivider} />
                    <View style={styles.metricRow}>
                        <MetricItem
                            label="BLOOD OXYGEN"
                            value="96%"
                            unit="SpO₂"
                            status="Normal"
                            statusColor="positive"
                            isLastRow
                        />
                        <View style={styles.verticalDivider} />
                        <MetricItem
                            label="TEMPERATURE"
                            value="98.4°"
                            unit="Fahrenheit"
                            status="Normal"
                            statusColor="positive"
                            isLastRow
                        />
                    </View>
                </View>

                {/* AI Assistant CTA (Page 7 Link) */}
                <TouchableOpacity
                    style={styles.aiLink}
                    onPress={() => navigation.navigate('Chitti')}
                >
                    <Text style={styles.aiLinkText}>ASK CHITTI AI ANYTHING →</Text>
                </TouchableOpacity>

                <View style={{ height: 100 }} />
            </ScrollView>
        </View>
    );
}

const styles = StyleSheet.create({
    statusBarInfo: {
        flexDirection: 'row',
        justifyContent: 'space-between',
        paddingTop: 50,
        paddingHorizontal: 20,
        paddingBottom: 10,
    },
    statusBarText: {
        fontFamily: Theme.fonts.label,
        color: Theme.colors.secondary,
        fontSize: 10,
    },
    scrollContent: {
        paddingHorizontal: 20,
    },
    topSection: {
        flexDirection: 'row',
        justifyContent: 'space-between',
        alignItems: 'center',
        marginTop: 20,
        marginBottom: 40,
    },
    greeting: {
        fontFamily: Theme.fonts.label,
        color: Theme.colors.secondary,
        fontSize: 10,
        letterSpacing: 1,
    },
    userName: {
        fontFamily: Theme.fonts.heading,
        color: Theme.colors.primary,
        fontSize: 24,
    },
    avatarCircle: {
        width: 50,
        height: 50,
        borderRadius: 25,
        borderWidth: 1,
        borderColor: Theme.colors.primary,
        justifyContent: 'center',
        alignItems: 'center',
    },
    avatarText: {
        fontFamily: Theme.fonts.headingSemi,
        color: Theme.colors.primary,
        fontSize: 18,
    },
    scoreHero: {
        marginBottom: 30,
    },
    scoreRow: {
        flexDirection: 'row',
        alignItems: 'flex-end',
        marginBottom: 15,
        gap: 15,
    },
    giantScore: {
        fontFamily: Theme.fonts.heading,
        color: Theme.colors.primary,
        fontSize: 80,
        lineHeight: 80,
    },
    scoreLabelStack: {
        paddingBottom: 10,
    },
    scoreLabel: {
        fontFamily: Theme.fonts.label,
        color: Theme.colors.secondary,
        fontSize: 10,
        letterSpacing: 1,
    },
    scoreCondition: {
        fontFamily: Theme.fonts.body,
        color: Theme.colors.primary,
        fontSize: 14,
    },
    progressTrack: {
        height: 4,
        backgroundColor: Theme.colors.black,
        width: '100%',
    },
    progressFill: {
        height: '100%',
        backgroundColor: Theme.colors.primary,
    },
    alertBox: {
        borderWidth: 1,
        borderColor: Theme.colors.primary,
        padding: 20,
        flexDirection: 'row',
        alignItems: 'center',
        marginTop: 20,
    },
    alertTitle: {
        fontFamily: Theme.fonts.headingSemi,
        color: Theme.colors.primary,
        fontSize: 14,
    },
    alertSub: {
        fontFamily: Theme.fonts.label,
        color: Theme.colors.secondary,
        fontSize: 9,
        marginTop: 4,
    },
    grayDivider: {
        height: 1,
        backgroundColor: '#1A1A1A',
        width: '100%',
        marginVertical: 40,
    },
    metricGrid: {
        width: '100%',
    },
    metricRow: {
        flexDirection: 'row',
    },
    metricCell: {
        flex: 1,
        paddingVertical: 15,
    },
    metricLabelRow: {
        flexDirection: 'row',
        justifyContent: 'space-between',
        alignItems: 'center',
        marginBottom: 5,
    },
    metricLabel: {
        fontFamily: Theme.fonts.label,
        color: Theme.colors.secondary,
        fontSize: 9,
        letterSpacing: 0.5,
    },
    metricStatus: {
        fontFamily: Theme.fonts.label,
        fontSize: 8,
    },
    metricValue: {
        fontFamily: Theme.fonts.headingSemi,
        color: Theme.colors.primary,
        fontSize: 20,
    },
    metricUnit: {
        fontFamily: Theme.fonts.label,
        color: Theme.colors.secondary,
        fontSize: 9,
    },
    verticalDivider: {
        width: 1,
        backgroundColor: '#1A1A1A',
        marginHorizontal: 15,
    },
    horizontalDivider: {
        height: 1,
        backgroundColor: '#1A1A1A',
        width: '100%',
    },
    aiLink: {
        marginTop: 40,
        alignItems: 'center',
        paddingVertical: 15,
        borderWidth: 1,
        borderStyle: 'dashed',
        borderColor: '#333',
    },
    aiLinkText: {
        fontFamily: Theme.fonts.label,
        color: Theme.colors.secondary,
        fontSize: 12,
        letterSpacing: 1,
    }
});
