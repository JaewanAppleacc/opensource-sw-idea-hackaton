import { AlertTriangle, Loader2, Wallet } from 'lucide-react'
import { useId, useState } from 'react'
import {
  ApiClientError,
  compareFinance,
  type FinancialComparison,
  type FinancialOption,
} from '../../lib/apiClient'
import { errorCodeToMessage } from '../../lib/displayLabels'

interface MoneyFormState {
  monthly_income_after_tax: string
  monthly_housing_cost: string
  monthly_other_living_cost: string
  deposit: string
}

const EMPTY_MONEY_FORM: MoneyFormState = {
  monthly_income_after_tax: '',
  monthly_housing_cost: '',
  monthly_other_living_cost: '',
  deposit: '',
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

function MoneyFields({
  legend,
  values,
  onChange,
  idPrefix,
}: {
  legend: string
  values: MoneyFormState
  onChange: (next: MoneyFormState) => void
  idPrefix: string
}) {
  const fields: { key: keyof MoneyFormState; label: string }[] = [
    { key: 'monthly_income_after_tax', label: '세후 월급 (원)' },
    { key: 'monthly_housing_cost', label: '주거비 + 관리비 (원/월)' },
    { key: 'monthly_other_living_cost', label: '기타 생활비 (원/월)' },
    { key: 'deposit', label: '보증금 (원)' },
  ]
  return (
    <fieldset className="rounded-card border border-ink-border p-4">
      <legend className="px-1 text-sm font-bold text-ink-900">{legend}</legend>
      <div className="mt-2 grid grid-cols-1 gap-3 sm:grid-cols-2">
        {fields.map(({ key, label }) => (
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

function ResultCard({ result }: { result: FinancialComparison }) {
  return (
    <div className="mt-5 space-y-4">
      <div className="grid grid-cols-1 gap-4 sm:grid-cols-2">
        {Object.entries(result.options).map(([key, option]) => (
          <div key={key} className="rounded-card border border-ink-border bg-surface-muted p-4">
            <p className="font-semibold text-ink-900">{option.label}</p>
            <dl className="mt-2 space-y-1 text-sm text-ink-700">
              <div className="flex justify-between">
                <dt>월 가용자금</dt>
                <dd>{formatKrw(option.monthly_surplus)}</dd>
              </div>
              <div className="flex justify-between">
                <dt>1년 가용자금</dt>
                <dd>{formatKrw(option.one_year_liquid_cash)}</dd>
              </div>
              <div className="flex justify-between">
                <dt>3년 가용자금 (가정 기반)</dt>
                <dd>{formatKrw(option.three_year_liquid_cash)}</dd>
              </div>
              <div className="flex justify-between border-t border-ink-border pt-1 text-ink-500">
                <dt>보증금 (묶인 자산)</dt>
                <dd>{formatKrw(option.deposit_locked)}</dd>
              </div>
            </dl>
          </div>
        ))}
      </div>

      <div className="rounded-card border border-ink-border bg-white p-4 text-sm text-ink-700">
        <p className="font-semibold text-ink-900">주거비 교차점</p>
        <p className="mt-1">{result.crossover.interpretation}</p>
      </div>

      <p className="text-xs text-ink-400">{result.disclaimer}</p>
    </div>
  )
}

export function FinanceComparisonPanel() {
  const idPrefix = useId()
  const [metro, setMetro] = useState<MoneyFormState>(EMPTY_MONEY_FORM)
  const [jeonbuk, setJeonbuk] = useState<MoneyFormState>(EMPTY_MONEY_FORM)
  const [formError, setFormError] = useState<string | null>(null)
  const [state, setState] = useState<
    { status: 'idle' } | { status: 'loading' } | { status: 'success'; result: FinancialComparison } | { status: 'error'; error: ApiClientError }
  >({ status: 'idle' })

  function toOption(label: string, form: MoneyFormState): FinancialOption | null {
    const monthly_income_after_tax = parseNonNegative(form.monthly_income_after_tax)
    const monthly_housing_cost = parseNonNegative(form.monthly_housing_cost)
    const monthly_other_living_cost = parseNonNegative(form.monthly_other_living_cost)
    const deposit = parseNonNegative(form.deposit)
    if (
      monthly_income_after_tax === null ||
      monthly_housing_cost === null ||
      monthly_other_living_cost === null ||
      deposit === null
    ) {
      return null
    }
    return { label, monthly_income_after_tax, monthly_housing_cost, monthly_other_living_cost, deposit }
  }

  async function handleSubmit(event: React.FormEvent) {
    event.preventDefault()
    const metropolitan = toOption('수도권', metro)
    const jb = toOption('전북', jeonbuk)
    if (!metropolitan || !jb) {
      setFormError('모든 항목을 0 이상의 숫자로 입력해 주세요.')
      setState({ status: 'idle' })
      return
    }
    setFormError(null)
    setState({ status: 'loading' })
    try {
      const result = await compareFinance({ metropolitan, jeonbuk: jb })
      setState({ status: 'success', result })
    } catch (err) {
      setState({ status: 'error', error: err instanceof ApiClientError ? err : new ApiClientError({ code: 'unexpected_response', message: '알 수 없는 오류가 발생했습니다.' }) })
    }
  }

  return (
    <div className="rounded-card border border-ink-border bg-white p-5">
      <h3 className="flex items-center gap-2 font-bold text-ink-900">
        <Wallet size={18} aria-hidden="true" className="text-brand-blue" />
        자금축적 비교 (1년 · 3년)
      </h3>
      <p className="mt-1 text-xs text-ink-400">
        입력한 값만 사용하는 결정론적 계산입니다. 추천 점수나 승자는 표시하지 않습니다.
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

      {state.status === 'success' && <ResultCard result={state.result} />}
    </div>
  )
}
