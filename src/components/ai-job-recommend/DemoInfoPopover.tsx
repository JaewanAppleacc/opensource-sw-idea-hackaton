import { Info } from 'lucide-react'

/**
 * Compact "DEMO · 전북" status chip with a click-to-reveal disclosure
 * popover. Replaces the always-visible DemoModeNotice + ServiceDifferentiationNotice
 * pair on this page (TASK "UI 고도화" section 5): the same required
 * disclosures stay verbatim and always reachable, just not spread across
 * the main screen as two separate boxes. DemoModeNotice itself is left
 * untouched for ManualAnalysisPage, which still renders it directly.
 */
export function DemoInfoPopover() {
  return (
    <details className="group relative">
      <summary
        className="flex w-fit cursor-pointer list-none items-center gap-1 rounded-pill border border-ink-border bg-surface-muted px-2.5 py-1 text-[11px] font-semibold text-ink-500 transition hover:border-brand-blue hover:text-brand-blue marker:content-none"
        aria-label="시연 안내 자세히 보기"
      >
        <span className="h-1.5 w-1.5 rounded-full bg-brand-blue" aria-hidden="true" />
        DEMO · 전북
        <Info size={12} aria-hidden="true" />
      </summary>
      <div className="absolute right-0 z-20 mt-2 w-[19rem] space-y-3 rounded-card border border-ink-border bg-white p-4 text-xs leading-relaxed text-ink-600 shadow-soft sm:w-80">
        <p className="font-semibold text-ink-900">데모 모드 · 사전 검증된 분석 결과</p>
        <p>
          본 서비스는 고용24 공식 서비스가 아닌 해커톤 시연용 프로토타입입니다. 6개 항목 분석은 결정론적(mock)
          추출기와 실제 백엔드 검증 로직(스키마·근거·규칙 보정)으로 동작하며, 실시간 Anthropic/NVIDIA 호출은
          사용하지 않습니다.
        </p>
        <ul className="list-disc space-y-1 pl-4 text-ink-500">
          <li>전북 비교 공고는 동일하게 정규화한 모집직종·고용형태 기준이며, 유사도 순위가 아닙니다.</li>
          <li>
            잡케어 연동은 해커톤 시연용 프로필이며, 실제 잡케어 API와 연동되지 않았습니다. 취업확률·역량점수·심리검사
            결과는 제공하지 않습니다.
          </li>
        </ul>
        <div className="grid grid-cols-1 gap-2 border-t border-ink-border pt-3 sm:grid-cols-2">
          <div className="rounded-card bg-surface-muted p-2.5">
            <p className="font-semibold text-ink-900">고용24 AI추천</p>
            <p className="mt-0.5 text-ink-500">사람과 일자리의 적합성을 분석</p>
          </div>
          <div className="rounded-card bg-tint-sky/20 p-2.5">
            <p className="font-semibold text-ink-900">지역 선택 보정 에이전트</p>
            <p className="mt-0.5 text-ink-500">수도권과 자기 지역 일자리의 비교 가능성을 분석</p>
          </div>
        </div>
        <p className="text-ink-400">
          별도 플랫폼이 아니라, 고용24 AI추천 결과 위에 자기 지역 비교 단계를 추가하는 확장 기능입니다.
        </p>
      </div>
    </details>
  )
}
