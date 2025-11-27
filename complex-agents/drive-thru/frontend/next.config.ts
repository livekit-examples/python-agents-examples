import path from 'path';
import { fileURLToPath } from 'url';
import type { NextConfig } from 'next';

const __dirname = path.dirname(fileURLToPath(import.meta.url));

const nextConfig: NextConfig = {
  webpack: (config) => {
    config.resolve.alias['clsx'] = path.resolve(__dirname, 'node_modules/clsx');
    config.resolve.alias['tailwind-merge'] = path.resolve(
      __dirname,
      'node_modules/tailwind-merge'
    );

    // Ignore bulky directories for both client and server watchers to avoid EMFILE errors
    const ignoredGlobs = [
      '**/node_modules/**',
      '**/.git/**',
      '**/.next/**',
      '**/dist/**',
      '**/build/**',
      '../../**/node_modules/**',
    ];

    config.watchOptions = {
      ...config.watchOptions,
      ignored: ignoredGlobs,
    };

    return config;
  },
};

export default nextConfig;
