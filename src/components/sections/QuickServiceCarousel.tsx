import { Link } from 'react-router-dom'
import { Container } from '../ui/Container'
import { CarouselControls } from '../ui/CarouselControls'
import { useCarousel } from '../../hooks/useCarousel'
import type { QuickMenuItem } from '../../types'

const PAGE_SIZE = 6

function chunk<T>(items: T[], size: number): T[][] {
  const pages: T[][] = []
  for (let i = 0; i < items.length; i += size) {
    pages.push(items.slice(i, i + size))
  }
  return pages.length > 0 ? pages : [[]]
}

interface QuickServiceCarouselProps {
  items: QuickMenuItem[]
}

export function QuickServiceCarousel({ items }: QuickServiceCarouselProps) {
  const pages = chunk(items, PAGE_SIZE)
  const { page, goTo, next, prev } = useCarousel({ pageCount: pages.length })
  const currentItems = pages[page] ?? []

  return (
    <Container className="mt-10">
      <div
        id="quick-service-panel"
        role="tabpanel"
        aria-label="선택한 서비스의 바로가기 목록"
        className="grid grid-cols-3 gap-x-4 gap-y-8 sm:grid-cols-6 sm:gap-x-7"
      >
        {currentItems.map((item) => {
          const Icon = item.icon
          const content = (
            <>
              <span className="flex h-20 w-20 items-center justify-center rounded-full bg-brand-indigo text-brand-blue shadow-soft transition group-hover:bg-brand-blue sm:h-36 sm:w-36">
                <span className="flex h-11 w-11 items-center justify-center rounded-lg bg-white shadow-sm sm:h-16 sm:w-16">
                  <Icon className="h-7 w-7 sm:h-10 sm:w-10" strokeWidth={2.2} aria-hidden="true" />
                </span>
              </span>
              <span className="text-xs font-medium leading-snug text-ink-900 sm:text-lg">{item.label}</span>
            </>
          )
          const className =
            'group flex flex-col items-center gap-4 rounded-2xl p-2 text-center transition hover:-translate-y-0.5 focus-visible:-translate-y-0.5'

          return item.to ? (
            <Link key={item.id} to={item.to} className={className}>
              {content}
            </Link>
          ) : (
            <a key={item.id} href={item.href} className={className}>
              {content}
            </a>
          )
        })}
      </div>

      {pages.length > 1 && (
        <div className="mt-6 flex justify-center">
          <CarouselControls page={page} pageCount={pages.length} onPrev={prev} onNext={next} onGoTo={goTo} label="퀵메뉴" />
        </div>
      )}
    </Container>
  )
}
