import { defineConfig } from '@rsbuild/core';
import { pluginReact } from '@rsbuild/plugin-react';

export default defineConfig({
  plugins: [pluginReact()],
  html: {
    title: 'M3U Filter'
  },
  output: {
    distPath: {
      root: 'dist/web'
    },
    assetPrefix: '/web/'
  }
});
