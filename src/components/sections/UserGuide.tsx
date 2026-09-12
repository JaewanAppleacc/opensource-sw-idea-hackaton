import { ChevronRight } from 'lucide-react'
import { Container } from '../ui/Container'
import { guideCards } from '../../data/content'
import type { GuideTint } from '../../types'

const tintClasses: Record<GuideTint, string> = {
  lavender: 'bg-tint-lavender',
  mint: 'bg-tint-mint',
  sky: 'bg-tint-sky',
}

export function UserGuide() {
  return (
    <section aria-labelledby="guide-heading" className="mt-14">
      <Container>
        <h2 id="guide-heading" className="text-xl font-bold text-ink-900 sm:text-2xl">
          이용가이드
        </h2>

        <ul className="mt-6 grid grid-cols-1 gap-4 sm:grid-cols-3">
          {guideCards.map((card) => (
            <li key={card.id}>
              <a
                href={card.href}
                className={`block h-full rounded-card p-6 transition hover:-translate-y-0.5 focus-visible:-translate-y-0.5 ${tintClasses[card.tint]}`}
              >
                <h3 className="text-lg font-bold text-ink-900">{card.title}</h3>
                <p className="mt-2 text-sm leading-relaxed text-ink-700">{card.description}</p>
                <span className="mt-4 inline-flex items-center gap-1 text-sm font-semibold text-ink-900">
                  바로가기
                  <ChevronRight size={14} aria-hidden="true" />
                </span>
              </a>
            </li>
          ))}
        </ul>
      </Container>
    </section>
  )
}
