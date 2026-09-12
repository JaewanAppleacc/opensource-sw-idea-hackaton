/**
 * Demo-only "login" state for the region-scoped comparison agent. This is
 * NOT real authentication: no password, no server session, no real address
 * or contact info is ever collected or stored. A single fixed demo profile
 * is toggled on/off in localStorage (per-browser only, never sent to the
 * backend, never shared across viewers) purely so the UI can show the
 * "로그인하면 비교할 수 있습니다" -> "OO 기준으로 비교하고 있습니다" journey
 * the task calls for. The backend independently enforces the same home
 * region via its own DEMO_HOME_REGION setting (see
 * backend/app/datasets/loader.py::home_region()) -- this module only
 * drives what the UI *shows*, never what the backend actually returns.
 */

const STORAGE_KEY = 'jeonbuk-agent-demo-login'

export interface DemoProfile {
  displayName: string
  homeRegionLabel: string
  homeRegionCode: string
}

export const DEMO_PROFILE: DemoProfile = {
  displayName: '전북 청년 데모 사용자',
  homeRegionLabel: '전북특별자치도',
  homeRegionCode: 'JEONBUK',
}

export function isDemoLoggedIn(): boolean {
  try {
    return window.localStorage.getItem(STORAGE_KEY) === '1'
  } catch {
    return false
  }
}

export function setDemoLoggedIn(loggedIn: boolean): void {
  try {
    if (loggedIn) window.localStorage.setItem(STORAGE_KEY, '1')
    else window.localStorage.removeItem(STORAGE_KEY)
  } catch {
    // Private browsing / storage blocked: the demo simply won't remember
    // login across reloads, which is an acceptable degradation here.
  }
}
