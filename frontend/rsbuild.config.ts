import { defineConfig } from '@rsbuild/core';
import { pluginReact } from '@rsbuild/plugin-react';
import autoprefixer from 'autoprefixer';

export default defineConfig({
  plugins: [pluginReact()],
  output: {
    distPath: {
      root: 'dist'
    },
    assetPrefix: '/',
    polyfill: 'entry',
    target: 'web',
    copy: [{ from: './public', to: '.' }],
  },
  html: {
    title: 'M3U Filter'
  },
  server: {
    base: '/',
    cors: true,
    port: 3000,
    proxy: {
      '/api': {
        target: 'http://localhost:3232',
        changeOrigin: true,
      },
    },
  },
  source: {
    define: {
      ENABLE_MOCK: JSON.stringify(true),
    },
    alias: {
      '@': './src'
    }
  },
  tools: {
    postcss: {
      postcssOptions: {
        plugins: [
          autoprefixer({
            flexbox: 'no-2009',
            grid: true,
          }),
        ],
      },
    },
  },
});
