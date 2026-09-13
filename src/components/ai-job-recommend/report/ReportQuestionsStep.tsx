import type { PriorityItem } from '../../../lib/priorityUnresolved'
import { CompanyQuestionsPanel } from '../CompanyQuestionsPanel'

const MAX_QUESTIONS = 3

/** Selects up to three unique verification-action prompts from the already
 * computed priority list, in the same deterministic order. Never generates
 * a new prompt or rewrites an existing one -- purely a display-count cap
 * (TASK "단계형 리포트 모달" section "4단계": "질문 최대 3개"). */
function topThreeQuestionItems(items: PriorityItem[]): PriorityItem[] {
  const seen = new Set<string>()
  const result: PriorityItem[] = []
  for (const item of items) {
    if (!item.action) continue
    const key = `${item.region}:${item.action.prompt}`
    if (seen.has(key)) continue
    seen.add(key)
    result.push(item)
    if (result.length === MAX_QUESTIONS) break
  }
  return result
}

interface ReportQuestionsStepProps {
  items: PriorityItem[]
  metroLabel: string
  jeonbukLabel: string
}

/**
 * Report step 4/6 -- "담당자에게 그대로 물어보세요". A thin wrapper around
 * the existing CompanyQuestionsPanel (checkbox list + copy + opt-in personal
 * note) so the checkbox/copy/note logic is not duplicated here.
 */
export function ReportQuestionsStep({ items, metroLabel, jeonbukLabel }: ReportQuestionsStepProps) {
  const capped = topThreeQuestionItems(items)
  if (capped.length === 0) {
    return (
      <p className="rounded-card border border-ink-border bg-white p-4 text-sm text-ink-500">
        현재 확인이 필요한 조건이 없어 기업에 물어볼 질문도 없습니다.
      </p>
    )
  }
  return <CompanyQuestionsPanel items={capped} metroLabel={metroLabel} jeonbukLabel={jeonbukLabel} />
}
