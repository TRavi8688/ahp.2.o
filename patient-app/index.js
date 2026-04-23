// --- V15 STYLES SHIELD ---
// This is the emergency polyfill that captures any missed library-level crashes.
import * as ReactNativeWeb from 'react-native-web';
if (typeof window !== 'undefined') {
    window.StyleSheet = ReactNativeWeb.StyleSheet;
    if (!window.StyleSheet.create) {
        window.StyleSheet.create = (obj) => obj;
    }
}

import { AppRegistry, Platform } from 'react-native-web';
import App from './App';

// --- MULAJNA PRODUCTION RESTORATION v15.0 ---
if (Platform.OS === 'web') {
    document.body.style.backgroundColor = '#050810';
    AppRegistry.registerComponent('main', () => App);
    AppRegistry.runApplication('main', {
        initialProps: {},
        rootTag: document.getElementById('root') || document.getElementById('main')
    });
} else {
    const { registerRootComponent } = require('expo');
    registerRootComponent(App);
}
