import { Briefcase, Info, MapPin, UserCheck } from 'lucide-react'
import { DEMO_PROFILE, JOBCARE_DEMO_DISCLAIMER } from '../../lib/demoAuth'

/**
 * Demo-only stand-in for a "잡케어(JobCare) 분석 결과" hand-off (TASK
 * section 3). The real JobCare API is never called from this codebase --
 * this panel only ever shows three fixed demo values (관심 직무/관심
 * 고용형태/관심 생활권) plus an explicit disclaimer. It never renders a
 * 취업확률, 역량점수, or 심리검사 result, real or fabricated: those concepts
 * do not appear anywhere in this component or in `DEMO_PROFILE`.
 */
export function JobCareProfilePanel() {
  return (
    <div className="rounded-card border border-ink-border bg-surface-muted p-4 text-sm">
      <p className="flex items-center gap-1.5 font-semibold text-ink-900">
        <UserCheck size={15} aria-hidden="true" className="text-brand-indigo" />
        잡케어 연결 (시연용 프로필)
      </p>
      <dl className="mt-2 space-y-1.5 text-ink-700">
        <div className="flex items-center gap-1.5">
          <Briefcase size={13} aria-hidden="true" className="shrink-0 text-ink-400" />
          <dt className="text-ink-500">관심 직무</dt>
          <dd className="font-medium text-ink-900">{DEMO_PROFILE.interestedOccupation}</dd>
        </div>
        <div className="flex items-center gap-1.5">
          <Briefcase size={13} aria-hidden="true" className="shrink-0 text-ink-400" />
          <dt className="text-ink-500">관심 고용형태</dt>
          <dd className="font-medium text-ink-900">{DEMO_PROFILE.interestedEmploymentType}</dd>
        </div>
        <div className="flex items-center gap-1.5">
          <MapPin size={13} aria-hidden="true" className="shrink-0 text-ink-400" />
          <dt className="text-ink-500">관심 생활권</dt>
          <dd className="font-medium text-ink-900">{DEMO_PROFILE.homeRegionLabel}</dd>
        </div>
      </dl>
      <p className="mt-3 flex items-start gap-1.5 text-[11px] text-ink-400">
        <Info size={12} aria-hidden="true" className="mt-0.5 shrink-0" />
        {JOBCARE_DEMO_DISCLAIMER} 실제 잡케어 API와 연동되지 않았으며, 취업확률·역량점수·심리검사 결과는
        제공하지 않습니다.
      </p>
    </div>
  )
}
