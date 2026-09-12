import { Container } from '../ui/Container'

export function GovernmentNoticeBar() {
  return (
    <div className="border-b border-ink-border bg-surface-muted text-xs text-ink-500">
      <Container className="flex h-9 items-center gap-2">
        <span aria-hidden="true" className="text-sm leading-none">🇰🇷</span>
        <p>이 누리집은 대한민국 공식 전자정부 누리집을 참고해 만든 학습용 예시입니다.</p>
      </Container>
    </div>
  )
}
