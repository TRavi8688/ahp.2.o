import React, { useState } from 'react';
import { View, Text, StyleSheet, TouchableOpacity, TextInput, ScrollView, Alert } from 'react-native';
import { LinearGradient } from 'expo-linear-gradient';
import { Ionicons } from '@expo/vector-icons';
import axios from 'axios';
import AsyncStorage from '@react-native-async-storage/async-storage';

import { API_BASE_URL } from '../api';

export default function CurrentMedicationsScreen({ navigation, route }) {
    const [meds, setMeds] = useState([]);
    const [currentMed, setCurrentMed] = useState('');

    const addMed = () => {
        if (!currentMed) return;
        setMeds([...meds, currentMed]);
        setCurrentMed('');
    };

    const removeMed = (index) => {
        setMeds(meds.filter((_, i) => i !== index));
    };

    const handleFinish = async () => {
        try {
            const fullName = route.params?.fullName || "";
            const names = fullName.split(" ");
            const firstName = names[0] || "Unknown";
            const lastName = names.length > 1 ? names.slice(1).join(" ") : "";

            const payload = {
                phone_number: route.params?.phone || "",
                first_name: firstName,
                last_name: lastName,
                date_of_birth: route.params?.age ? String(route.params.age) : "0",
                gender: route.params?.gender || "Unknown",
                blood_group: route.params?.bloodGroup || "Unknown",
                conditions: route.params?.conditions || [],
                medications: meds
            };

            const response = await axios.post(`${API_BASE_URL}/profile/setup`, payload);

            if (response.data && response.data.access_token) {
                await AsyncStorage.setItem('token', response.data.access_token);
                navigation.replace('MainTabs');
            } else {
                Alert.alert("Error", "Registration failed. No token received.");
            }
        } catch (error) {
            console.error('Registration Error:', error);
            Alert.alert("Error", "Could not complete registration.");
        }
    };

    return (
        <View style={styles.container}>
            <LinearGradient colors={['#4c1d95', '#7c3aed']} style={styles.header}>
                <Text style={styles.headerTitle}>Current Medications</Text>
                <Text style={styles.headerSubtitle}>Do you take any daily medicines?</Text>
            </LinearGradient>

            <ScrollView contentContainerStyle={styles.content}>
                <View style={styles.inputRow}>
                    <TextInput
                        style={styles.input}
                        placeholder="Medicine name (e.g. Lipitor)"
                        value={currentMed}
                        onChangeText={setCurrentMed}
                    />
                    <TouchableOpacity style={styles.addButton} onPress={addMed}>
                        <Ionicons name="add" size={30} color="#fff" />
                    </TouchableOpacity>
                </View>

                <View style={styles.list}>
                    {meds.map((m, i) => (
                        <View key={i} style={styles.medItem}>
                            <View style={styles.medIcon}>
                                <Ionicons name="medkit-outline" size={20} color="#4c1d95" />
                            </View>
                            <Text style={styles.medText}>{m}</Text>
                            <TouchableOpacity onPress={() => removeMed(i)}>
                                <Ionicons name="trash-outline" size={20} color="#dc2626" />
                            </TouchableOpacity>
                        </View>
                    ))}
                </View>

                <TouchableOpacity style={styles.button} onPress={handleFinish}>
                    <Text style={styles.buttonText}>Finish Setup</Text>
                    <Ionicons name="checkmark-circle" size={20} color="#fff" style={{ marginLeft: 10 }} />
                </TouchableOpacity>

                <TouchableOpacity style={styles.skipButton} onPress={handleFinish}>
                    <Text style={styles.skipText}>I'll add them later</Text>
                </TouchableOpacity>
            </ScrollView>
        </View>
    );
}

const styles = StyleSheet.create({
    container: { flex: 1, backgroundColor: '#fff' },
    header: { padding: 40, paddingTop: 60, borderBottomLeftRadius: 30, borderBottomRightRadius: 30 },
    headerTitle: { color: '#fff', fontSize: 24, fontWeight: 'bold' },
    headerSubtitle: { color: '#ddd', fontSize: 16, marginTop: 5 },
    content: { padding: 25 },
    inputRow: { flexDirection: 'row', marginBottom: 25 },
    input: { flex: 1, backgroundColor: '#f3f4f6', borderRadius: 12, padding: 15, fontSize: 16, marginRight: 10 },
    addButton: { backgroundColor: '#4c1d95', width: 55, borderRadius: 12, justifyContent: 'center', alignItems: 'center' },
    list: { marginBottom: 30 },
    medItem: {
        flexDirection: 'row',
        alignItems: 'center',
        backgroundColor: '#fff',
        padding: 15,
        borderRadius: 12,
        marginBottom: 10,
        elevation: 2,
        shadowOpacity: 0.1,
        shadowRadius: 5
    },
    medIcon: { width: 40, height: 40, borderRadius: 10, backgroundColor: '#f5f3ff', justifyContent: 'center', alignItems: 'center', marginRight: 15 },
    medText: { flex: 1, fontSize: 15, fontWeight: '600', color: '#374151' },
    button: {
        backgroundColor: '#4c1d95',
        height: 55,
        borderRadius: 15,
        flexDirection: 'row',
        justifyContent: 'center',
        alignItems: 'center'
    },
    buttonText: { color: '#fff', fontSize: 16, fontWeight: 'bold' },
    skipButton: { marginTop: 20, alignItems: 'center' },
    skipText: { color: '#6b7280', fontSize: 14 },
});
