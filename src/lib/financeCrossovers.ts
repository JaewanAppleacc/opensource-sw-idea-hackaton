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
        title: '월 차량비 차이 역전점',
        statement: '현재 입력값 기준으로 두 시나리오의 월 잉여자금이 이미 같습니다.',
      },
    ]
  }

  const higherLabel = gap > 0 ? metro.label : jeonbuk.label
  const lowerLabel = gap > 0 ? jeonbuk.label : metro.label
  const gapAbs = formatKrw(gap)

  // 한 가지 조건만 변경하고 나머지 입력값은 동일하다고 가정한 시나리오다
  // (TASK section 5.3) -- never framed as an annual-salary ("연봉") gap,
  // only as a monthly take-home-pay ("월 실수령액") difference, matching
  // the exact field label the finance form uses.
  const crossovers: AdditionalCrossover[] = [
    {
      id: 'vehicle_cost',
      title: '월 차량비 차이 역전점',
      statement: `현재 입력에서는 ${higherLabel} 근무 시 월 잉여자금이 더 많습니다. 다만 ${higherLabel}의 차량 관련 비용(유지비·주차비 등)이 월 ${gapAbs} 증가하고 나머지 입력값은 동일하다면 두 시나리오의 차이가 사라집니다.`,
    },
    {
      id: 'metro_housing_support',
      title: '월 주거지원 차이 역전점',
      statement:
        higherLabel === metro.label
          ? `${metro.label}이 이미 앞서 있어, 이 시나리오에서는 수도권 주거지원이 필요하지 않습니다.`
          : `${metro.label}에 월 ${gapAbs}의 주거지원(회사 지원금 등)이 추가되고 나머지 입력값은 동일하다면 두 시나리오의 차이가 사라집니다.`,
    },
    {
      id: 'wage_gap',
      title: '월 실수령액 차이 역전점',
      statement: `${lowerLabel}의 월 실수령액이 지금보다 월 ${gapAbs} 더 많아지면(또는 ${higherLabel}의 월 실수령액이 그만큼 적어지면), 나머지 입력값이 동일하다는 가정 하에 두 시나리오의 월 잉여자금이 같아집니다.`,
    },
  ]
  return crossovers
}
