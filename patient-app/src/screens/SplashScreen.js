import React, { useEffect, useRef } from 'react';
import { View, Text, StyleSheet, Animated, Dimensions } from 'react-native';
import { Theme, GlobalStyles } from '../theme';

const { width } = Dimensions.get('window');

export default function SplashScreen({ navigation }) {
    const loaderAnim = useRef(new Animated.Value(0)).current;

    useEffect(() => {
        // Simple loading bar animation
        Animated.timing(loaderAnim, {
            toValue: 1,
            duration: 2000,
            useNativeDriver: false,
        }).start(() => {
            navigation.replace('Login');
        });
    }, []);

    const barWidth = loaderAnim.interpolate({
        inputRange: [0, 1],
        outputRange: ['0%', '100%'],
    });

    return (
        <View style={styles.container}>
            <View style={styles.content}>
                <Text style={styles.logoText}>ELEX.AI</Text>

                {/* Thin white horizontal line (full width) */}
                <View style={styles.divider} />

                <Text style={styles.tagline}>HEALTH INTELLIGENCE</Text>
            </View>

            {/* Bottom: Thin animated loading bar */}
            <View style={styles.loaderContainer}>
                <Animated.View style={[styles.loaderBar, { width: barWidth }]} />
            </View>
        </View>
    );
}

const styles = StyleSheet.create({
    container: {
        flex: 1,
        backgroundColor: Theme.colors.background,
        justifyContent: 'center',
        paddingHorizontal: 0,
    },
    content: {
        alignItems: 'center',
        width: '100%',
    },
    logoText: {
        fontFamily: Theme.fonts.heading,
        color: Theme.colors.primary,
        fontSize: width * 0.15, // Giant
        textAlign: 'center',
        width: '60%',
        letterSpacing: -2,
    },
    divider: {
        height: 1,
        backgroundColor: Theme.colors.primary,
        width: '100%',
        marginVertical: 10,
    },
    tagline: {
        fontFamily: Theme.fonts.label,
        color: Theme.colors.secondary,
        fontSize: 10,
        letterSpacing: 4,
        textAlign: 'center',
        marginTop: 5,
    },
    loaderContainer: {
        position: 'absolute',
        bottom: 50,
        left: 0,
        right: 0,
        height: 2,
        backgroundColor: Theme.colors.black,
    },
    loaderBar: {
        height: '100%',
        backgroundColor: Theme.colors.primary,
    }
});
