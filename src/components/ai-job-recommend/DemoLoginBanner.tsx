import { UserCircle2 } from 'lucide-react'
import type { DemoProfile } from '../../lib/demoProfile'

interface DemoLoginBannerProps {
  profile: DemoProfile
}

/**
 * Shows the demo "logged-in" profile (TASK section 3). This is not real
 * authentication -- no address, phone number, or email is ever collected --
 * it only makes the "the current user's home living zone is Jeonbuk" premise
 * visible so the region-comparison flow reads naturally.
 */
export function DemoLoginBanner({ profile }: DemoLoginBannerProps) {
  return (
    <div className="flex flex-wrap items-center gap-3 rounded-card border border-ink-border bg-surface-muted p-4">
      <span className="flex h-10 w-10 shrink-0 items-center justify-center rounded-full bg-white text-brand-blue">
        <UserCircle2 size={24} aria-hidden="true" />
      </span>
      <div className="text-sm">
        <p className="font-bold text-ink-900">
          {profile.displayName}
          <span className="ml-2 rounded-pill bg-ink-border px-2 py-0.5 text-[11px] font-medium text-ink-500">
            데모 로그인
          </span>
        </p>
        <p className="mt-0.5 text-ink-500">
          관심 생활권: <strong className="font-semibold text-ink-700">{profile.homeRegionLabel}</strong>
        </p>
        <p className="mt-0.5 text-xs text-ink-400">
          {/* Exact wording required by TASK section 3. */}
          현재 {profile.homeRegionLabel}를 기준으로 내 지역 일자리를 비교합니다.
        </p>
      </div>
    </div>
  )
}
