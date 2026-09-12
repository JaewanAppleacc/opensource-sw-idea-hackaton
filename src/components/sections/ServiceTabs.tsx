import { Container } from '../ui/Container'
import { serviceTabs } from '../../data/tabs'
import type { ServiceTabId } from '../../types'

interface ServiceTabsProps {
  activeTab: ServiceTabId
  onChange: (id: ServiceTabId) => void
}

export function ServiceTabs({ activeTab, onChange }: ServiceTabsProps) {
  function handleKeyDown(event: React.KeyboardEvent, index: number) {
    if (event.key !== 'ArrowRight' && event.key !== 'ArrowLeft') return
    event.preventDefault()
    const delta = event.key === 'ArrowRight' ? 1 : -1
    const nextIndex = (index + delta + serviceTabs.length) % serviceTabs.length
    const next = serviceTabs[nextIndex]!
    onChange(next.id)
    ;(document.getElementById(`service-tab-${next.id}`) as HTMLElement | null)?.focus()
  }

  return (
    <Container className="relative">
      <div
        role="tablist"
        aria-label="고용24 개인 서비스 분류"
        className="mx-auto flex max-w-2xl flex-wrap justify-center rounded-2xl border border-white/80 bg-white/65 p-2 shadow-soft backdrop-blur-md sm:flex-nowrap"
      >
        {serviceTabs.map((tab, index) => (
          <button
            key={tab.id}
            id={`service-tab-${tab.id}`}
            type="button"
            role="tab"
            aria-selected={activeTab === tab.id}
            aria-controls="quick-service-panel"
            tabIndex={activeTab === tab.id ? 0 : -1}
            onClick={() => onChange(tab.id)}
            onKeyDown={(e) => handleKeyDown(e, index)}
            className={`flex-1 whitespace-nowrap rounded-xl px-3 py-3 text-xs font-semibold transition sm:flex-initial sm:px-5 sm:text-base ${
              activeTab === tab.id
                ? 'bg-brand-blue text-white shadow-soft'
                : 'text-ink-500 hover:bg-white hover:text-brand-blue'
            }`}
          >
            {tab.label}
          </button>
        ))}
      </div>
    </Container>
  )
}
