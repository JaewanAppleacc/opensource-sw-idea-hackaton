/**
 * Runs once before any test. Hard-fails the whole run (never lets
 * individual tests limp along and report misleading failures) if the
 * backend this run will talk to is not actually the safe, offline mock
 * configuration -- this is the one enforced precondition for every e2e
 * scenario in this repo: LLM_PROVIDER=mock, no external network call,
 * no API key needed. Never prints response bodies beyond the two fields
 * checked here (no posting text, no secrets are present in this endpoint
 * anyway, but this file must not become a place that starts logging them).
 */
const BACKEND_PORT = process.env.E2E_BACKEND_PORT ?? '8000'
const BACKEND_URL = `http://127.0.0.1:${BACKEND_PORT}`
const HEALTH_URL = `${BACKEND_URL}/api/v1/health`

async function fetchHealthWithRetry(maxAttempts: number, delayMs: number) {
  let lastError: unknown
  for (let attempt = 1; attempt <= maxAttempts; attempt += 1) {
    try {
      const response = await fetch(HEALTH_URL)
      if (response.ok) return response.json()
      lastError = new Error(`GET ${HEALTH_URL} -> HTTP ${response.status}`)
    } catch (error) {
      lastError = error
    }
    await new Promise((resolve) => setTimeout(resolve, delayMs))
  }
  throw lastError
}

export default async function globalSetup() {
  const health = await fetchHealthWithRetry(10, 500)

  if (health.provider_mode !== 'mock') {
    throw new Error(
      `e2e refuses to run: backend at ${BACKEND_URL} reports provider_mode=${JSON.stringify(health.provider_mode)}, ` +
        'expected "mock". These scenarios must run fully offline with no external LLM call. ' +
        'Set LLM_PROVIDER=mock (or unset it) and restart the backend.',
    )
  }
  if (health.dataset_available !== true) {
    throw new Error(
      `e2e refuses to run: backend at ${BACKEND_URL} reports dataset_available=false. ` +
        'The curated Jeonbuk dataset must be present for these scenarios.',
    )
  }
}
