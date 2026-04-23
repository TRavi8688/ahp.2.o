const { getDefaultConfig } = require('expo/metro-config');
const path = require('path');

/** @type {import('expo/metro-config').MetroConfig} */
const config = getDefaultConfig(__dirname);

// --- V16 DEEP METRO OVERRIDE ---
// This is the strongest way to disable the Hermes transform on web.

// 1. Explicitly disable Hermes in the transformer
config.transformer.getTransformOptions = async () => ({
  transform: {
    experimentalImportSupport: false,
    inlineRequires: true,
    // Force Hermes to false for any web-related transform
    hermes: false,
  },
});

// 2. Absolute Aliasing via extraNodeModules
config.resolver.extraNodeModules = {
  'react-native': path.resolve(__dirname, 'node_modules/react-native-web'),
};

// 3. Platform-specific resolution priority
config.resolver.sourceExts = [
  'web.js', 'web.jsx', 'web.ts', 'web.tsx',
  'js', 'jsx', 'json', 'ts', 'tsx'
];

module.exports = config;
