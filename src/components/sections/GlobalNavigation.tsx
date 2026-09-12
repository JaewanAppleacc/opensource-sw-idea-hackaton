import { ChevronDown, Menu } from 'lucide-react'
import { useRef, useState } from 'react'
import { Container } from '../ui/Container'
import { navigationMenu } from '../../data/navigation'
import { useOnClickOutside } from '../../hooks/useOnClickOutside'
import type { NavMenuItem } from '../../types'

interface NavDropdownProps {
  item: NavMenuItem
  isOpen: boolean
  onOpen: () => void
  onClose: () => void
}

function NavDropdown({ item, isOpen, onOpen, onClose }: NavDropdownProps) {
  const closeTimer = useRef<ReturnType<typeof setTimeout> | null>(null)
  const rootRef = useRef<HTMLDivElement>(null)

  useOnClickOutside(rootRef, onClose, isOpen)

  function handleMouseEnter() {
    if (closeTimer.current) clearTimeout(closeTimer.current)
    onOpen()
  }

  function handleMouseLeave() {
    closeTimer.current = setTimeout(onClose, 150)
  }

  function handleKeyDown(event: React.KeyboardEvent) {
    if (event.key === 'Escape') {
      onClose()
      ;(event.currentTarget.querySelector('a,button') as HTMLElement | null)?.focus()
    }
    if (event.key === 'ArrowDown' && !isOpen) {
      event.preventDefault()
      onOpen()
    }
  }

  return (
    <div
      ref={rootRef}
      className="relative"
      onMouseEnter={handleMouseEnter}
      onMouseLeave={handleMouseLeave}
      onKeyDown={handleKeyDown}
    >
      <button
        type="button"
        aria-expanded={isOpen}
        aria-haspopup="true"
        onClick={() => (isOpen ? onClose() : onOpen())}
        className="flex items-center gap-2 py-4 text-[17px] font-semibold text-ink-900 transition hover:text-brand-blue focus-visible:text-brand-blue"
      >
        {item.label}
        <ChevronDown
          size={16}
          aria-hidden="true"
          className={`transition-transform ${isOpen ? 'rotate-180 text-brand-blue' : ''}`}
        />
      </button>

      {isOpen && (
        <div className="absolute left-1/2 top-full z-40 w-64 -translate-x-1/2 rounded-card border border-ink-border bg-white p-2 shadow-softer">
          <ul>
            {item.children.map((child) => (
              <li key={child.id}>
                <a
                  href={child.href}
                  className="block rounded-lg px-3 py-2 transition hover:bg-surface-muted focus-visible:bg-surface-muted"
                >
                  <span className="block text-sm font-medium text-ink-900">{child.label}</span>
                  {child.description && (
                    <span className="mt-0.5 block text-xs text-ink-400">{child.description}</span>
                  )}
                </a>
              </li>
            ))}
          </ul>
        </div>
      )}
    </div>
  )
}

interface GlobalNavigationProps {
  onOpenAllMenu: () => void
}

export function GlobalNavigation({ onOpenAllMenu }: GlobalNavigationProps) {
  const [openId, setOpenId] = useState<string | null>(null)

  return (
    <nav aria-label="주 메뉴" id="gnb" className="hidden border-t border-ink-border lg:block">
      <Container className="flex items-center justify-between">
        <ul className="flex items-center gap-12">
          {navigationMenu.map((item) => (
            <li key={item.id}>
              <NavDropdown
                item={item}
                isOpen={openId === item.id}
                onOpen={() => setOpenId(item.id)}
                onClose={() => setOpenId((current) => (current === item.id ? null : current))}
              />
            </li>
          ))}
        </ul>

        <button
          type="button"
          onClick={onOpenAllMenu}
          className="flex items-center gap-2 py-4 text-base font-semibold text-ink-700 transition hover:text-brand-blue"
        >
          <Menu size={18} aria-hidden="true" />
          전체 메뉴
        </button>
      </Container>
    </nav>
  )
}
