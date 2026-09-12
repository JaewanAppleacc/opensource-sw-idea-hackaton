/**
 * Additional deterministic crossover statements (TASK section 8, priorities
 * 2-4), derived purely from the numbers the backend's /finance/compare
 * already returned (FinancialComparison.options.*.monthly_surplus). No
 * LLM, no new backend call, no new input. Priority 1 (monthly housing
 * cost crossover) is the backend's own `crossover` field and is not
 * duplicated here.
 *
 * Every one of these variables (vehicle cost, a housing subsidy, a wage
 * difference) enters the same linear monthly-surplus equation with
 * coefficient 1 (see backend/app/services/finance.py::_monthly_surplus:
 * income - housing - other, no interaction terms) -- so the magnitude that
 * closes the gap is always the same number, |surplus_a - surplus_b|. Only
 * the direction and the sentence differ. This is exactly why these can be
 * derived safely on the frontend from the backend's own already-computed
 * surplus values instead of recomputing anything.
 */
import type { FinancialComparison } from './apiClient'

export interface AdditionalCrossover {
  id: 'vehicle_cost' | 'metro_housing_support' | 'wage_gap'
  title: string
  statement: string
}

function formatKrw(value: number): string {
  return `${Math.round(Math.abs(value)).toLocaleString('ko-KR')}원`
}

/** Rounds to the same unit the backend used for its own crossover, so all
 * crossover figures in one screen share one rounding convention. */
function roundToUnit(value: number, unit: number): number {
  if (!Number.isFinite(unit) || unit <= 0) return Math.round(value)
  return Math.round(value / unit) * unit
}

export function computeAdditionalCrossovers(result: FinancialComparison): AdditionalCrossover[] {
  const metro = result.options.metropolitan
  const jeonbuk = result.options.jeonbuk
  if (!metro || !jeonbuk) return []

  const unit = result.assumptions.rounding_unit_krw ?? 100000
  const gapRaw = metro.monthly_surplus - jeonbuk.monthly_surplus
  const gap = roundToUnit(gapRaw, unit)

  if (gap === 0) {
    return [
      {
        id: 'vehicle_cost',
        title: '차량비 역전점',
        statement: '현재 입력값 기준으로 두 시나리오의 월 잉여자금이 이미 같습니다.',
      },
    ]
  }

  const higherLabel = gap > 0 ? metro.label : jeonbuk.label
  const lowerLabel = gap > 0 ? jeonbuk.label : metro.label
  const gapAbs = formatKrw(gap)

  const crossovers: AdditionalCrossover[] = [
    {
      id: 'vehicle_cost',
      title: '차량비 역전점',
      statement: `현재 입력에서는 ${higherLabel} 근무 시 월 잉여자금이 더 많습니다. 다만 ${higherLabel}의 차량 관련 비용(유지비·주차비 등)이 월 ${gapAbs} 증가하면 두 시나리오의 차이가 사라집니다.`,
    },
    {
      id: 'metro_housing_support',
      title: '수도권 주거지원 역전점',
      statement:
        higherLabel === metro.label
          ? `${metro.label}이 이미 앞서 있어, 이 시나리오에서는 수도권 주거지원이 필요하지 않습니다.`
          : `${metro.label}에 월 ${gapAbs}의 주거지원(회사 지원금 등)이 추가된다면 두 시나리오의 차이가 사라집니다.`,
    },
    {
      id: 'wage_gap',
      title: '임금 차이 역전점',
      statement: `${lowerLabel}의 세후 월급이 지금보다 월 ${gapAbs} 더 많아지면(또는 ${higherLabel}의 월급이 그만큼 적어지면) 두 시나리오의 월 잉여자금이 같아집니다.`,
    },
  ]
  return crossovers
}
