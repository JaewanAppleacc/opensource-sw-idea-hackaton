import { ChevronRight } from 'lucide-react'
import { Container } from '../ui/Container'
import { policyCards } from '../../data/content'

export function PolicyCards() {
  return (
    <section aria-labelledby="policy-heading" className="mt-14">
      <Container>
        <div className="flex items-end justify-between">
          <h2 id="policy-heading" className="text-xl font-bold text-ink-900 sm:text-2xl">
            고용정책 정보
          </h2>
          <a
            href="#policy-more"
            className="inline-flex items-center gap-1 text-sm font-medium text-ink-500 transition hover:text-brand-blue"
          >
            더보기
            <ChevronRight size={16} aria-hidden="true" />
          </a>
        </div>

        <ul className="mt-6 grid grid-cols-2 gap-4 sm:grid-cols-3 lg:grid-cols-5">
          {policyCards.map((card) => {
            const Icon = card.icon
            return (
              <li key={card.id}>
                <a
                  href={card.href}
                  className="flex h-full flex-col rounded-card border border-ink-border bg-white p-5 transition hover:-translate-y-0.5 hover:border-brand-blue hover:shadow-soft focus-visible:-translate-y-0.5"
                >
                  <span className="flex h-11 w-11 items-center justify-center rounded-full bg-brand-blue/10 text-brand-blue">
                    <Icon size={22} aria-hidden="true" />
                  </span>
                  <span className="mt-4 text-base font-bold text-ink-900">{card.title}</span>
                  <span className="mt-2 flex-1 text-sm leading-relaxed text-ink-500">{card.description}</span>
                  <span className="mt-4 inline-flex items-center gap-1 text-sm font-medium text-brand-blue">
                    바로가기
                    <ChevronRight size={14} aria-hidden="true" />
                  </span>
                </a>
              </li>
            )
          })}
        </ul>
      </Container>
    </section>
  )
}
