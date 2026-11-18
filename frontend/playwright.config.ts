import { defineConfig } from '@playwright/test'

const baseURL = process.env.PULS_BASE_URL ?? 'http://localhost:8080'
const channel = process.env.PULS_BROWSER_CHANNEL

export default defineConfig({
  testDir: './tests/e2e',
  workers: 1,
  retries: 0,
  reporter: process.env.CI ? [['github'], ['html', { open: 'never' }]] : 'list',
  use: { baseURL, channel, trace: 'off' },
  projects: [
    { name: 'mobile-360', grepInvert: /@desktop/, use: { viewport: { width: 360, height: 800 }, isMobile: true, hasTouch: true } },
    { name: 'mobile-390', grepInvert: /@desktop|@mobile-360/, use: { viewport: { width: 390, height: 844 }, isMobile: true, hasTouch: true } },
    { name: 'desktop', grepInvert: /@mobile-360/, use: { viewport: { width: 1440, height: 900 } } },
  ],
})
