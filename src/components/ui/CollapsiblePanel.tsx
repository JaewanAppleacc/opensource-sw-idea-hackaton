import { ChevronDown, ChevronUp } from 'lucide-react'
import { useId, useState } from 'react'
import type { ReactNode } from 'react'

interface CollapsiblePanelProps {
  label: string
  children: ReactNode
  defaultOpen?: boolean
}

/** Generic collapsed-by-default section with a toggle button, used to keep
 * advanced/secondary features (e.g. the finance comparison) out of the main
 * flow until the user opts in. */
export function CollapsiblePanel({ label, children, defaultOpen = false }: CollapsiblePanelProps) {
  const [open, setOpen] = useState(defaultOpen)
  const contentId = useId()

  return (
    <div className="rounded-card border border-ink-border bg-white">
      <button
        type="button"
        onClick={() => setOpen((v) => !v)}
        aria-expanded={open}
        aria-controls={contentId}
        className="flex w-full items-center justify-between gap-2 px-5 py-4 text-left text-sm font-bold text-ink-900"
      >
        {label}
        {open ? (
          <ChevronUp size={18} aria-hidden="true" className="shrink-0 text-ink-500" />
        ) : (
          <ChevronDown size={18} aria-hidden="true" className="shrink-0 text-ink-500" />
        )}
      </button>
      {open && (
        <div id={contentId} className="border-t border-ink-border p-5">
          {children}
        </div>
      )}
    </div>
  )
}
