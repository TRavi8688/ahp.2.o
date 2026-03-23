import React, { useState } from 'react';
import { View, Text, StyleSheet, TouchableOpacity, ScrollView } from 'react-native';
import { LinearGradient } from 'expo-linear-gradient';
import { Ionicons } from '@expo/vector-icons';

export default function MedicalHistoryScreen({ navigation, route }) {
    const [selected, setSelected] = useState([]);

    const conditions = [
        'Diabetes', 'Hypertension', 'Asthma', 'Thyroid',
        'Heart Disease', 'Allergies', 'Arthritis', 'None'
    ];

    const toggle = (c) => {
        if (c === 'None') return setSelected(['None']);
        const newSel = selected.includes(c)
            ? selected.filter(x => x !== c)
            : [...selected.filter(x => x !== 'None'), c];
        setSelected(newSel);
    };

    return (
        <View style={styles.container}>
            <LinearGradient colors={['#4c1d95', '#7c3aed']} style={styles.header}>
                <Text style={styles.headerTitle}>Medical History</Text>
                <Text style={styles.headerSubtitle}>Do you have any existing conditions?</Text>
            </LinearGradient>

            <ScrollView contentContainerStyle={styles.content}>
                <View style={styles.grid}>
                    {conditions.map(c => (
                        <TouchableOpacity
                            key={c}
                            style={[styles.item, selected.includes(c) && styles.selectedItem]}
                            onPress={() => toggle(c)}
                        >
                            <Text style={[styles.itemText, selected.includes(c) && styles.selectedText]}>{c}</Text>
                            {selected.includes(c) && <Ionicons name="checkmark-circle" size={20} color="#fff" />}
                        </TouchableOpacity>
                    ))}
                </View>

                <TouchableOpacity
                    style={styles.button}
                    onPress={() => navigation.navigate('CurrentMedications', { ...route.params, conditions: selected })}
                >
                    <Text style={styles.buttonText}>Continue</Text>
                    <Ionicons name="arrow-forward" size={20} color="#fff" style={{ marginLeft: 10 }} />
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
    grid: { flexDirection: 'row', flexWrap: 'wrap', justifyContent: 'space-between', marginBottom: 30 },
    item: {
        width: '47%',
        backgroundColor: '#f3f4f6',
        padding: 20,
        borderRadius: 15,
        marginBottom: 15,
        flexDirection: 'row',
        justifyContent: 'space-between',
        alignItems: 'center'
    },
    selectedItem: { backgroundColor: '#4c1d95' },
    itemText: { fontSize: 14, color: '#374151', fontWeight: '600' },
    selectedText: { color: '#fff' },
    button: {
        backgroundColor: '#4c1d95',
        height: 55,
        borderRadius: 15,
        flexDirection: 'row',
        justifyContent: 'center',
        alignItems: 'center'
    },
    buttonText: { color: '#fff', fontSize: 16, fontWeight: 'bold' },
});
