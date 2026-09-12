import { Info } from 'lucide-react'

/**
 * Collapsed info panel (native <details>, per TASK section 4's "과도한
 * 설명문 대신 툴팁 또는 접힌 안내 패널") distinguishing this extension layer
 * from both 고용24 AI추천 and 고용24's existing AI 구인공고 검증. Kept short
 * -- this is a disclosure, not a marketing pitch, and it must never imply a
 * separate competing platform.
 */
export function ServiceDifferentiationNotice() {
  return (
    <details className="group rounded-card border border-ink-border bg-white p-3 text-xs text-ink-600">
      <summary className="flex cursor-pointer list-none items-center gap-1.5 font-semibold text-ink-700 marker:content-none">
        <Info size={13} aria-hidden="true" className="shrink-0 text-brand-blue" />
        고용24 AI추천과 지역 선택 보정 에이전트는 어떻게 다른가요?
      </summary>
      <div className="mt-3 space-y-3">
        <div className="grid grid-cols-1 gap-2 sm:grid-cols-2">
          <div className="rounded-card bg-surface-muted p-2.5">
            <p className="font-semibold text-ink-900">고용24 AI추천</p>
            <p className="mt-0.5 text-ink-500">사람과 일자리의 적합성을 분석</p>
          </div>
          <div className="rounded-card bg-tint-sky/20 p-2.5">
            <p className="font-semibold text-ink-900">지역 선택 보정 에이전트</p>
            <p className="mt-0.5 text-ink-500">수도권과 자기 지역 일자리의 비교 가능성을 분석</p>
          </div>
        </div>
        <div>
          <p className="font-semibold text-ink-700">기존 AI 구인공고 검증과도 다릅니다</p>
          <div className="mt-1.5 grid grid-cols-1 gap-2 sm:grid-cols-2">
            <div className="rounded-card bg-surface-muted p-2.5">
              <p className="font-semibold text-ink-900">기존 검증</p>
              <p className="mt-0.5 text-ink-500">차별 표현·최저임금 등 법 위반 가능성 확인</p>
            </div>
            <div className="rounded-card bg-tint-sky/20 p-2.5">
              <p className="font-semibold text-ink-900">우리의 검증</p>
              <p className="mt-0.5 text-ink-500">
                지원자가 지역 간 조건을 판단할 수 있을 만큼 공고 정보가 충분한지 확인
              </p>
            </div>
          </div>
        </div>
        <p className="text-ink-400">
          별도 플랫폼이 아니라, 고용24 AI추천 결과 위에 자기 지역 비교 단계를 추가하는 확장 기능입니다.
        </p>
      </div>
    </details>
  )
}
