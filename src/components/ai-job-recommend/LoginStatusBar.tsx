import { LogIn, LogOut } from 'lucide-react'
import { DEMO_PROFILE } from '../../lib/demoAuth'

interface LoginStatusBarProps {
  loggedIn: boolean
  onLogin: () => void
  onLogout: () => void
}

/**
 * Demo-only login + compact profile summary. Folds the former separate
 * JobCareProfilePanel card into a single one/two-line row once logged in
 * (TASK "UI 고도화" section 7) -- 잡케어 관심 정보 is presented as profile
 * context, not its own step or its own card. Never implies a real
 * authentication system or a real 잡케어 API call.
 */
export function LoginStatusBar({ loggedIn, onLogin, onLogout }: LoginStatusBarProps) {
  if (!loggedIn) {
    return (
      <div className="flex flex-wrap items-center justify-between gap-3 rounded-card border border-ink-border bg-surface-muted px-4 py-3 text-sm">
        <p className="text-ink-700">로그인하면 관심 생활권의 공고를 함께 비교할 수 있습니다.</p>
        <button
          type="button"
          onClick={onLogin}
          className="flex items-center gap-1.5 rounded-pill bg-brand-blue px-4 py-2 text-xs font-semibold text-white transition-colors duration-150 hover:bg-brand-blue-dark"
        >
          <LogIn size={14} aria-hidden="true" />
          전북 데모 프로필로 시작
        </button>
      </div>
    )
  }

  return (
    <div className="flex flex-wrap items-center justify-between gap-3 rounded-card border border-ink-border bg-surface-muted px-4 py-3 text-sm">
      <p className="text-ink-700">
        <span className="font-semibold text-ink-900">{DEMO_PROFILE.displayName}</span>
        <span className="mx-1.5 text-ink-border">·</span>
        관심 직무 {DEMO_PROFILE.interestedOccupation}
        <span className="mx-1.5 text-ink-border">·</span>
        희망 고용형태 {DEMO_PROFILE.interestedEmploymentType}
        <span className="mx-1.5 text-ink-border">·</span>
        생활권 {DEMO_PROFILE.homeRegionLabel}
      </p>
      <button
        type="button"
        onClick={onLogout}
        className="flex items-center gap-1.5 rounded-pill border border-ink-border bg-white px-3 py-1.5 text-xs font-medium text-ink-500 transition-colors duration-150 hover:border-brand-blue hover:text-brand-blue"
      >
        <LogOut size={13} aria-hidden="true" />
        로그아웃
      </button>
    </div>
  )
}
