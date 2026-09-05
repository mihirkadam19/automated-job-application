import { useState, type ReactNode } from 'react'

function CloseIcon({ className = '' }: { className?: string }) {
  return (
    <svg viewBox="0 0 20 20" fill="none" className={className}>
      <path
        d="M5 5l10 10M15 5L5 15"
        stroke="currentColor"
        strokeWidth={1.6}
        strokeLinecap="round"
      />
    </svg>
  )
}

export function MobileFloatingPanel({
  label,
  icon,
  title,
  children,
}: {
  label: string
  icon: string
  title: string
  children: ReactNode
}) {
  const [expanded, setExpanded] = useState(false)

  return (
    <div className="lg:hidden">
      <button
        type="button"
        onClick={() => setExpanded((e) => !e)}
        aria-expanded={expanded}
        aria-label={expanded ? `Hide ${label}` : `Show ${label}`}
        className="fixed right-4 bottom-4 z-40 flex items-center gap-2 rounded-pill bg-ink px-4 py-3 text-sm font-medium text-white shadow-lg focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-primary focus-visible:ring-offset-2"
      >
        <img src={icon} alt="" className="size-4 invert" />
        {label}
      </button>

      {expanded && (
        <div className="fixed inset-x-4 bottom-20 z-40 max-h-[70vh] overflow-y-auto rounded-2xl bg-surface p-6 shadow-2xl">
          <div className="flex items-start justify-between gap-2">
            <h3 className="text-base font-semibold text-ink">{title}</h3>
            <button
              type="button"
              onClick={() => setExpanded(false)}
              aria-label="Close"
              className="shrink-0 text-ink-2/60 focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-primary focus-visible:ring-offset-2"
            >
              <CloseIcon className="size-5" />
            </button>
          </div>
          {children}
        </div>
      )}
    </div>
  )
}
