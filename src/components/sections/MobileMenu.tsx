import { ChevronDown, LogIn, Search, UserPlus, X } from 'lucide-react'
import { useEffect } from 'react'
import { Logo } from '../ui/Logo'
import { useToast } from '../ui/ToastProvider'
import { navigationMenu } from '../../data/navigation'

interface MobileMenuProps {
  isOpen: boolean
  onClose: () => void
}

export function MobileMenu({ isOpen, onClose }: MobileMenuProps) {
  const { announce } = useToast()

  useEffect(() => {
    if (!isOpen) return
    document.body.style.overflow = 'hidden'
    function handleKey(event: KeyboardEvent) {
      if (event.key === 'Escape') onClose()
    }
    document.addEventListener('keydown', handleKey)
    return () => {
      document.body.style.overflow = ''
      document.removeEventListener('keydown', handleKey)
    }
  }, [isOpen, onClose])

  if (!isOpen) return null

  return (
    <div className="fixed inset-0 z-[60]">
      <button
        type="button"
        aria-label="배경 닫기"
        onClick={onClose}
        className="absolute inset-0 bg-black/40"
      />

      <div
        role="dialog"
        aria-modal="true"
        aria-label="전체 메뉴"
        className="absolute inset-y-0 left-0 flex w-[86%] max-w-sm flex-col overflow-y-auto bg-white shadow-softer"
      >
        <div className="flex items-center justify-between border-b border-ink-border p-4">
          <Logo />
          <button
            type="button"
            onClick={onClose}
            aria-label="메뉴 닫기"
            className="flex h-10 w-10 items-center justify-center rounded-full text-ink-700 transition hover:bg-surface-muted"
          >
            <X size={22} aria-hidden="true" />
          </button>
        </div>

        <div className="flex gap-2 border-b border-ink-border p-4">
          <button
            type="button"
            onClick={() => announce('로그인은 데모에서 지원하지 않아요.')}
            className="flex flex-1 items-center justify-center gap-1.5 rounded-card border border-ink-border py-2.5 text-sm font-semibold text-ink-900"
          >
            <LogIn size={16} aria-hidden="true" />
            로그인
          </button>
          <button
            type="button"
            onClick={() => announce('회원가입은 데모에서 지원하지 않아요.')}
            className="flex flex-1 items-center justify-center gap-1.5 rounded-card border border-ink-border py-2.5 text-sm font-semibold text-ink-900"
          >
            <UserPlus size={16} aria-hidden="true" />
            회원가입
          </button>
        </div>

        <button
          type="button"
          onClick={() => {
            onClose()
            window.setTimeout(() => {
              const input = document.getElementById('hero-search-input')
              input?.scrollIntoView({ behavior: 'smooth', block: 'center' })
              ;(input as HTMLInputElement | null)?.focus()
            }, 300)
          }}
          className="mx-4 mt-4 flex items-center gap-2 rounded-pill border border-ink-border px-4 py-2.5 text-sm text-ink-500"
        >
          <Search size={16} aria-hidden="true" />
          필요한 서비스를 검색해보세요
        </button>

        <nav aria-label="주 메뉴" className="flex-1 p-4">
          <ul className="space-y-1">
            {navigationMenu.map((item) => (
              <li key={item.id}>
                <details className="group">
                  <summary className="flex cursor-pointer list-none items-center justify-between rounded-lg px-2 py-3 text-[15px] font-semibold text-ink-900">
                    {item.label}
                    <ChevronDown size={16} aria-hidden="true" className="transition group-open:rotate-180" />
                  </summary>
                  <ul className="pb-2 pl-3">
                    {item.children.map((child) => (
                      <li key={child.id}>
                        <a
                          href={child.href}
                          onClick={onClose}
                          className="block rounded-lg px-2 py-2 text-sm text-ink-500 transition hover:bg-surface-muted hover:text-brand-blue"
                        >
                          {child.label}
                        </a>
                      </li>
                    ))}
                  </ul>
                </details>
              </li>
            ))}
          </ul>
        </nav>
      </div>
    </div>
  )
}
