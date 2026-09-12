import { Pause, Play } from 'lucide-react'
import { useEffect, useRef, useState } from 'react'
import { Container } from '../ui/Container'
import { usePrefersReducedMotion } from '../../hooks/usePrefersReducedMotion'
import { useToast } from '../ui/ToastProvider'
import type { AudienceId } from '../../types'

const notices = [
  '시스템 개선 작업에 따른 서비스 중단 안내 (2026년 9월 12일(토) 00:00~18:00)',
  '추석 연휴 고객센터 운영시간 변경 안내',
  '모바일 앱 업데이트 안내(로그인 방식 개선)',
]

interface AudienceSwitcherProps {
  audience: AudienceId
  onChange: (audience: AudienceId) => void
}

export function AudienceSwitcher({ audience, onChange }: AudienceSwitcherProps) {
  const prefersReducedMotion = usePrefersReducedMotion()
  const [noticeIndex, setNoticeIndex] = useState(0)
  const [isPlaying, setIsPlaying] = useState(!prefersReducedMotion)
  const { announce } = useToast()
  const timerRef = useRef<ReturnType<typeof setInterval> | null>(null)

  useEffect(() => {
    if (!isPlaying) return
    timerRef.current = setInterval(() => {
      setNoticeIndex((i) => (i + 1) % notices.length)
    }, 4500)
    return () => {
      if (timerRef.current) clearInterval(timerRef.current)
    }
  }, [isPlaying])

  function handleAudienceChange(next: AudienceId) {
    onChange(next)
    if (next === 'business') {
      announce('기업 서비스 화면은 이 학습용 데모에 포함되어 있지 않아요.')
    }
  }

  return (
    <div className="bg-brand-blue text-white">
      <Container className="flex h-12 items-center gap-4">
        <div role="tablist" aria-label="이용자 구분" className="flex shrink-0 overflow-hidden rounded-md bg-white/15">
          {(
            [
              { id: 'personal', label: '개인' },
              { id: 'business', label: '기업' },
            ] as const
          ).map((tab) => (
            <button
              key={tab.id}
              type="button"
              role="tab"
              aria-selected={audience === tab.id}
              onClick={() => handleAudienceChange(tab.id)}
              className={`px-5 py-2 text-sm font-semibold transition ${
                audience === tab.id ? 'bg-white text-brand-blue' : 'text-white hover:bg-white/10'
              }`}
            >
              {tab.label}
            </button>
          ))}
        </div>

        <p className="min-w-0 flex-1 truncate text-sm" aria-live="polite">
          <span aria-hidden="true">📢 </span>
          {notices[noticeIndex]}
        </p>

        <button
          type="button"
          onClick={() => announce('공지사항 상세 안내는 데모에서 준비 중이에요.')}
          className="hidden shrink-0 items-center rounded-full border border-white/50 px-3 py-1 text-xs font-medium transition hover:bg-white/10 sm:inline-flex"
        >
          자세히 보기
        </button>

        <button
          type="button"
          onClick={() => setIsPlaying((p) => !p)}
          aria-label={isPlaying ? '공지사항 자동전환 정지' : '공지사항 자동전환 재생'}
          aria-pressed={isPlaying}
          className="flex h-7 w-7 shrink-0 items-center justify-center rounded-full border border-white/50 transition hover:bg-white/10"
        >
          {isPlaying ? <Pause size={13} aria-hidden="true" /> : <Play size={13} aria-hidden="true" />}
        </button>
      </Container>
    </div>
  )
}
