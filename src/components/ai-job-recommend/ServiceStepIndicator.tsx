import { Check } from 'lucide-react'

const STEPS = ['잡케어 관심직무', '고용24 AI추천', '내 지역 비교', '지원 전 확인'] as const

interface ServiceStepIndicatorProps {
  /** 1-4. The step this indicator instance is currently emphasizing. Steps
   * before it render as done, steps after as upcoming -- this is a purely
   * presentational progress marker, never a gate on what the user can
   * click. */
  currentStep: 1 | 2 | 3 | 4
  className?: string
}

/**
 * Small ①②③④ step strip (TASK section 6) that frames the region-comparison
 * agent as an extension of the existing 고용24 AI추천 flow, never as a
 * separate platform. Rendered once at the page level for steps 1-2 (잡케어
 * 프로필 표시 -> AI추천 목록), and again inside each posting card for steps
 * 3-4 once that card's own comparison agent is expanded.
 */
export function ServiceStepIndicator({ currentStep, className = '' }: ServiceStepIndicatorProps) {
  return (
    <ol className={`flex flex-wrap items-center gap-x-1 gap-y-1.5 text-[11px] ${className}`}>
      {STEPS.map((label, i) => {
        const step = (i + 1) as 1 | 2 | 3 | 4
        const isDone = step < currentStep
        const isCurrent = step === currentStep
        return (
          <li key={label} className="flex items-center gap-1">
            <span
              className={`flex items-center gap-1 rounded-pill px-2 py-0.5 font-semibold transition ${
                isCurrent
                  ? 'bg-brand-blue text-white'
                  : isDone
                    ? 'bg-tint-mint/60 text-brand-green'
                    : 'bg-surface-muted text-ink-400'
              }`}
            >
              {isDone ? <Check size={10} aria-hidden="true" /> : <span>{step}</span>}
              {label}
            </span>
            {step < 4 && <span className="text-ink-300">→</span>}
          </li>
        )
      })}
    </ol>
  )
}
