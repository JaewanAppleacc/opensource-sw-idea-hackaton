import { Headset, LogIn, Menu, Search, Settings2, UserPlus } from 'lucide-react'
import { Container } from '../ui/Container'
import { Logo } from '../ui/Logo'
import { useToast } from '../ui/ToastProvider'

interface MainHeaderProps {
  onOpenMobileMenu: () => void
}

export function MainHeader({ onOpenMobileMenu }: MainHeaderProps) {
  const { announce } = useToast()

  function focusHeroSearch() {
    const input = document.getElementById('hero-search-input')
    input?.scrollIntoView({ behavior: 'smooth', block: 'center' })
    ;(input as HTMLInputElement | null)?.focus()
  }

  return (
    <div className="bg-white">
      <Container className="flex h-20 items-center justify-between gap-4">
        <div className="flex items-center gap-3">
          <button
            type="button"
            onClick={onOpenMobileMenu}
            aria-label="전체 메뉴 열기"
            className="flex h-10 w-10 items-center justify-center rounded-full text-ink-700 transition hover:bg-surface-muted active:scale-95 lg:hidden"
          >
            <Menu size={22} aria-hidden="true" />
          </button>
          <a href="#top" aria-label="고용24 클론 홈으로 이동">
            <Logo />
          </a>
        </div>

        <div className="hidden items-center gap-6 text-sm text-ink-500 md:flex">
          <button
            type="button"
            onClick={() => announce('고객센터 연결은 데모에서 지원하지 않아요.')}
            className="inline-flex items-center gap-1.5 transition hover:text-brand-blue"
          >
            <Headset size={16} aria-hidden="true" />
            고객센터
          </button>
          <button
            type="button"
            onClick={() => announce('원격지원 연결은 데모에서 지원하지 않아요.')}
            className="transition hover:text-brand-blue"
          >
            원격지원
          </button>
          <button
            type="button"
            onClick={() => announce('글자·화면 설정은 데모에서 지원하지 않아요.')}
            className="inline-flex items-center gap-1.5 transition hover:text-brand-blue"
          >
            <Settings2 size={16} aria-hidden="true" />
            글자·화면 설정
          </button>

          <span className="h-4 w-px bg-ink-border" aria-hidden="true" />

          <button
            type="button"
            onClick={() => announce('로그인은 데모에서 지원하지 않아요. 목업 데이터로 둘러보세요.')}
            className="inline-flex items-center gap-1.5 font-medium text-ink-900 transition hover:text-brand-blue"
          >
            <LogIn size={16} aria-hidden="true" />
            로그인
          </button>
          <button
            type="button"
            onClick={() => announce('회원가입은 데모에서 지원하지 않아요.')}
            className="inline-flex items-center gap-1.5 font-medium text-ink-900 transition hover:text-brand-blue"
          >
            <UserPlus size={16} aria-hidden="true" />
            회원가입
          </button>
          <button
            type="button"
            onClick={focusHeroSearch}
            className="inline-flex items-center gap-1.5 font-medium text-ink-900 transition hover:text-brand-blue"
          >
            <Search size={16} aria-hidden="true" />
            검색
          </button>
        </div>

        <button
          type="button"
          onClick={focusHeroSearch}
          aria-label="검색으로 이동"
          className="flex h-10 w-10 items-center justify-center rounded-full text-ink-700 transition hover:bg-surface-muted active:scale-95 md:hidden"
        >
          <Search size={20} aria-hidden="true" />
        </button>
      </Container>
    </div>
  )
}
