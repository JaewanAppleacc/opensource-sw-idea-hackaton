import { AlertCircle } from 'lucide-react'
import type { PriorityItem } from '../../../lib/priorityUnresolved'

const MAX_SHOWN = 4

// Short, plain-language sentences for the small fixed set of sub-labels the
// six comparison axes ever produce (see comparisonAxes.ts realSubItem calls).
// Presentation-only: never changes which items are selected or their order
// -- that ordering is entirely buildPriorityUnresolvedList's (TASK "단계형
// 리포트 모달" section 3: "기존 priorityUnresolved 로직을 그대로 재사용").
const ABSENT_SENTENCES: Record<string, string> = {
  '연봉·월급·수당': '급여 정보가 공고에 나와 있지 않아요.',
  '수습 중 급여': '수습 중 급여가 명시되지 않았어요.',
  '정규직·계약직·계약기간': '고용형태 세부조건이 명시되지 않았어요.',
  수습기간: '수습기간이 명시되지 않았어요.',
  '실제 수행 업무': '실제 담당업무가 공고에 나와 있지 않아요.',
  '기술·도구·자격증': '필요한 기술·자격 요건이 나와 있지 않아요.',
  '교육·성장 지원 (OJT·멘토링)': '입사 후 교육 방식이 나와 있지 않아요.',
}
const VAGUE_SENTENCES: Record<string, string> = {
  '연봉·월급·수당': '급여 관련 언급은 있지만 판단하기엔 부족해요.',
  '수습 중 급여': '수습 중 급여가 언급됐지만 구체적이지 않아요.',
  '정규직·계약직·계약기간': '고용형태가 언급됐지만 세부조건은 불명확해요.',
  수습기간: '수습기간이 언급됐지만 구체적이지 않아요.',
  '실제 수행 업무': '담당업무가 언급됐지만 구체적이지 않아요.',
  '기술·도구·자격증': '기술·자격 요건이 언급됐지만 구체적이지 않아요.',
  '교육·성장 지원 (OJT·멘토링)': '입사 후 교육 방식이 구체적이지 않아요.',
}

function sentenceFor(item: PriorityItem): string {
  const table = item.status === 'absent' ? ABSENT_SENTENCES : VAGUE_SENTENCES
  return (
    table[item.subLabel] ??
    (item.status === 'absent'
      ? `${item.subLabel} 정보가 공고에 나와 있지 않아요.`
      : `${item.subLabel}이(가) 언급됐지만 구체적이지 않아요.`)
  )
}

interface ReportUnknownsStepProps {
  items: PriorityItem[]
  metroLabel: string
  jeonbukLabel: string
}

/**
 * Report step 3/6 -- "결정 전에 이 정보는 꼭 확인하세요". Shows only the top
 * 3-4 items from the already-computed, deterministic priority list
 * (src/lib/priorityUnresolved.ts) as short plain sentences. `not_evaluated`
 * sub-items never appear here -- that list structurally excludes them.
 */
export function ReportUnknownsStep({ items, metroLabel, jeonbukLabel }: ReportUnknownsStepProps) {
  const top = items.slice(0, MAX_SHOWN)

  if (top.length === 0) {
    return (
      <p className="rounded-card border border-ink-border bg-white p-4 text-sm text-ink-500">
        선택한 조건에서 확인이 필요한 정보가 발견되지 않았습니다.
      </p>
    )
  }

  return (
    <ul className="space-y-2.5">
      {top.map((item, i) => (
        <li
          key={`${item.region}-${item.axisId}-${item.subLabel}-${i}`}
          className="report-card-stagger flex items-start gap-3 rounded-card border border-ink-border bg-white p-3"
          style={{ animationDelay: `${i * 40}ms` }}
        >
          <AlertCircle size={16} aria-hidden="true" className="mt-0.5 shrink-0 text-amber-600" />
          <span>
            <span className="block text-[11px] font-semibold text-ink-400">
              {item.region === 'metro' ? metroLabel : jeonbukLabel} · {item.axisLabel}
            </span>
            <span className="mt-0.5 block text-sm text-ink-900">{sentenceFor(item)}</span>
          </span>
        </li>
      ))}
    </ul>
  )
}
