import type { ReactNode } from 'react'

export function TagPill({ children }: { children: ReactNode }) {
  return (
    <span className="whitespace-nowrap rounded-pill border border-[#e8e8e8] px-4 py-1.5 text-sm text-ink-2">
      {children}
    </span>
  )
}
