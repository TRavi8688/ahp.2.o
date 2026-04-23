const createExpoWebpackConfigAsync = require('@expo/webpack-config');

module.exports = async function (env, argv) {
  const config = await createExpoWebpackConfigAsync(env, argv);
  
  // Custom Webpack fix for Mulajna Security Portal
  // This resolves the 'crypto' module not found error in Expo 51
  config.resolve.fallback = {
    ...config.resolve.fallback,
    crypto: false,
    path: false,
    stream: false,
  };

  return config;
};
