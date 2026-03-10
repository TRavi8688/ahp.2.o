import React, { useState, useEffect } from 'react';
import { NavigationContainer } from '@react-navigation/native';
import { createNativeStackNavigator } from '@react-navigation/native-stack';
import { StatusBar } from 'expo-status-bar';
import { Alert, LogBox, View, Text } from 'react-native';
import axios from 'axios';
import { useFonts, Syne_800ExtraBold, Syne_700Bold } from '@expo-google-fonts/syne';
import { SpaceMono_400Regular } from '@expo-google-fonts/space-mono';
import { DMSans_400Regular } from '@expo-google-fonts/dm-sans';
import * as SplashScreenNative from 'expo-splash-screen';

SplashScreenNative.preventAutoHideAsync().catch(() => { });

LogBox.ignoreLogs(['props.pointerEvents is deprecated']);

// -----------------------------------------------------------------------------------
// GLOBAL ERROR BOUNDARY
// -----------------------------------------------------------------------------------
axios.interceptors.response.use(
    response => response,
    error => {
        if (error.response) {
            const status = error.response.status;
            if (status === 401) {
                Alert.alert("Session Expired", "Please log in again.");
            } else if (status >= 500) {
                Alert.alert("Server Error", "Chitti is having trouble connecting correctly.");
            }
        }
        return Promise.reject(error);
    }
);

// Screens
import SplashScreen from './src/screens/SplashScreen';
// import LanguageSelectScreen from './src/screens/LanguageSelectScreen';
import AuthScreen from './src/screens/AuthScreen';
import ProfileSetupScreen from './src/screens/ProfileSetupScreen';
import MedicalHistoryScreen from './src/screens/MedicalHistoryScreen';
import CurrentMedicationsScreen from './src/screens/CurrentMedicationsScreen';
import RegisterScreen from './src/screens/RegisterScreen';
import RegistrationSuccessScreen from './src/screens/RegistrationSuccessScreen';
import MainTabs from './src/navigation/MainTabs';
import EmergencyModeScreen from './src/screens/EmergencyModeScreen';
import NotificationsScreen from './src/screens/NotificationsScreen';
import SharingSettingsScreen from './src/screens/SharingSettingsScreen';
import AccessHistoryScreen from './src/screens/AccessHistoryScreen';
import AppointmentsScreen from './src/screens/AppointmentsScreen';
import WeeklyTrendsScreen from './src/screens/WeeklyTrendsScreen';

import { SocketProvider } from './src/contexts/SocketContext';

const Stack = createNativeStackNavigator();

export default function App() {
    const [fontsLoaded] = useFonts({
        Syne_800ExtraBold,
        Syne_700Bold,
        SpaceMono_400Regular,
        DMSans_400Regular,
    });

    const [forceShow, setForceShow] = useState(false);

    useEffect(() => {
        // Force show after 5 seconds even if fonts aren't ready
        const timer = setTimeout(() => {
            setForceShow(true);
            SplashScreenNative.hideAsync().catch(() => { });
        }, 5000);

        if (fontsLoaded) {
            setForceShow(true);
            SplashScreenNative.hideAsync().catch(() => { });
        }

        return () => clearTimeout(timer);
    }, [fontsLoaded]);

    if (!fontsLoaded && !forceShow) {
        return (
            <View style={{ flex: 1, backgroundColor: '#080808', justifyContent: 'center', alignItems: 'center' }}>
                <Text style={{ color: '#FFFFFF', fontSize: 18, letterSpacing: 2 }}>ELEX.AI</Text>
                <Text style={{ color: '#555555', fontSize: 10, marginTop: 10, letterSpacing: 4 }}>INITIALIZING SYSTEM...</Text>
            </View>
        );
    }

    return (
        <SocketProvider>
            <NavigationContainer>
                <StatusBar style="light" />
                <Stack.Navigator screenOptions={{ headerShown: false, animation: 'fade' }}>
                    <Stack.Screen name="Splash" component={SplashScreen} />
                    {/* <Stack.Screen name="LanguageSelect" component={LanguageSelectScreen} /> */}
                    <Stack.Screen name="Login" component={AuthScreen} />
                    <Stack.Screen name="Register" component={RegisterScreen} />
                    <Stack.Screen name="RegistrationSuccess" component={RegistrationSuccessScreen} />
                    <Stack.Screen name="ProfileSetup" component={ProfileSetupScreen} />
                    <Stack.Screen name="MedicalHistory" component={MedicalHistoryScreen} />
                    <Stack.Screen name="CurrentMedications" component={CurrentMedicationsScreen} />
                    <Stack.Screen name="MainTabs" component={MainTabs} />
                    <Stack.Screen
                        name="EmergencyMode"
                        component={EmergencyModeScreen}
                        options={{ presentation: 'fullScreenModal', animation: 'slide_from_bottom' }}
                    />
                    <Stack.Screen name="Notifications" component={NotificationsScreen} />
                    <Stack.Screen name="SharingSettings" component={SharingSettingsScreen} />
                    <Stack.Screen name="AccessHistory" component={AccessHistoryScreen} />
                    <Stack.Screen name="Appointments" component={AppointmentsScreen} />
                    <Stack.Screen name="WeeklyTrends" component={WeeklyTrendsScreen} />
                </Stack.Navigator>
            </NavigationContainer>
        </SocketProvider>
    );
}
