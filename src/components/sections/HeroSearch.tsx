import { Keyboard, Search } from 'lucide-react'
import { useId, useState } from 'react'
import { Container } from '../ui/Container'
import { useToast } from '../ui/ToastProvider'
import { searchScopes } from '../../data/content'

export function HeroSearch() {
  const { announce } = useToast()
  const [scope, setScope] = useState(searchScopes[0]!.id)
  const [query, setQuery] = useState('')
  const inputId = useId()
  const scopeId = useId()

  function handleSubmit(event: React.FormEvent) {
    event.preventDefault()
    const scopeLabel = searchScopes.find((s) => s.id === scope)?.label ?? '전체'
    if (!query.trim()) {
      announce('검색어를 입력해 주세요.')
      return
    }
    announce(`[${scopeLabel}] '${query.trim()}' 검색 결과 (Mock) — 실제 검색은 연결되어 있지 않아요.`)
  }

  return (
    <section
      aria-labelledby="hero-search-heading"
      className="relative pt-14 pb-10 sm:pt-16 sm:pb-12"
    >
      <Container className="relative">
        <h1 id="hero-search-heading" className="text-center text-3xl font-bold tracking-tight text-brand-blue sm:text-[42px] sm:leading-tight">
          나만의 고용서비스, 고용24
        </h1>

        <form
          onSubmit={handleSubmit}
          className="mx-auto mt-8 flex h-16 max-w-4xl items-stretch rounded-pill border-[3px] border-brand-blue bg-white shadow-soft sm:h-[70px]"
        >
          <label htmlFor={scopeId} className="sr-only">
            검색 범위 선택
          </label>
          <select
            id={scopeId}
            value={scope}
            onChange={(e) => setScope(e.target.value)}
            className="w-32 rounded-l-pill bg-transparent pl-7 pr-3 text-base font-medium text-ink-900 outline-none sm:w-48 sm:text-lg"
          >
            {searchScopes.map((s) => (
              <option key={s.id} value={s.id}>
                {s.label}
              </option>
            ))}
          </select>

          <span className="my-3.5 w-px bg-ink-border" aria-hidden="true" />

          <label htmlFor={inputId} className="sr-only">
            통합검색어 입력
          </label>
          <input
            id={inputId}
            type="search"
            value={query}
            onChange={(e) => setQuery(e.target.value)}
            placeholder="필요한 서비스를 검색해보세요"
            className="min-w-0 flex-1 bg-transparent px-6 text-base text-ink-900 outline-none placeholder:text-ink-400 sm:text-lg"
          />

          <button
            type="button"
            onClick={() => announce('보안 가상 키보드는 데모에서 지원하지 않아요.')}
            aria-label="보안 가상 키보드 열기"
            className="flex w-14 shrink-0 items-center justify-center text-brand-blue transition hover:text-brand-blue-dark"
          >
            <Keyboard size={27} aria-hidden="true" />
          </button>

          <button
            type="submit"
            aria-label="통합검색 실행"
            className="flex w-16 shrink-0 items-center justify-center rounded-r-pill bg-white text-brand-blue transition hover:text-brand-blue-dark active:scale-95"
          >
            <Search size={34} strokeWidth={2} aria-hidden="true" />
          </button>
        </form>
      </Container>
    </section>
  )
}
