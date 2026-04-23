import React, { useState, useEffect } from 'react';
import { View, Text, ActivityIndicator, TouchableOpacity, StyleSheet } from 'react-native-web';
import { NavigationContainer } from '@react-navigation/native';
import { createNativeStackNavigator } from '@react-navigation/native-stack';
import AsyncStorage from '@react-native-async-storage/async-storage';
import { SafeAreaProvider } from 'react-native-safe-area-context';

// Core
import { SocketProvider } from './src/contexts/SocketContext';
import { useFonts, Syne_800ExtraBold, Syne_700Bold } from '@expo-google-fonts/syne';

// Screens
import LoginScreen from './src/screens/LoginScreen';
import RegisterScreen from './src/screens/RegisterScreen';
import ProfileSetupScreen from './src/screens/ProfileSetupScreen';
import MainTabs from './src/navigation/MainTabs';
import EmergencyScreen from './src/screens/EmergencyScreen';
import NotificationsScreen from './src/screens/NotificationsScreen';

const Stack = createNativeStackNavigator();

// -----------------------------------------------------------------------------------
// ERROR BOUNDARY FOR RESILIENCE
// -----------------------------------------------------------------------------------
class ErrorBoundary extends React.Component {
  state = { hasError: false, error: null };
  static getDerivedStateFromError(error) { return { hasError: true, error }; }
  componentDidCatch(error, info) { console.error('[Fatal App Error]', error, info); }
  render() {
    if (this.state.hasError) {
      return (
        <View style={{ flex: 1, backgroundColor: '#050810', justifyContent: 'center', padding: 40 }}>
          <Text style={{ color: '#EF4444', fontSize: 24, fontWeight: 'bold' }}>BOOT_CRITICAL: Mulajna System Failure</Text>
          <Text style={{ color: '#94A3B8', marginTop: 20 }}>An unexpected error prevented the system from starting.</Text>
          <Text style={{ color: '#FCD34D', marginTop: 20, fontFamily: 'monospace' }}>{this.state.error?.toString()}</Text>
          <TouchableOpacity 
            style={{ marginTop: 40, padding: 20, backgroundColor: '#6366F1', borderRadius: 12 }}
            onPress={() => window.location.reload()}
          >
            <Text style={{ color: 'white', textAlign: 'center' }}>FORCED_RESTART</Text>
          </TouchableOpacity>
        </View>
      );
    }
    return this.props.children;
  }
}

export default function App() {
  const [fontsLoaded] = useFonts({
    Syne_800ExtraBold,
    Syne_700Bold,
  });

  const [initialRoute, setInitialRoute] = useState(null);
  const [bootReady, setBootReady] = useState(false);

  useEffect(() => {
    const init = async () => {
      try {
        console.log('[App] Booting system...');
        const token = await AsyncStorage.getItem('mulajna_auth_token');
        console.log('[App] Token check:', token ? 'Session found' : 'No session');
        setInitialRoute(token ? 'MainTabs' : 'Login');
        
        const timer = setTimeout(() => {
          setBootReady(true);
        }, 1500);

        if (fontsLoaded) {
          setBootReady(true);
          clearTimeout(timer);
        }
      } catch (e) {
        setInitialRoute('Login');
        setBootReady(true);
      }
    };
    init();
  }, [fontsLoaded]);

  if (!bootReady || !initialRoute) {
    return (
      <View style={{ flex: 1, backgroundColor: '#050810', justifyContent: 'center', alignItems: 'center' }}>
        <Text style={{ color: '#6366F1', fontSize: 42, letterSpacing: 10, fontWeight: '900' }}>MULAJNA</Text>
        <ActivityIndicator size="large" color="#6366F1" style={{ marginTop: 20 }} />
        <Text style={{ color: '#94A3B8', marginTop: 20, letterSpacing: 2 }}>SECURE BOOT INITIALIZING...</Text>
      </View>
    );
  }

  return (
    <ErrorBoundary>
      <SafeAreaProvider style={{ flex: 1, backgroundColor: '#050810' }}>
        <SocketProvider>
          <NavigationContainer>
            <Stack.Navigator 
              screenOptions={{ headerShown: false, animation: 'fade' }} 
              initialRouteName={initialRoute}
            >
              <Stack.Screen name="Login" component={LoginScreen} />
              <Stack.Screen name="Register" component={RegisterScreen} />
              <Stack.Screen name="ProfileSetup" component={ProfileSetupScreen} />
              <Stack.Screen name="MainTabs" component={MainTabs} />
              <Stack.Screen name="EmergencyMode" component={EmergencyScreen} />
              <Stack.Screen name="Notifications" component={NotificationsScreen} />
            </Stack.Navigator>
          </NavigationContainer>
        </SocketProvider>
      </SafeAreaProvider>
    </ErrorBoundary>
  );
}
