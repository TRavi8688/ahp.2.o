import React from 'react';
import './src/i18n';
import { NavigationContainer } from '@react-navigation/native';
import { createNativeStackNavigator } from '@react-navigation/native-stack';
import { StatusBar } from 'expo-status-bar';
import { Alert, LogBox } from 'react-native';
import axios from 'axios';

LogBox.ignoreLogs(['props.pointerEvents is deprecated']);

// -----------------------------------------------------------------------------------
// GLOBAL ERROR BOUNDARY: Catch Backend API errors universally
// -----------------------------------------------------------------------------------
axios.interceptors.response.use(
  response => response,
  error => {
    if (error.response) {
      const status = error.response.status;
      if (status === 401) {
        Alert.alert("Session Expired", "Please log in again.");
      } else if (status === 404) {
        Alert.alert("Not Found", error.response.data?.detail || "Record not found.");
      } else if (status >= 500) {
        Alert.alert("Server Error", "Chitti is having trouble connecting to the brain. Please try again later.");
      }
    } else if (error.request) {
      Alert.alert("Connection Error", "Cannot reach the ELEX.AI servers. Please check your internet connection.");
    }
    return Promise.reject(error);
  }
);

// Authentication & Onboarding Screens
import SplashScreen from './src/screens/SplashScreen';
import LanguageSelectScreen from './src/screens/LanguageSelectScreen';
import AuthScreen from './src/screens/AuthScreen';
import ProfileSetupScreen from './src/screens/ProfileSetupScreen';
import MedicalHistoryScreen from './src/screens/MedicalHistoryScreen';
import CurrentMedicationsScreen from './src/screens/CurrentMedicationsScreen';
import RegisterScreen from './src/screens/RegisterScreen';
import RegistrationSuccessScreen from './src/screens/RegistrationSuccessScreen';

// Main Application
import MainTabs from './src/navigation/MainTabs';
import EmergencyModeScreen from './src/screens/EmergencyModeScreen';
import NotificationsScreen from './src/screens/NotificationsScreen';
import SharingSettingsScreen from './src/screens/SharingSettingsScreen';
import AccessHistoryScreen from './src/screens/AccessHistoryScreen';

import { SocketProvider } from './src/contexts/SocketContext';

const Stack = createNativeStackNavigator();

export default function App() {
  return (
    <SocketProvider>
      <NavigationContainer>
        <StatusBar style="light" />
        <Stack.Navigator screenOptions={{ headerShown: false, animation: 'fade' }}>
          <Stack.Screen name="Splash" component={SplashScreen} />
          <Stack.Screen name="LanguageSelect" component={LanguageSelectScreen} />
          <Stack.Screen name="Login" component={AuthScreen} />
          <Stack.Screen name="Register" component={RegisterScreen} />
          <Stack.Screen name="RegistrationSuccess" component={RegistrationSuccessScreen} />
          <Stack.Screen name="ProfileSetup" component={ProfileSetupScreen} />
          <Stack.Screen name="MedicalHistory" component={MedicalHistoryScreen} />
          <Stack.Screen name="CurrentMedications" component={CurrentMedicationsScreen} />

          {/* Main Application */}
          <Stack.Screen name="MainTabs" component={MainTabs} />

          {/* Emergency Mode (Full Screen Overlay) */}
          <Stack.Screen
            name="EmergencyMode"
            component={EmergencyModeScreen}
            options={{ presentation: 'fullScreenModal', animation: 'slide_from_bottom' }}
          />

          <Stack.Screen name="Notifications" component={NotificationsScreen} />
          <Stack.Screen name="SharingSettings" component={SharingSettingsScreen} />
          <Stack.Screen name="AccessHistory" component={AccessHistoryScreen} />
        </Stack.Navigator>
      </NavigationContainer>
    </SocketProvider>
  );
}
