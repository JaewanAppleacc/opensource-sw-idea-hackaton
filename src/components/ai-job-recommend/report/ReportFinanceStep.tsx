import { FinanceComparisonPanel } from '../FinanceComparisonPanel'

interface ReportFinanceStepProps {
  onComputed: () => void
}

/**
 * Report step 5/6 -- "지역 선택에 따른 자금 흐름도 확인해보세요". Thin
 * wrapper around the existing FinanceComparisonPanel: reuses its form,
 * /finance/compare call, and crossover statements unchanged. Never
 * recomputes a region average or shows a winner -- see that component's own
 * doc comment. This step is always skippable via the modal's 다음 button;
 * FinanceComparisonPanel itself shows "조건을 입력하면 계산할 수 있습니다"
 * before the first calculation.
 */
export function ReportFinanceStep({ onComputed }: ReportFinanceStepProps) {
  return (
    <div className="rounded-card border border-ink-border bg-white p-4">
      <FinanceComparisonPanel onComputed={onComputed} />
    </div>
  )
}
