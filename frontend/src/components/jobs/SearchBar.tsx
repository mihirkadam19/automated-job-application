function SearchIcon({ className = '' }: { className?: string }) {
  return (
    <svg viewBox="0 0 20 20" fill="none" className={className}>
      <circle cx="9" cy="9" r="6.5" stroke="currentColor" strokeWidth={1.6} />
      <path
        d="M17 17l-3.5-3.5"
        stroke="currentColor"
        strokeWidth={1.6}
        strokeLinecap="round"
      />
    </svg>
  )
}

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

export function SearchBar({
  value,
  onChange,
}: {
  value: string
  onChange: (value: string) => void
}) {
  return (
    <div className="flex items-center gap-2.5 rounded-pill bg-surface px-4 py-3">
      <SearchIcon className="size-4 shrink-0 text-ink-2/50" />
      <input
        type="text"
        value={value}
        onChange={(e) => onChange(e.target.value)}
        placeholder="Search jobs, companies, or locations"
        aria-label="Search jobs"
        className="w-full bg-transparent text-sm text-ink-2 placeholder:text-ink-2/40 focus:outline-none"
      />
      {value && (
        <button
          type="button"
          onClick={() => onChange('')}
          aria-label="Clear search"
          className="shrink-0 text-ink-2/50 focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-primary focus-visible:ring-offset-2"
        >
          <CloseIcon className="size-4" />
        </button>
      )}
    </div>
  )
}
