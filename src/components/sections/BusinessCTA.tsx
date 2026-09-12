import { ArrowRight } from 'lucide-react'
import { Container } from '../ui/Container'
import { useToast } from '../ui/ToastProvider'

export function BusinessCTA() {
  const { announce } = useToast()

  return (
    <section className="mt-14">
      <Container>
        <div className="flex flex-col gap-4 rounded-card bg-brand-green px-6 py-6 text-white sm:flex-row sm:items-center sm:justify-between sm:px-10">
          <div>
            <p className="text-lg font-bold">기업 회원이신가요?</p>
            <p className="mt-1 text-sm text-white/85">구인 등록부터 고용 관리까지, 효율적인 인재 채용을 지원합니다.</p>
          </div>
          <button
            type="button"
            onClick={() => announce('기업 서비스 화면은 이 학습용 데모에 포함되어 있지 않아요.')}
            className="inline-flex items-center gap-1.5 self-start rounded-pill bg-white/15 px-5 py-2.5 text-sm font-semibold transition hover:bg-white/25 active:scale-95 sm:self-auto"
          >
            기업 서비스로 이동하기
            <ArrowRight size={16} aria-hidden="true" />
          </button>
        </div>
      </Container>
    </section>
  )
}
