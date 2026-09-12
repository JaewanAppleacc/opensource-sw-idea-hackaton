import { ChevronRight } from 'lucide-react'
import { Container } from '../ui/Container'
import { newsItems, noticeItems } from '../../data/content'

export function NewsAndNotices() {
  return (
    <section aria-labelledby="news-heading" className="mt-14">
      <Container>
        <div className="grid grid-cols-1 gap-8 rounded-card border border-ink-border p-6 sm:p-8 lg:grid-cols-2">
          <div>
            <div className="flex items-end justify-between">
              <h2 id="news-heading" className="text-xl font-bold text-ink-900">
                고용뉴스
              </h2>
              <a href="#news-more" className="inline-flex items-center gap-1 text-sm text-ink-500 hover:text-brand-blue">
                더보기
                <ChevronRight size={16} aria-hidden="true" />
              </a>
            </div>
            <ul className="mt-4 divide-y divide-ink-border">
              {newsItems.map((item) => (
                <li key={item.id} className="py-4 first:pt-0">
                  <a href={item.href} className="group block">
                    <p className="font-semibold text-ink-900 group-hover:text-brand-blue">{item.title}</p>
                    <p className="mt-1 text-xs text-ink-400">{item.date}</p>
                    <p className="mt-2 line-clamp-2 text-sm text-ink-500">{item.excerpt}</p>
                  </a>
                </li>
              ))}
            </ul>
          </div>

          <div>
            <div className="flex items-end justify-between">
              <h2 id="notice-heading" className="text-xl font-bold text-ink-900">
                공지사항
              </h2>
              <a href="#notice-more" className="inline-flex items-center gap-1 text-sm text-ink-500 hover:text-brand-blue">
                더보기
                <ChevronRight size={16} aria-hidden="true" />
              </a>
            </div>
            <ul className="mt-4 divide-y divide-ink-border">
              {noticeItems.map((item) => (
                <li key={item.id} className="py-4 first:pt-0">
                  <a href={item.href} className="group flex items-center justify-between gap-4">
                    <span className="flex min-w-0 items-center gap-2">
                      {item.isNew && (
                        <span className="shrink-0 rounded-full bg-brand-blue px-2 py-0.5 text-[10px] font-bold text-white">
                          NEW
                        </span>
                      )}
                      <span className="truncate text-sm font-medium text-ink-900 group-hover:text-brand-blue">
                        {item.title}
                      </span>
                    </span>
                    <span className="shrink-0 text-xs text-ink-400">{item.date}</span>
                  </a>
                </li>
              ))}
            </ul>
          </div>
        </div>
      </Container>
    </section>
  )
}
