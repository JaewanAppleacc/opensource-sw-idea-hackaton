import { LogIn, LogOut, MapPin, UserCircle2 } from 'lucide-react'
import { DEMO_PROFILE } from '../../lib/demoAuth'

interface LoginStatusBarProps {
  loggedIn: boolean
  onLogin: () => void
  onLogout: () => void
}

/**
 * Demo-only login/region status bar. Never implies a real authentication
 * system -- see src/lib/demoAuth.ts. Copy strings are verbatim per the
 * task's UI requirements.
 */
export function LoginStatusBar({ loggedIn, onLogin, onLogout }: LoginStatusBarProps) {
  if (!loggedIn) {
    return (
      <div className="flex flex-wrap items-center justify-between gap-3 rounded-card border border-ink-border bg-surface-muted p-4 text-sm">
        <p className="text-ink-700">로그인하면 관심 생활권의 비교 공고를 확인할 수 있습니다.</p>
        <button
          type="button"
          onClick={onLogin}
          className="flex items-center gap-1.5 rounded-pill bg-brand-blue px-4 py-2 text-xs font-semibold text-white transition hover:bg-brand-blue-dark active:scale-95"
        >
          <LogIn size={14} aria-hidden="true" />
          데모 로그인 (전북 청년 프로필)
        </button>
      </div>
    )
  }

  return (
    <div className="space-y-2 rounded-card border border-brand-blue/30 bg-tint-sky/30 p-4 text-sm">
      <div className="flex flex-wrap items-center justify-between gap-3">
        <div className="flex items-center gap-2 text-ink-900">
          <UserCircle2 size={18} aria-hidden="true" className="text-brand-blue" />
          <span className="font-semibold">로그인 사용자: {DEMO_PROFILE.displayName}</span>
        </div>
        <button
          type="button"
          onClick={onLogout}
          className="flex items-center gap-1.5 rounded-pill border border-ink-border bg-white px-3 py-1.5 text-xs font-medium text-ink-500 transition hover:border-brand-blue hover:text-brand-blue"
        >
          <LogOut size={13} aria-hidden="true" />
          로그아웃
        </button>
      </div>
      <p className="flex items-center gap-1.5 text-ink-700">
        <MapPin size={13} aria-hidden="true" className="text-brand-blue" />내 관심 생활권: {DEMO_PROFILE.homeRegionLabel}
      </p>
      <p className="text-xs text-ink-500">현재 {DEMO_PROFILE.homeRegionLabel}를 기준으로 비교하고 있습니다.</p>
    </div>
  )
}
