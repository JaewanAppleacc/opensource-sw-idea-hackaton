/**
 * Demo-only "login" profile for the hackathon prototype.
 *
 * This is NOT real authentication and collects NO personal data: no address,
 * phone number, or email is ever requested or stored. It exists only to
 * make the "logged-in user's home region is Jeonbuk" premise visible on
 * screen, per TASK section 3.
 *
 * If localStorage is used at all, it stores only the demo region code and
 * its display label -- nothing else.
 */

export type HomeRegionCode = 'JEONBUK'

export interface DemoProfile {
  displayName: string
  homeRegion: HomeRegionCode
  homeRegionLabel: string
  isDemoProfile: true
}

export const DEMO_PROFILE: DemoProfile = {
  displayName: '전북 청년 데모 사용자',
  homeRegion: 'JEONBUK',
  homeRegionLabel: '전북특별자치도',
  isDemoProfile: true,
}

const STORAGE_KEY = 'work24-clone.demoProfile.homeRegion.v1'

interface StoredHomeRegion {
  homeRegion: HomeRegionCode
  homeRegionLabel: string
}

/**
 * Reads the demo profile. The display name and isDemoProfile flag are
 * always the fixed demo constant (there is no real account system); only
 * the home-region code/label are ever read from localStorage, and only if
 * present and well-formed.
 */
export function loadDemoProfile(): DemoProfile {
  try {
    const raw = window.localStorage.getItem(STORAGE_KEY)
    if (!raw) return DEMO_PROFILE
    const parsed = JSON.parse(raw) as Partial<StoredHomeRegion>
    if (parsed.homeRegion === 'JEONBUK' && typeof parsed.homeRegionLabel === 'string') {
      return { ...DEMO_PROFILE, homeRegion: parsed.homeRegion, homeRegionLabel: parsed.homeRegionLabel }
    }
    return DEMO_PROFILE
  } catch {
    // Private browsing, disabled storage, corrupt value, etc. -- fall back
    // to the fixed demo constant rather than throwing.
    return DEMO_PROFILE
  }
}

/** Persists only the demo region code and display label -- no other field. */
export function saveDemoProfile(homeRegion: HomeRegionCode, homeRegionLabel: string): void {
  try {
    const value: StoredHomeRegion = { homeRegion, homeRegionLabel }
    window.localStorage.setItem(STORAGE_KEY, JSON.stringify(value))
  } catch {
    // Ignore storage failures; the fixed demo constant remains usable.
  }
}
