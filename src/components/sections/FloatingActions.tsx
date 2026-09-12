import { ArrowUp, Bot, HelpCircle } from 'lucide-react'
import { usePrefersReducedMotion } from '../../hooks/usePrefersReducedMotion'
import { useToast } from '../ui/ToastProvider'

export function FloatingActions() {
  const { announce } = useToast()
  const prefersReducedMotion = usePrefersReducedMotion()

  function scrollToTop() {
    window.scrollTo({ top: 0, behavior: prefersReducedMotion ? 'auto' : 'smooth' })
  }

  return (
    <div className="fixed bottom-6 right-4 z-50 flex flex-col items-center gap-3 sm:right-8">
      <button
        type="button"
        onClick={() => announce('챗봇 상담은 데모에서 지원하지 않아요.')}
        aria-label="챗봇 상담 열기"
        className="flex h-12 w-12 flex-col items-center justify-center rounded-full bg-brand-blue text-white shadow-softer transition hover:bg-brand-blue-dark active:scale-95 sm:h-14 sm:w-14"
      >
        <Bot size={20} aria-hidden="true" />
        <span className="text-[9px] font-medium leading-none">챗봇</span>
      </button>

      <button
        type="button"
        onClick={() => announce('도우미 안내는 데모에서 지원하지 않아요.')}
        aria-label="도우미 열기"
        className="flex h-12 w-12 flex-col items-center justify-center rounded-full border border-ink-border bg-white text-ink-700 shadow-soft transition hover:border-brand-blue hover:text-brand-blue active:scale-95 sm:h-14 sm:w-14"
      >
        <HelpCircle size={20} aria-hidden="true" />
        <span className="text-[9px] font-medium leading-none">도우미</span>
      </button>

      <button
        type="button"
        onClick={scrollToTop}
        aria-label="맨 위로 이동"
        className="flex h-12 w-12 flex-col items-center justify-center rounded-full border border-ink-border bg-white text-ink-700 shadow-soft transition hover:border-brand-blue hover:text-brand-blue active:scale-95 sm:h-14 sm:w-14"
      >
        <ArrowUp size={20} aria-hidden="true" />
        <span className="text-[9px] font-medium leading-none">맨위로</span>
      </button>
    </div>
  )
}
