import { defineConfig, devices } from '@playwright/test'

// Ports default to the project's normal demo values (5183 frontend, 8000
// backend) so a plain `npx playwright test` behaves exactly as before.
// Override with E2E_FRONTEND_PORT / E2E_BACKEND_PORT only for this test
// run (e.g. when the default ports are occupied by another process this
// session must not touch) -- never bake a non-default port into the app's
// own default config (.env.example, vite.config.ts, backend/app/config.py).
const FRONTEND_PORT = process.env.E2E_FRONTEND_PORT ?? '5183'
const BACKEND_PORT = process.env.E2E_BACKEND_PORT ?? '8000'
const FRONTEND_URL = `http://localhost:${FRONTEND_PORT}`
const BACKEND_URL = `http://127.0.0.1:${BACKEND_PORT}`

export default defineConfig({
  testDir: './e2e',
  fullyParallel: true,
  forbidOnly: !!process.env.CI,
  retries: 0,
  reporter: [['list']],
  globalSetup: './e2e/global-setup.ts',
  use: {
    baseURL: FRONTEND_URL,
    trace: 'retain-on-failure',
  },
  projects: [
    { name: 'desktop-chromium', use: { ...devices['Desktop Chrome'], viewport: { width: 1440, height: 900 } } },
    { name: 'tablet', use: { ...devices['Desktop Chrome'], viewport: { width: 768, height: 1024 } } },
    { name: 'mobile', use: { ...devices['Desktop Chrome'], viewport: { width: 390, height: 844 } } },
  ],
  webServer: [
    {
      command: `npm run dev -- --port ${FRONTEND_PORT}`,
      url: FRONTEND_URL,
      reuseExistingServer: true,
      timeout: 30000,
      // Test-only override: points this run's frontend at whichever
      // backend port this run picked, without changing the checked-in
      // VITE_API_BASE_URL default a plain `npm run dev` uses.
      env: { VITE_API_BASE_URL: BACKEND_URL },
    },
    {
      command: `python3 -m uvicorn app.main:app --app-dir backend --port ${BACKEND_PORT}`,
      url: `${BACKEND_URL}/api/v1/health`,
      // Never silently adopt a server this run didn't start -- a stray or
      // stale process on this port (e.g. from another session) must fail
      // the run loudly (address already in use) rather than have tests
      // run against unknown/outdated code. Pick a different
      // E2E_BACKEND_PORT rather than freeing the port yourself.
      reuseExistingServer: false,
      timeout: 30000,
      cwd: '.',
      // Test-only overrides layered on top of the real environment (and
      // this repo's untracked .env, which the backend loads itself) --
      // LLM_PROVIDER/PRIVATE_INTAKE_RAW_DIR still come from there.
      env: {
        CORS_ORIGINS: `http://localhost:${FRONTEND_PORT},http://127.0.0.1:${FRONTEND_PORT}`,
      },
    },
  ],
})
