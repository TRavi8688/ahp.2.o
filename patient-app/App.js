import React, { useState, useEffect } from 'react';
import { View, Text, ActivityIndicator } from 'react-native';
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

export default function App() {
  const [fontsLoaded] = useFonts({
    Syne_800ExtraBold,
    Syne_700Bold,
  });

  const [initialRoute, setInitialRoute] = useState(null);

  useEffect(() => {
    const init = async () => {
      try {
        const token = await AsyncStorage.getItem('token');
        setInitialRoute(token ? 'MainTabs' : 'Login');
        console.log('[Heartbeat 3] Session Context Initialized');
      } catch (e) {
        console.error('[App] Init Error:', e);
        setInitialRoute('Login');
      }
    };
    init();
  }, []);

  if (!fontsLoaded || !initialRoute) {
    return (
      <View style={{ flex: 1, backgroundColor: '#050810', justifyContent: 'center', alignItems: 'center' }}>
        <ActivityIndicator size="large" color="#6366F1" />
      </View>
    );
  }

  return (
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
  );
}
