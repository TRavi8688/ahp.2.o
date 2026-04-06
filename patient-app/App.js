import React from 'react';
import { NavigationContainer } from '@react-navigation/native';
import { createNativeStackNavigator } from '@react-navigation/native-stack';
import { StatusBar } from 'expo-status-bar';
import { Alert, LogBox } from 'react-native';
import axios from 'axios';

LogBox.ignoreLogs(['props.pointerEvents is deprecated']);

// -----------------------------------------------------------------------------------
// GLOBAL ERROR BOUNDARY
// -----------------------------------------------------------------------------------
axios.interceptors.response.use(
  response => response,
  error => {
    if (error.response) {
      if (error.response.status === 401) {
        Alert.alert("Session Expired", "Please log in again.");
      }
    }
    return Promise.reject(error);
  }
);

// Screens
import SplashScreen from './src/screens/SplashScreen';
import LoginScreen from './src/screens/LoginScreen';
import RegisterScreen from './src/screens/RegisterScreen';
import ProfileSetupScreen from './src/screens/ProfileSetupScreen';
import MainTabs from './src/navigation/MainTabs';
import EmergencyScreen from './src/screens/EmergencyScreen';
import NotificationsScreen from './src/screens/NotificationsScreen';

import { SocketProvider } from './src/contexts/SocketContext';

const Stack = createNativeStackNavigator();

export default function App() {
  return (
    <SocketProvider>
      <NavigationContainer>
        <StatusBar style="light" />
        <Stack.Navigator screenOptions={{ headerShown: false, animation: 'fade' }}>
          <Stack.Screen name="Splash" component={SplashScreen} />
          <Stack.Screen name="Login" component={LoginScreen} />
          <Stack.Screen name="Register" component={RegisterScreen} />
          <Stack.Screen name="ProfileSetup" component={ProfileSetupScreen} />
          <Stack.Screen name="MainTabs" component={MainTabs} />
          <Stack.Screen
            name="EmergencyMode"
            component={EmergencyScreen}
            options={{ presentation: 'fullScreenModal', animation: 'slide_from_bottom' }}
          />
          <Stack.Screen name="Notifications" component={NotificationsScreen} />
        </Stack.Navigator>
      </NavigationContainer>
    </SocketProvider>
  );
}
