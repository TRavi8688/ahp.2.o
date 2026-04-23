module.exports = function (api) {
  api.cache(true);
  return {
    presets: ['babel-preset-expo'],
    plugins: [
      // --- V14 GLOBAL ALIAS REPAIR ---
      // This forces ALL imports (including libraries) to use react-native-web.
      // This is the absolute fix for "StyleSheet.create is not a function".
      ['module-resolver', {
        alias: {
          '^react-native$': 'react-native-web',
        },
      }],
      'react-native-reanimated/plugin',
    ],
  };
};
