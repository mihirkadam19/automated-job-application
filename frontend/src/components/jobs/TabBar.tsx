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
    <div role="tablist" className="flex items-stretch bg-surface px-6">
      {tabs.map((tab, i) => {
        const isActive = tab.key === active
        const count = counts[tab.key]
        return (
          <div key={tab.key} className="flex items-stretch">
            {i > 0 && <span className="my-5 w-px bg-black/10" />}
            <button
              type="button"
              role="tab"
              aria-selected={isActive}
              onClick={() => onChange(tab.key)}
              className={`flex items-center gap-2 px-6 py-5 text-base font-medium focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-primary focus-visible:ring-offset-2 ${
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
