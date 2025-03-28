import { execSync } from 'node:child_process';

try {
  execSync('npx msw init public --save');
  console.log('MSW Service Worker initialized successfully');
} catch (error) {
  console.error('Error initializing MSW Service Worker:', error);
}
