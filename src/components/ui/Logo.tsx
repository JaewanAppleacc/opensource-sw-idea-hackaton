interface LogoProps {
  className?: string
}

/**
 * Original placeholder emblem for this learning clone — not the real
 * government CI. A simple two-tone abstract swirl, unrelated to any
 * official mark.
 */
export function Logo({ className = '' }: LogoProps) {
  return (
    <span className={`inline-flex items-center gap-2 ${className}`}>
      <svg width="32" height="32" viewBox="0 0 32 32" aria-hidden="true" focusable="false">
        <circle cx="16" cy="16" r="16" fill="#3F58D4" />
        <path
          d="M16 4a12 12 0 0 1 0 24 6 6 0 0 1 0-12 6 6 0 0 0 0-12Z"
          fill="#7E89FD"
        />
        <circle cx="16" cy="10" r="2.4" fill="#3F58D4" />
        <circle cx="16" cy="22" r="2.4" fill="#EBE5FF" />
      </svg>
      <span className="text-xl font-bold tracking-tight text-ink-900">
        고용24
      </span>
    </span>
  )
}
