import { Plus } from 'lucide-react'
import { Container } from '../ui/Container'
import { Logo } from '../ui/Logo'
import { familySites, footerPolicyLinks, relatedOrgs } from '../../data/content'
import type { LinkListGroup } from '../../types'

function FooterAccordion({ group }: { group: LinkListGroup }) {
  return (
    <details className="group border-b border-ink-border py-1 sm:flex-1 sm:border-b-0 sm:border-r sm:last:border-r-0">
      <summary className="flex cursor-pointer list-none items-center justify-between px-2 py-3 text-sm font-semibold text-ink-900 transition hover:text-brand-blue">
        {group.label}
        <Plus size={16} aria-hidden="true" className="transition group-open:rotate-45" />
      </summary>
      <ul className="px-2 pb-3">
        {group.links.map((link) => (
          <li key={link.id}>
            <a href={link.href} className="block py-1.5 text-sm text-ink-500 transition hover:text-brand-blue">
              {link.label}
            </a>
          </li>
        ))}
      </ul>
    </details>
  )
}

export function Footer() {
  return (
    <footer className="mt-14 border-t border-ink-border bg-white">
      <Container className="flex flex-col divide-y divide-ink-border sm:flex-row sm:divide-x sm:divide-y-0">
        <FooterAccordion group={familySites} />
        <FooterAccordion group={relatedOrgs} />
      </Container>

      <div className="border-t border-ink-border">
        <Container className="py-8">
          <Logo />

          <p className="mt-4 text-sm leading-relaxed text-ink-500">
            (00000) 이 프로젝트는 실제 주소가 아닌 학습용 예시 주소를 사용합니다.
            <br />
            홈페이지 전산 이용 문의 000-0000 (평일 09시 ~ 18시, 예시 번호)
            <br />
            고용·노동 분야 제도 문의 000-0000 (평일 09시 ~ 18시, 예시 번호)
          </p>

          <p className="mt-4 max-w-3xl text-xs leading-relaxed text-ink-400">
            이 사이트는 고용노동부 고용24(work24.go.kr) 메인페이지의 정보 구조와 화면 구성을 참고하여 만든{' '}
            <strong className="text-ink-700">비공식 학습용 클론</strong>입니다. 실제 고용24 서비스와 무관하며, 모든
            데이터·링크·기관명은 학습을 위한 가상의 정보입니다.
          </p>

          <nav aria-label="정책 링크" className="mt-6 flex flex-wrap gap-x-5 gap-y-2">
            {footerPolicyLinks.links.map((link) => (
              <a
                key={link.id}
                href={link.href}
                className="text-xs font-medium text-ink-500 underline-offset-2 transition hover:text-brand-blue hover:underline"
              >
                {link.label}
              </a>
            ))}
          </nav>

          <div className="mt-6 flex flex-wrap gap-2">
            <span className="rounded-full border border-ink-border px-3 py-1 text-[11px] text-ink-400">
              웹접근성 인증 마크(예시)
            </span>
            <span className="rounded-full border border-ink-border px-3 py-1 text-[11px] text-ink-400">
              품질인증 마크(예시)
            </span>
          </div>

          <p className="mt-6 text-xs text-ink-400">© 학습용 예시 프로젝트. All rights reserved.</p>
        </Container>
      </div>
    </footer>
  )
}
