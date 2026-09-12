import type { ReactNode } from 'react'

interface ContainerProps {
  children: ReactNode
  className?: string
  as?: 'div' | 'section'
}

export function Container({ children, className = '', as = 'div' }: ContainerProps) {
  const Tag = as
  return <Tag className={`content-container ${className}`}>{children}</Tag>
}
