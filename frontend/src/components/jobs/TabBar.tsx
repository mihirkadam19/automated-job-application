export type JobTab = 'matched' | 'liked' | 'applied'

const tabs: { key: JobTab; label: string }[] = [
  { key: 'matched', label: 'Matched' },
  { key: 'liked', label: 'Liked' },
  { key: 'applied', label: 'Applied' },
]

export function TabBar({
  active,
  onChange,
  counts,
}: {
  active: JobTab
  onChange: (tab: JobTab) => void
  counts: Partial<Record<JobTab, number>>
}) {
  return (
    <div
      role="tablist"
      className="flex items-stretch overflow-x-auto bg-surface px-4 lg:px-6"
    >
      {tabs.map((tab, i) => {
        const isActive = tab.key === active
        const count = counts[tab.key]
        return (
          <div key={tab.key} className="flex shrink-0 items-stretch">
            {i > 0 && <span className="my-4 w-px shrink-0 bg-black/10 lg:my-5" />}
            <button
              type="button"
              role="tab"
              aria-selected={isActive}
              onClick={() => onChange(tab.key)}
              className={`flex shrink-0 items-center gap-2 px-3 py-4 text-sm font-medium whitespace-nowrap focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-primary focus-visible:ring-offset-2 lg:px-6 lg:py-5 lg:text-base ${
                isActive ? 'text-primary' : 'text-ink-2/70'
              }`}
            >
              {tab.label}
              {!!count && (
                <span className="flex h-[18px] min-w-[18px] items-center justify-center rounded-pill bg-lime px-1 text-xs font-medium text-ink">
                  {count}
                </span>
              )}
            </button>
          </div>
        )
      })}
    </div>
  )
}
