import { ChevronRight, FolderOpen } from 'lucide-react'
import { Container } from '../ui/Container'
import { statItems } from '../../data/content'

export function StatisticsPanel() {
  return (
    <section aria-labelledby="stats-heading" className="mt-14">
      <Container>
        <div className="rounded-card border border-ink-border bg-surface-muted p-6 sm:p-10">
          <div className="flex flex-col gap-8 lg:flex-row lg:items-center">
            <div className="flex items-center gap-5 lg:w-2/5">
              <span
                aria-hidden="true"
                className="flex h-16 w-16 shrink-0 items-center justify-center rounded-2xl bg-gradient-to-br from-brand-indigo to-brand-blue text-white shadow-soft"
              >
                <FolderOpen size={30} aria-hidden="true" />
              </span>
              <h2 id="stats-heading" className="text-xl font-bold leading-snug text-ink-900 sm:text-2xl">
                채용공고와 참여 가능한
                <br className="hidden sm:block" /> 교육·훈련을 확인해 보세요.
              </h2>
            </div>

            <div className="grid flex-1 grid-cols-1 gap-4 sm:grid-cols-2">
              {statItems.map((stat) => (
                <div key={stat.id} className="rounded-card border border-ink-border bg-white p-6">
                  <p className="text-sm font-medium text-ink-500">{stat.label}</p>
                  <p className="mt-1 text-3xl font-bold text-brand-blue">
                    {stat.value}
                    <span className="ml-1 text-lg font-semibold text-ink-700">{stat.unit}</span>
                  </p>
                  <ul className="mt-4 space-y-2 border-t border-ink-border pt-4">
                    {stat.links.map((link) => (
                      <li key={link.id}>
                        <a
                          href={link.href}
                          className="flex items-center justify-between text-sm text-ink-500 transition hover:text-brand-blue"
                        >
                          {link.label}
                          <ChevronRight size={15} aria-hidden="true" />
                        </a>
                      </li>
                    ))}
                  </ul>
                </div>
              ))}
            </div>
          </div>
        </div>
      </Container>
    </section>
  )
}
