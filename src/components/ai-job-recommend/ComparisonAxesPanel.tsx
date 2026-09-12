import { HelpCircle, Quote, Star } from 'lucide-react'
import type { AxisId, AxisResult, AxisSubItemResult } from '../../lib/comparisonAxes'
import { WORK_CONDITIONS_UNSUPPORTED_MESSAGE } from '../../lib/comparisonAxes'
import { CHANNEL_LABELS, STATUS_LABELS } from '../../lib/displayLabels'

const STATUS_STYLES: Record<string, string> = {
  confirmed: 'bg-tint-mint/60 text-brand-green',
  vague: 'bg-amber-100 text-amber-700',
  absent: 'bg-surface-muted text-ink-500',
}

function SubItemRow({ item }: { item: AxisSubItemResult }) {
  const status = item.audited?.status
  const isWorkConditionsPlaceholder = item.sourceField === null
  return (
    <div className="border-t border-ink-border pt-2 first:border-t-0 first:pt-0">
      <div className="flex flex-wrap items-center gap-1.5">
        <span className="text-xs font-semibold text-ink-700">{item.subLabel}</span>
        {status && (
          <span className={`rounded-pill px-1.5 py-0.5 text-[10px] font-medium ${STATUS_STYLES[status]}`}>
            {STATUS_LABELS[status]}
          </span>
        )}
      </div>
      <p className="mt-1 text-xs text-ink-700">
        {isWorkConditionsPlaceholder ? (
          <span className="text-ink-400">{WORK_CONDITIONS_UNSUPPORTED_MESSAGE}</span>
        ) : item.audited?.evidence ? (
          <span className="flex items-start gap-1 text-ink-700">
            <Quote size={11} aria-hidden="true" className="mt-0.5 shrink-0 text-ink-400" />
            <span>&ldquo;{item.audited.evidence.text}&rdquo;</span>
          </span>
        ) : (
          <span className="text-ink-400">근거 문구 없음</span>
        )}
      </p>
      {item.action && (
        <p className="mt-1 flex items-start gap-1 rounded-card bg-surface-muted p-1.5 text-[11px] text-ink-500">
          <HelpCircle size={11} aria-hidden="true" className="mt-0.5 shrink-0 text-brand-blue" />
          <span>
            ({CHANNEL_LABELS[item.action.channel]}) {item.action.prompt}
          </span>
        </p>
      )}
    </div>
  )
}

function AxisColumn({ label, axis }: { label: string; axis: AxisResult }) {
  return (
    <div>
      <p className="text-[11px] font-semibold text-ink-500">{label}</p>
      <div className="mt-1.5 space-y-2">
        {axis.subItems.map((item, i) => (
          <SubItemRow key={`${axis.id}-${i}`} item={item} />
        ))}
      </div>
    </div>
  )
}

interface ComparisonAxesPanelProps {
  metroLabel: string
  jeonbukLabel: string
  metroAxes: AxisResult[]
  jeonbukAxes: AxisResult[]
  selectedAxisIds: AxisId[]
}

/** Six-axis side-by-side comparison, replacing the flat six-field list.
 * Selected axes are visually emphasized and moved to the top; nothing here
 * computes or displays a combined score or a winner. */
export function ComparisonAxesPanel({
  metroLabel,
  jeonbukLabel,
  metroAxes,
  jeonbukAxes,
  selectedAxisIds,
}: ComparisonAxesPanelProps) {
  const byId = (axes: AxisResult[]) => new Map(axes.map((a) => [a.id, a]))
  const metroById = byId(metroAxes)
  const jeonbukById = byId(jeonbukAxes)

  const orderedIds = [
    ...selectedAxisIds,
    ...metroAxes.map((a) => a.id).filter((id) => !selectedAxisIds.includes(id)),
  ]

  return (
    <div className="space-y-3">
      {orderedIds.map((id) => {
        const metroAxis = metroById.get(id)
        const jeonbukAxis = jeonbukById.get(id)
        if (!metroAxis || !jeonbukAxis) return null
        const isSelected = selectedAxisIds.includes(id)
        return (
          <div
            key={id}
            className={`rounded-card border p-3 ${
              isSelected ? 'border-brand-blue bg-tint-sky/10' : 'border-ink-border bg-white'
            }`}
          >
            <p className="flex items-center gap-1.5 text-sm font-bold text-ink-900">
              {isSelected && <Star size={13} aria-hidden="true" className="fill-brand-blue text-brand-blue" />}
              {metroAxis.label}
            </p>
            <div className="mt-2 grid grid-cols-1 gap-4 sm:grid-cols-2">
              <AxisColumn label={metroLabel} axis={metroAxis} />
              <AxisColumn label={jeonbukLabel} axis={jeonbukAxis} />
            </div>
          </div>
        )
      })}
    </div>
  )
}
