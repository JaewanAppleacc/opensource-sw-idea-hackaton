import { FlaskConical } from 'lucide-react'

/**
 * Always-visible demo/mock transparency notice for the AI job recommend
 * flow. Required verbatim strings (see TASK section 7):
 *   - "데모 모드 · 사전 검증된 분석 결과" badge
 *   - "본 서비스는 고용24 공식 서비스가 아닌 해커톤 시연용 프로토타입입니다." disclaimer
 */
export function DemoModeNotice() {
  return (
    <div className="flex flex-col gap-2 rounded-card border border-brand-blue/30 bg-tint-sky/40 p-4 text-sm">
      <span className="inline-flex w-fit items-center gap-1.5 rounded-pill bg-brand-blue px-3 py-1 text-xs font-bold text-white">
        <FlaskConical size={14} aria-hidden="true" />
        데모 모드 · 사전 검증된 분석 결과
      </span>
      <p className="text-ink-500">
        본 서비스는 고용24 공식 서비스가 아닌 해커톤 시연용 프로토타입입니다. 6개 항목 분석은 결정론적(mock)
        추출기와 실제 백엔드 검증 로직(스키마·근거·규칙 보정)으로 동작하며, 실시간 Anthropic/NVIDIA 호출은
        사용하지 않습니다.
      </p>
    </div>
  )
}
