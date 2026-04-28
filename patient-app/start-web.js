/**
 * start-web.js
 * Runs Webpack dev server DIRECTLY, bypassing Expo's Metro middleware.
 * This fixes the JSON-at-root collision issue where Metro intercepts requests
 * meant for the Webpack dev server.
 */
const path = require('path');

// We need to call expo's webpack config function the same way expo does
process.env.NODE_ENV = 'development';
process.env.EXPO_WEBPACK_FAST_REFRESH = 'true';

async function start() {
  const createExpoWebpackConfigAsync = require('@expo/webpack-config');
  const Webpack = require('webpack');
  const WebpackDevServer = require('webpack-dev-server');

  const env = {
    projectRoot: __dirname,
    platform: 'web',
    mode: 'development',
    https: false,
    port: 19006,
  };

  console.log('[start-web] Building Webpack config...');
  const config = await createExpoWebpackConfigAsync(env, {});

  // Ensure react-native-web alias is applied (it should be, but just in case)
  config.resolve = config.resolve || {};
  config.resolve.alias = {
    ...(config.resolve.alias || {}),
    'react-native$': 'react-native-web',
  };

  // Fix for missing node built-ins
  config.resolve.fallback = {
    ...(config.resolve.fallback || {}),
    crypto: false,
    path: false,
    stream: false,
  };

  const compiler = Webpack(config);

  const serverConfig = {
    ...config.devServer,
    port: 19006,
    host: 'localhost',
    open: false,
    hot: true,
  };

  const server = new WebpackDevServer(serverConfig, compiler);

  compiler.hooks.done.tap('start-web', (stats) => {
    if (stats.hasErrors()) {
      console.error('[start-web] ❌ Compilation FAILED:\n', stats.toString('errors-only'));
    } else {
      console.log('\n[start-web] ✅ Compiled successfully!');
      console.log('[start-web] 👉 Open: http://localhost:19006\n');
    }
  });

  await server.start();
  console.log('[start-web] Webpack Dev Server running on http://localhost:19006');
}

start().catch((err) => {
  console.error('[start-web] Fatal error:', err);
  process.exit(1);
});
