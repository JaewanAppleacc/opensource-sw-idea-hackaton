import { Check, Copy, Filter, MessageSquareText } from 'lucide-react'
import { useMemo, useState } from 'react'
import type { PriorityItem } from '../../lib/priorityUnresolved'
import { CHANNEL_LABELS } from '../../lib/displayLabels'
import { useToast } from '../ui/ToastProvider'

interface QuestionEntry {
  id: string
  region: 'metro' | 'jeonbuk'
  axisLabel: string
  prompt: string
  channelLabel: string
}

interface CompanyQuestionsPanelProps {
  items: PriorityItem[]
  metroLabel: string
  jeonbukLabel: string
}

/**
 * Fact-based, backend-generated verification prompts, re-surfaced as
 * copyable/saveable questions the applicant can actually send. Never shows
 * a fabricated company answer -- only an optional personal note the user
 * types themselves, explicitly labeled as such (TASK section 9).
 */
export function CompanyQuestionsPanel({ items, metroLabel, jeonbukLabel }: CompanyQuestionsPanelProps) {
  const { announce } = useToast()
  const [savedIds, setSavedIds] = useState<Set<string>>(new Set())
  const [showSavedOnly, setShowSavedOnly] = useState(false)
  const [notes, setNotes] = useState<Record<string, string>>({})

  const questions = useMemo<QuestionEntry[]>(() => {
    const seen = new Set<string>()
    const list: QuestionEntry[] = []
    for (const item of items) {
      if (!item.action) continue
      const key = `${item.region}:${item.action.prompt}`
      if (seen.has(key)) continue
      seen.add(key)
      list.push({
        id: key,
        region: item.region,
        axisLabel: item.axisLabel,
        prompt: item.action.prompt,
        channelLabel: CHANNEL_LABELS[item.action.channel],
      })
    }
    return list
  }, [items])

  const visibleQuestions = showSavedOnly ? questions.filter((q) => savedIds.has(q.id)) : questions

  async function handleCopy(prompt: string) {
    try {
      await navigator.clipboard.writeText(prompt)
      announce('질문을 복사했어요.')
    } catch {
      announce('복사에 실패했어요. 직접 선택해서 복사해 주세요.')
    }
  }

  function toggleSaved(id: string) {
    setSavedIds((prev) => {
      const next = new Set(prev)
      if (next.has(id)) next.delete(id)
      else next.add(id)
      return next
    })
  }

  if (questions.length === 0) {
    return null
  }

  return (
    <div className="rounded-card border border-ink-border bg-white p-4">
      <div className="flex flex-wrap items-center justify-between gap-2">
        <p className="flex items-center gap-1.5 text-sm font-bold text-ink-900">
          <MessageSquareText size={15} aria-hidden="true" className="text-brand-blue" />
          기업에 물어볼 질문
        </p>
        <button
          type="button"
          onClick={() => setShowSavedOnly((v) => !v)}
          className={`flex items-center gap-1 rounded-pill px-3 py-1 text-[11px] font-semibold transition ${
            showSavedOnly ? 'bg-brand-blue text-white' : 'border border-ink-border text-ink-500 hover:border-brand-blue'
          }`}
        >
          <Filter size={11} aria-hidden="true" />
          선택한 질문만 보기
        </button>
      </div>

      <ul className="mt-3 space-y-3">
        {visibleQuestions.map((q) => (
          <li key={q.id} className="rounded-card border border-ink-border p-3">
            <p className="text-[11px] text-ink-400">
              {q.region === 'metro' ? metroLabel : jeonbukLabel} · {q.axisLabel} · {q.channelLabel}
            </p>
            <p className="mt-1 text-sm text-ink-900">{q.prompt}</p>
            <div className="mt-2 flex flex-wrap gap-2">
              <button
                type="button"
                onClick={() => void handleCopy(q.prompt)}
                className="flex items-center gap-1 rounded-pill border border-ink-border px-2.5 py-1 text-[11px] font-medium text-ink-700 hover:border-brand-blue hover:text-brand-blue"
              >
                <Copy size={11} aria-hidden="true" />
                질문 복사
              </button>
              <button
                type="button"
                onClick={() => toggleSaved(q.id)}
                className={`flex items-center gap-1 rounded-pill px-2.5 py-1 text-[11px] font-medium transition ${
                  savedIds.has(q.id)
                    ? 'bg-brand-green/10 text-brand-green'
                    : 'border border-ink-border text-ink-700 hover:border-brand-blue hover:text-brand-blue'
                }`}
              >
                <Check size={11} aria-hidden="true" />
                {savedIds.has(q.id) ? '저장됨' : '질문 목록에 저장'}
              </button>
            </div>
            <div className="mt-2">
              <label className="text-[10px] font-medium text-ink-400">내 메모 (기업의 실제 답변이 아닙니다)</label>
              <textarea
                value={notes[q.id] ?? ''}
                onChange={(e) => setNotes((prev) => ({ ...prev, [q.id]: e.target.value }))}
                rows={2}
                placeholder="이 질문에 대한 나만의 메모를 남겨보세요."
                className="mt-1 w-full resize-y rounded-card border border-ink-border bg-surface-muted px-2 py-1.5 text-xs text-ink-700 outline-none focus:border-brand-blue"
              />
            </div>
          </li>
        ))}
      </ul>
    </div>
  )
}
