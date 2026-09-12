import { Copy, MessageSquareText } from 'lucide-react'
import { useMemo, useState } from 'react'
import type { PriorityItem } from '../../lib/priorityUnresolved'
import { useToast } from '../ui/ToastProvider'

interface QuestionEntry {
  id: string
  region: 'metro' | 'jeonbuk'
  axisLabel: string
  prompt: string
}

interface CompanyQuestionsPanelProps {
  items: PriorityItem[]
  metroLabel: string
  jeonbukLabel: string
}

/**
 * "지원 전 확인할 질문" checklist (TASK "UI 고도화" section 11) --
 * fact-based, backend-generated verification prompts the applicant can
 * check off and copy. Never shows a fabricated company answer; the note
 * field is opt-in per question, not shown by default, so the checklist
 * itself stays scannable.
 */
export function CompanyQuestionsPanel({ items, metroLabel, jeonbukLabel }: CompanyQuestionsPanelProps) {
  const { announce } = useToast()
  const [checkedIds, setCheckedIds] = useState<Set<string>>(new Set())
  const [noteOpenId, setNoteOpenId] = useState<string | null>(null)
  const [notes, setNotes] = useState<Record<string, string>>({})

  const questions = useMemo<QuestionEntry[]>(() => {
    const seen = new Set<string>()
    const list: QuestionEntry[] = []
    for (const item of items) {
      if (!item.action) continue
      const key = `${item.region}:${item.action.prompt}`
      if (seen.has(key)) continue
      seen.add(key)
      list.push({ id: key, region: item.region, axisLabel: item.axisLabel, prompt: item.action.prompt })
    }
    return list
  }, [items])

  async function handleCopy(prompt: string) {
    try {
      await navigator.clipboard.writeText(prompt)
      announce('질문을 복사했어요.')
    } catch {
      announce('복사에 실패했어요. 직접 선택해서 복사해 주세요.')
    }
  }

  function toggleChecked(id: string) {
    setCheckedIds((prev) => {
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
    <div>
      <p className="flex items-center gap-1.5 text-sm font-bold text-ink-900">
        <MessageSquareText size={15} aria-hidden="true" className="text-brand-blue" />
        지원 전 확인할 질문
      </p>
      <p className="mt-0.5 text-xs text-ink-400">공고에서 확인되지 않은 조건을 질문으로 정리했습니다.</p>

      <ul className="mt-2.5 divide-y divide-ink-border rounded-card border border-ink-border">
        {questions.map((q) => (
          <li key={q.id} className="p-3">
            <label className="flex cursor-pointer items-start gap-2.5">
              <input
                type="checkbox"
                checked={checkedIds.has(q.id)}
                onChange={() => toggleChecked(q.id)}
                className="mt-0.5"
              />
              <span className="min-w-0 flex-1">
                <span
                  className={`block text-sm ${checkedIds.has(q.id) ? 'text-ink-400 line-through' : 'text-ink-900'}`}
                >
                  {q.prompt}
                </span>
                <span className="mt-0.5 block text-[11px] text-ink-400">
                  {q.region === 'metro' ? metroLabel : jeonbukLabel} · {q.axisLabel}
                </span>
              </span>
            </label>
            <div className="mt-2 flex flex-wrap items-center gap-3 pl-6">
              <button
                type="button"
                onClick={() => void handleCopy(q.prompt)}
                className="flex items-center gap-1 text-[11px] font-medium text-ink-500 hover:text-brand-blue"
              >
                <Copy size={11} aria-hidden="true" />
                복사
              </button>
              <button
                type="button"
                onClick={() => setNoteOpenId(noteOpenId === q.id ? null : q.id)}
                className="text-[11px] font-medium text-ink-500 hover:text-brand-blue"
              >
                {noteOpenId === q.id ? '메모 닫기' : '메모 추가'}
              </button>
            </div>
            {noteOpenId === q.id && (
              <div className="mt-2 pl-6">
                <label className="text-[10px] font-medium text-ink-400">내 메모 (기업의 실제 답변이 아닙니다)</label>
                <textarea
                  value={notes[q.id] ?? ''}
                  onChange={(e) => setNotes((prev) => ({ ...prev, [q.id]: e.target.value }))}
                  rows={2}
                  placeholder="이 질문에 대한 나만의 메모를 남겨보세요."
                  className="mt-1 w-full resize-y rounded-card border border-ink-border bg-surface-muted px-2 py-1.5 text-xs text-ink-700 outline-none focus:border-brand-blue"
                />
              </div>
            )}
          </li>
        ))}
      </ul>
    </div>
  )
}
