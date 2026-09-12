import { AlertTriangle, Info, Loader2, Wallet } from 'lucide-react'
import { useEffect, useId, useRef, useState } from 'react'
import {
  ApiClientError,
  compareFinance,
  type FinancialComparison,
  type FinancialOption,
} from '../../lib/apiClient'
import { errorCodeToMessage } from '../../lib/displayLabels'
import { computeAdditionalCrossovers } from '../../lib/financeCrossovers'

interface DetailedMoneyFormState {
  monthly_income_after_tax: string
  rent: string
  maintenance_fee: string
  commute_cost: string
  vehicle_upkeep_cost: string
  other_fixed_cost: string
  deposit: string
  current_savings: string
}

// Example starting values (TASK section 7 requires the disclaimer below
// whenever region defaults are shown). Purely illustrative -- never sent
// anywhere as if they were the specific posting's real cost of living.
const DEFAULT_METRO_FORM: DetailedMoneyFormState = {
  monthly_income_after_tax: '2800000',
  rent: '600000',
  maintenance_fee: '100000',
  commute_cost: '120000',
  vehicle_upkeep_cost: '0',
  other_fixed_cost: '300000',
  deposit: '20000000',
  current_savings: '0',
}

const DEFAULT_JEONBUK_FORM: DetailedMoneyFormState = {
  monthly_income_after_tax: '2500000',
  rent: '350000',
  maintenance_fee: '80000',
  commute_cost: '80000',
  vehicle_upkeep_cost: '150000',
  other_fixed_cost: '280000',
  deposit: '5000000',
  current_savings: '0',
}

function formatKrw(value: number): string {
  return `${Math.round(value).toLocaleString('ko-KR')}원`
}

function parseNonNegative(value: string): number | null {
  if (value.trim() === '') return null
  const n = Number(value)
  if (!Number.isFinite(n) || n < 0) return null
  return n
}

const FIELD_CONFIG: { key: keyof DetailedMoneyFormState; label: string }[] = [
  { key: 'monthly_income_after_tax', label: '월 실수령액 (원)' },
  { key: 'rent', label: '월세 (원/월)' },
  { key: 'maintenance_fee', label: '관리비 (원/월)' },
  { key: 'commute_cost', label: '교통비 (원/월)' },
  { key: 'vehicle_upkeep_cost', label: '차량 유지비 (원/월)' },
  { key: 'other_fixed_cost', label: '기타 고정비 (원/월)' },
  { key: 'deposit', label: '보증금 (원)' },
  { key: 'current_savings', label: '현재 보유자금 (원)' },
]

function MoneyFields({
  legend,
  values,
  onChange,
  idPrefix,
}: {
  legend: string
  values: DetailedMoneyFormState
  onChange: (next: DetailedMoneyFormState) => void
  idPrefix: string
}) {
  return (
    <fieldset className="rounded-card border border-ink-border p-4">
      <legend className="px-1 text-sm font-bold text-ink-900">{legend}</legend>
      <div className="mt-2 grid grid-cols-1 gap-3 sm:grid-cols-2">
        {FIELD_CONFIG.map(({ key, label }) => (
          <div key={key}>
            <label htmlFor={`${idPrefix}-${key}`} className="block text-xs font-medium text-ink-500">
              {label}
            </label>
            <input
              id={`${idPrefix}-${key}`}
              type="number"
              min={0}
              inputMode="numeric"
              value={values[key]}
              onChange={(e) => onChange({ ...values, [key]: e.target.value })}
              className="mt-1 w-full rounded-card border border-ink-border bg-white px-3 py-2 text-sm text-ink-900 outline-none focus:border-brand-blue"
            />
          </div>
        ))}
      </div>
    </fieldset>
  )
}

function ResultCard({
  result,
  metroSavings,
  jeonbukSavings,
}: {
  result: FinancialComparison
  metroSavings: number
  jeonbukSavings: number
}) {
  const savingsByKey: Record<string, number> = { metropolitan: metroSavings, jeonbuk: jeonbukSavings }
  const additionalCrossovers = computeAdditionalCrossovers(result)

  return (
    <div className="mt-5 space-y-4">
      <div className="grid grid-cols-1 gap-4 sm:grid-cols-2">
        {Object.entries(result.options).map(([key, option]) => {
          const savings = savingsByKey[key] ?? 0
          return (
            <div key={key} className="rounded-card border border-ink-border bg-surface-muted p-4">
              <p className="text-sm font-semibold text-ink-900">{option.label}</p>
              <p className="mt-2">
                <span className="text-2xl font-bold text-ink-900">{formatKrw(option.monthly_surplus)}</span>
                <span className="ml-1 text-xs text-ink-500">월 가용자금</span>
              </p>
              <dl className="mt-3 space-y-1 text-sm text-ink-700">
                <div className="flex justify-between">
                  <dt>1년 가용자금</dt>
                  <dd className="font-medium">{formatKrw(option.one_year_liquid_cash)}</dd>
                </div>
                <div className="flex justify-between">
                  <dt>3년 가용자금 (가정 기반)</dt>
                  <dd className="font-medium">{formatKrw(option.three_year_liquid_cash)}</dd>
                </div>
                <div className="flex justify-between border-t border-ink-border pt-1 text-ink-500">
                  <dt>보증금 (묶인 자산)</dt>
                  <dd>{formatKrw(option.deposit_locked)}</dd>
                </div>
                {savings > 0 && (
                  <div className="flex justify-between border-t border-ink-border pt-1 text-ink-500">
                    <dt>현재 보유자금 (입력값, 묶이지 않은 자산)</dt>
                    <dd>{formatKrw(savings)}</dd>
                  </div>
                )}
                {savings > 0 && (
                  <div className="flex justify-between font-semibold text-ink-900">
                    <dt>1년 후 실제 가용자금 (보유자금 포함)</dt>
                    <dd>{formatKrw(option.one_year_liquid_cash + savings)}</dd>
                  </div>
                )}
              </dl>
            </div>
          )
        })}
      </div>

      <div className="text-xs text-ink-500">
        <p className="font-semibold text-ink-700">조건 역전점 (보조 인사이트)</p>
        <p className="mt-1 text-ink-400">한 가지 조건만 변경하고 나머지 입력값은 동일하다고 가정한 시나리오입니다.</p>
        <p className="mt-1.5">
          <strong className="font-medium text-ink-700">월 주거비 차이 역전점.</strong> {result.crossover.interpretation}
        </p>
        {additionalCrossovers.map((c) => (
          <p key={c.id} className="mt-1.5">
            <strong className="font-medium text-ink-700">{c.title}.</strong> {c.statement}
          </p>
        ))}
      </div>

      <p className="text-xs text-ink-400">{result.disclaimer}</p>
    </div>
  )
}

export function FinanceComparisonPanel() {
  const idPrefix = useId()
  const [metro, setMetro] = useState<DetailedMoneyFormState>(DEFAULT_METRO_FORM)
  const [jeonbuk, setJeonbuk] = useState<DetailedMoneyFormState>(DEFAULT_JEONBUK_FORM)
  const [formError, setFormError] = useState<string | null>(null)
  const [hasComputedOnce, setHasComputedOnce] = useState(false)
  const [state, setState] = useState<
    { status: 'idle' } | { status: 'loading' } | { status: 'success'; result: FinancialComparison } | { status: 'error'; error: ApiClientError }
  >({ status: 'idle' })
  const debounceRef = useRef<number | null>(null)

  function toOption(label: string, form: DetailedMoneyFormState): FinancialOption | null {
    const monthly_income_after_tax = parseNonNegative(form.monthly_income_after_tax)
    const rent = parseNonNegative(form.rent)
    const maintenance_fee = parseNonNegative(form.maintenance_fee)
    const commute_cost = parseNonNegative(form.commute_cost)
    const vehicle_upkeep_cost = parseNonNegative(form.vehicle_upkeep_cost)
    const other_fixed_cost = parseNonNegative(form.other_fixed_cost)
    const deposit = parseNonNegative(form.deposit)
    if (
      monthly_income_after_tax === null ||
      rent === null ||
      maintenance_fee === null ||
      commute_cost === null ||
      vehicle_upkeep_cost === null ||
      other_fixed_cost === null ||
      deposit === null
    ) {
      return null
    }
    return {
      label,
      monthly_income_after_tax,
      monthly_housing_cost: rent + maintenance_fee,
      monthly_other_living_cost: commute_cost + vehicle_upkeep_cost + other_fixed_cost,
      deposit,
    }
  }

  async function runCompare() {
    const metropolitan = toOption('수도권', metro)
    const jb = toOption('전북', jeonbuk)
    if (!metropolitan || !jb) {
      setFormError('모든 항목을 0 이상의 숫자로 입력해 주세요.')
      return
    }
    setFormError(null)
    setState({ status: 'loading' })
    try {
      const result = await compareFinance({ metropolitan, jeonbuk: jb })
      setState({ status: 'success', result })
      setHasComputedOnce(true)
    } catch (err) {
      setState({
        status: 'error',
        error: err instanceof ApiClientError ? err : new ApiClientError({ code: 'unexpected_response', message: '알 수 없는 오류가 발생했습니다.' }),
      })
    }
  }

  function handleSubmit(event: React.FormEvent) {
    event.preventDefault()
    void runCompare()
  }

  // "입력값이 바뀌면 즉시 다시 계산" (TASK section 8) -- once the user has
  // computed at least once, further edits auto-recompute after a short
  // debounce, so typing doesn't fire a request per keystroke.
  useEffect(() => {
    if (!hasComputedOnce) return
    if (debounceRef.current) window.clearTimeout(debounceRef.current)
    debounceRef.current = window.setTimeout(() => {
      void runCompare()
    }, 500)
    return () => {
      if (debounceRef.current) window.clearTimeout(debounceRef.current)
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [metro, jeonbuk])

  const metroSavings = parseNonNegative(metro.current_savings) ?? 0
  const jeonbukSavings = parseNonNegative(jeonbuk.current_savings) ?? 0

  return (
    <div>
      <h3 className="flex items-center gap-2 text-sm font-bold text-ink-900">
        <Wallet size={16} aria-hidden="true" className="text-brand-blue" />
        생활비까지 비교해보기
      </h3>
      <p className="mt-1 text-xs text-ink-400">
        직접 입력한 금액으로 1년·3년 뒤 가용자금을 계산합니다. 추천 점수나 승자는 표시하지 않습니다.
      </p>
      <p className="mt-2 flex items-start gap-1.5 text-[11px] text-ink-400">
        <Info size={12} aria-hidden="true" className="mt-0.5 shrink-0" />
        시연용 예시값입니다. 실제 거주지와 출퇴근 조건에 맞게 수정할 수 있습니다.
      </p>

      <form onSubmit={handleSubmit} noValidate className="mt-4 space-y-4">
        <MoneyFields legend="수도권" values={metro} onChange={setMetro} idPrefix={`${idPrefix}-metro`} />
        <MoneyFields legend="전북" values={jeonbuk} onChange={setJeonbuk} idPrefix={`${idPrefix}-jeonbuk`} />

        {formError && (
          <p role="alert" className="flex items-center gap-1.5 text-xs font-medium text-red-500">
            <AlertTriangle size={13} aria-hidden="true" />
            {formError}
          </p>
        )}

        <button
          type="submit"
          disabled={state.status === 'loading'}
          className="flex items-center gap-2 rounded-pill bg-brand-blue px-6 py-3 text-sm font-semibold text-white transition hover:bg-brand-blue-dark active:scale-95 disabled:opacity-60"
        >
          {state.status === 'loading' && <Loader2 size={16} aria-hidden="true" className="animate-spin" />}
          자금 비교 계산하기
        </button>
      </form>

      {state.status === 'error' && (
        <p role="alert" className="mt-3 flex items-center gap-1.5 rounded-card border border-red-200 bg-red-50 p-3 text-sm text-red-600">
          <AlertTriangle size={16} aria-hidden="true" />
          {errorCodeToMessage(state.error.code, state.error.message)}
        </p>
      )}

      {state.status === 'success' && (
        <ResultCard result={state.result} metroSavings={metroSavings} jeonbukSavings={jeonbukSavings} />
      )}
    </div>
  )
}
