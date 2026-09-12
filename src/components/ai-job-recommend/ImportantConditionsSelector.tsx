import { AXIS_LABELS, AXIS_ORDER, AXIS_SUBITEM_HINTS, type AxisId } from '../../lib/comparisonAxes'

const MAX_SELECTED = 3

interface ImportantConditionsSelectorProps {
  selected: AxisId[]
  onChange: (next: AxisId[]) => void
}

export function ImportantConditionsSelector({ selected, onChange }: ImportantConditionsSelectorProps) {
  function toggle(id: AxisId) {
    if (selected.includes(id)) {
      onChange(selected.filter((s) => s !== id))
    } else if (selected.length < MAX_SELECTED) {
      onChange([...selected, id])
    }
  }

  return (
    <div>
      <p className="text-sm font-bold text-ink-900">중요하게 생각하는 조건을 선택해 주세요</p>
      <p className="mt-0.5 text-xs text-ink-400">
        최대 {MAX_SELECTED}개까지 선택할 수 있어요. ({selected.length}/{MAX_SELECTED})
      </p>
      <ul className="mt-3 grid grid-cols-1 gap-2 sm:grid-cols-2">
        {AXIS_ORDER.map((id) => {
          const checked = selected.includes(id)
          const disabled = !checked && selected.length >= MAX_SELECTED
          return (
            <li key={id}>
              <label
                className={`flex items-start gap-2 rounded-card border p-3 text-sm transition ${
                  checked ? 'border-brand-blue bg-tint-sky/20' : 'border-ink-border bg-white'
                } ${disabled ? 'opacity-50' : 'cursor-pointer hover:border-brand-blue'}`}
              >
                <input
                  type="checkbox"
                  checked={checked}
                  disabled={disabled}
                  onChange={() => toggle(id)}
                  className="mt-0.5"
                />
                <span>
                  <span className="block font-semibold text-ink-900">{AXIS_LABELS[id]}</span>
                  <span className="block text-xs text-ink-400">{AXIS_SUBITEM_HINTS[id]}</span>
                </span>
              </label>
            </li>
          )
        })}
      </ul>
    </div>
  )
}
