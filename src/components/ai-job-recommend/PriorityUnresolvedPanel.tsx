import { AlertCircle } from 'lucide-react'
import type { PriorityItem } from '../../lib/priorityUnresolved'

interface PriorityUnresolvedPanelProps {
  items: PriorityItem[]
  metroLabel: string
  jeonbukLabel: string
}

const STATUS_TEXT: Record<'vague' | 'absent', string> = {
  absent: '공고에서 확인되지 않음',
  vague: '언급됐지만 판단하기 어려움',
}

/** "선택 전에 우선 확인할 정보" -- deterministic ordering only (see
 * src/lib/priorityUnresolved.ts). Never re-ranked by an LLM. */
export function PriorityUnresolvedPanel({ items, metroLabel, jeonbukLabel }: PriorityUnresolvedPanelProps) {
  if (items.length === 0) {
    return (
      <div className="rounded-card border border-ink-border bg-surface-muted p-4 text-sm text-ink-700">
        선택한 조건에서 확인이 필요한 정보가 발견되지 않았습니다.
      </div>
    )
  }

  return (
    <div className="rounded-card border border-amber-300 bg-amber-50 p-4">
      <p className="flex items-center gap-1.5 text-sm font-bold text-amber-800">
        <AlertCircle size={16} aria-hidden="true" />
        선택 전에 우선 확인할 정보
      </p>
      <ol className="mt-3 space-y-2 text-sm text-ink-700">
        {items.map((item, i) => (
          <li key={`${item.region}-${item.axisId}-${item.subLabel}-${i}`} className="flex gap-2">
            <span className="font-semibold text-amber-700">{i + 1}.</span>
            <span>
              {item.region === 'metro' ? metroLabel : jeonbukLabel} 공고의 {item.axisLabel} — {item.subLabel} (
              {STATUS_TEXT[item.status]})
            </span>
          </li>
        ))}
      </ol>
    </div>
  )
}
