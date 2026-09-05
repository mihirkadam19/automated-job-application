import { useEffect, useRef, useState } from 'react'
import refreshIcon from '../../assets/icons/refresh.svg'
import searchWindow from '../../assets/icons/search-window.svg'
import { Button } from '../ui/Button'

export type SortKey = 'top-matched' | 'most-recent' | 'salary'

const options: { key: SortKey; label: string }[] = [
  { key: 'top-matched', label: 'Top matched' },
  { key: 'most-recent', label: 'Most recent' },
  { key: 'salary', label: 'Highest salary' },
]

export function SortRow({
  value,
  onChange,
}: {
  value: SortKey
  onChange: (key: SortKey) => void
}) {
  const [open, setOpen] = useState(false)
  const rootRef = useRef<HTMLDivElement>(null)

  useEffect(() => {
    if (!open) return
    const onClickOutside = (e: MouseEvent) => {
      if (!rootRef.current?.contains(e.target as Node)) setOpen(false)
    }
    const onKeyDown = (e: KeyboardEvent) => {
      if (e.key === 'Escape') setOpen(false)
    }
    document.addEventListener('mousedown', onClickOutside)
    document.addEventListener('keydown', onKeyDown)
    return () => {
      document.removeEventListener('mousedown', onClickOutside)
      document.removeEventListener('keydown', onKeyDown)
    }
  }, [open])

  const activeLabel = options.find((o) => o.key === value)?.label

  return (
    <div className="flex flex-wrap items-center justify-between gap-3">
      <Button
        variant="purple"
        leftIcon={refreshIcon}
        className="px-6"
        tabIndex={-1}
        aria-disabled="true"
      >
        Change Job Reference
      </Button>

      <div ref={rootRef} className="relative">
        <Button
          variant="white"
          leftIcon={searchWindow}
          rightIcon={searchWindow}
          className="px-6"
          onClick={() => setOpen((o) => !o)}
          aria-haspopup="listbox"
          aria-expanded={open}
        >
          {activeLabel}
        </Button>

        {open && (
          <ul
            role="listbox"
            className="absolute right-0 top-full z-10 mt-2 w-48 overflow-hidden rounded-2xl bg-surface py-2 shadow-lg"
          >
            {options.map((o) => (
              <li key={o.key}>
                <button
                  type="button"
                  role="option"
                  aria-selected={o.key === value}
                  onClick={() => {
                    onChange(o.key)
                    setOpen(false)
                  }}
                  className={`w-full px-4 py-2 text-left text-sm focus-visible:outline-none focus-visible:bg-bg ${
                    o.key === value
                      ? 'font-medium text-primary'
                      : 'text-ink-2'
                  }`}
                >
                  {o.label}
                </button>
              </li>
            ))}
          </ul>
        )}
      </div>
    </div>
  )
}
