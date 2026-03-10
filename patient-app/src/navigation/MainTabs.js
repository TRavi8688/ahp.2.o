import React from 'react';
import { createBottomTabNavigator } from '@react-navigation/bottom-tabs';
import { Ionicons } from '@expo/vector-icons';
import { View, Text } from 'react-native';

// Import Screens
import HomeScreen from '../screens/HomeScreen';
import VitalsScreen from '../screens/VitalsScreen';
import ChittiAiScreen from '../screens/ChittiAiScreen';
import MedsScreen from '../screens/MedsScreen';

const Tab = createBottomTabNavigator();

export default function MainTabs() {
    return (
        <Tab.Navigator
            screenOptions={({ route }) => ({
                tabBarIcon: ({ focused, color, size }) => {
                    let iconName;

                    if (route.name === 'Home') {
                        iconName = focused ? 'home' : 'home-outline';
                    } else if (route.name === 'Vitals') {
                        iconName = focused ? 'pulse' : 'pulse-outline';
                    } else if (route.name === 'Chitti') {
                        iconName = focused ? 'chatbubble-ellipses' : 'chatbubble-ellipses-outline';
                    } else if (route.name === 'Meds') {
                        iconName = focused ? 'medkit' : 'medkit-outline';
                    }

                    return <Ionicons name={iconName} size={size} color={color} />;
                },
                tabBarActiveTintColor: '#FFFFFF',
                tabBarInactiveTintColor: '#555555',
                tabBarLabelStyle: {
                    fontFamily: 'SpaceMono_400Regular',
                    fontSize: 10,
                    letterSpacing: 1,
                },
                tabBarStyle: {
                    backgroundColor: '#080808',
                    borderTopWidth: 1,
                    borderTopColor: '#1A1A1A',
                    height: 80,
                    paddingBottom: 20,
                },
                headerShown: false,
            })}
        >
            <Tab.Screen name="Home" component={HomeScreen} />
            <Tab.Screen name="Vitals" component={VitalsScreen} />
            <Tab.Screen name="Chitti" component={ChittiAiScreen} />
            <Tab.Screen name="Meds" component={MedsScreen} />
        </Tab.Navigator>
    );
}
