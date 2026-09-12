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

/** "우선 확인할 조건" -- deterministic ordering only (see
 * src/lib/priorityUnresolved.ts). Never re-ranked by an LLM. Shown above
 * the full six-axis comparison so the highest-signal gaps read first. */
export function PriorityUnresolvedPanel({ items, metroLabel, jeonbukLabel }: PriorityUnresolvedPanelProps) {
  if (items.length === 0) {
    return <p className="text-sm text-ink-500">선택한 조건에서 확인이 필요한 정보가 발견되지 않았습니다.</p>
  }

  const top = items.slice(0, 3)

  return (
    <div>
      <p className="flex items-center gap-1.5 text-sm font-bold text-ink-900">
        <AlertCircle size={15} aria-hidden="true" className="text-amber-600" />
        우선 확인할 조건
      </p>
      <ol className="mt-2 space-y-1.5 text-sm text-ink-700">
        {top.map((item, i) => (
          <li key={`${item.region}-${item.axisId}-${item.subLabel}-${i}`} className="flex gap-2">
            <span className="font-semibold text-amber-700">{i + 1}.</span>
            <span>
              {item.region === 'metro' ? metroLabel : jeonbukLabel} · {item.axisLabel} — {item.subLabel} (
              {STATUS_TEXT[item.status]})
            </span>
          </li>
        ))}
      </ol>
    </div>
  )
}
