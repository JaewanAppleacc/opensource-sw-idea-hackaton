import { createContext, useCallback, useContext, useRef, useState } from 'react'
import type { ReactNode } from 'react'

interface ToastMessage {
  id: number
  text: string
}

interface ToastContextValue {
  announce: (text: string) => void
}

const ToastContext = createContext<ToastContextValue | null>(null)

export function ToastProvider({ children }: { children: ReactNode }) {
  const [messages, setMessages] = useState<ToastMessage[]>([])
  const idRef = useRef(0)

  const announce = useCallback((text: string) => {
    const id = idRef.current++
    setMessages((prev) => [...prev, { id, text }])
    window.setTimeout(() => {
      setMessages((prev) => prev.filter((m) => m.id !== id))
    }, 3200)
  }, [])

  return (
    <ToastContext.Provider value={{ announce }}>
      {children}
      <div
        role="status"
        aria-live="polite"
        className="pointer-events-none fixed inset-x-0 bottom-6 z-[70] flex flex-col items-center gap-2 px-4"
      >
        {messages.map((m) => (
          <div
            key={m.id}
            className="pointer-events-auto rounded-card bg-ink-900 px-4 py-3 text-sm font-medium text-white shadow-softer"
          >
            {m.text}
          </div>
        ))}
      </div>
    </ToastContext.Provider>
  )
}

export function useToast(): ToastContextValue {
  const ctx = useContext(ToastContext)
  if (!ctx) throw new Error('useToast must be used within a ToastProvider')
  return ctx
}
