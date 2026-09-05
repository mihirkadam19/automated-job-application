import { useEffect, useState } from 'react'
import { NavLink } from 'react-router-dom'
import airplay from '../../assets/icons/airplay.svg'
import briefcase from '../../assets/icons/briefcase.svg'
import extraCredits from '../../assets/icons/extra-credits.svg'
import fileText from '../../assets/icons/file-text.svg'
import paperclip from '../../assets/icons/paperclip.svg'
import settings from '../../assets/icons/settings.svg'
import subscription from '../../assets/icons/subscription.svg'
import logo from '../../assets/images/logo.png'

const primaryNav = [
  { label: 'Jobs', icon: briefcase, to: '/' },
  { label: 'AI Mock Interview', icon: airplay, to: null },
  { label: 'Resume', icon: fileText, to: null },
]

const secondaryNav = [
  { label: 'Profile', icon: paperclip, to: null },
  { label: 'Setting', icon: settings, to: null },
]

const tertiaryNav = [
  { label: 'Subscription', icon: subscription, to: null },
  { label: 'Extra Credits', icon: extraCredits, to: null },
]

function HamburgerIcon() {
  return (
    <svg viewBox="0 0 20 20" fill="none" className="size-5">
      <path
        d="M3 5.5h14M3 10h14M3 14.5h14"
        stroke="currentColor"
        strokeWidth={1.6}
        strokeLinecap="round"
      />
    </svg>
  )
}

function CloseIcon() {
  return (
    <svg viewBox="0 0 20 20" fill="none" className="size-5">
      <path
        d="M5 5l10 10M15 5L5 15"
        stroke="currentColor"
        strokeWidth={1.6}
        strokeLinecap="round"
      />
    </svg>
  )
}

function NavRow({
  label,
  icon,
  to,
  onNavigate,
}: {
  label: string
  icon: string
  to: string | null
  onNavigate?: () => void
}) {
  const content = (isActive: boolean) => (
    <span
      className={`flex h-11 w-full items-center gap-2.5 whitespace-nowrap rounded-pill px-3 text-[15px] font-medium transition-colors ${
        isActive ? 'bg-primary text-white' : 'text-ink-2'
      }`}
    >
      <img src={icon} alt="" className="size-[22px] shrink-0" />
      {label}
    </span>
  )

  if (!to) {
    return (
      <button
        type="button"
        tabIndex={-1}
        aria-disabled="true"
        className="w-full cursor-default text-left"
      >
        {content(false)}
      </button>
    )
  }

  return (
    <NavLink
      to={to}
      end
      onClick={onNavigate}
      className="block rounded-pill focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-primary focus-visible:ring-offset-2"
    >
      {({ isActive }) => content(isActive)}
    </NavLink>
  )
}

function NavContent({ onNavigate }: { onNavigate?: () => void }) {
  return (
    <>
      <nav className="flex flex-1 flex-col gap-2.5 overflow-y-auto px-3 py-4">
        <div className="flex flex-col gap-2.5">
          {primaryNav.map((item) => (
            <NavRow key={item.label} {...item} onNavigate={onNavigate} />
          ))}
        </div>
        <hr className="my-1 border-t border-black/5" />
        <div className="flex flex-col gap-2.5">
          {secondaryNav.map((item) => (
            <NavRow key={item.label} {...item} onNavigate={onNavigate} />
          ))}
        </div>
        <hr className="my-1 border-t border-black/5" />
        <div className="flex flex-col gap-2.5">
          {tertiaryNav.map((item) => (
            <NavRow key={item.label} {...item} onNavigate={onNavigate} />
          ))}
        </div>
      </nav>

      <div className="p-3">
        <div className="relative overflow-hidden rounded-2xl bg-gradient-to-br from-accent to-primary px-4 py-5 text-white">
          <p className="text-lg font-medium">Upgrade Your Plan</p>
          <p className="mt-2 text-sm leading-snug text-white/85">
            Boost your success rate now!
          </p>
          <button
            type="button"
            tabIndex={-1}
            aria-disabled="true"
            className="mt-4 w-full rounded-pill bg-white py-2.5 text-sm font-medium text-ink"
          >
            Subscription
          </button>
        </div>
      </div>
    </>
  )
}

export function Sidebar() {
  const [open, setOpen] = useState(false)

  useEffect(() => {
    if (!open) return
    const onKeyDown = (e: KeyboardEvent) => {
      if (e.key === 'Escape') setOpen(false)
    }
    document.addEventListener('keydown', onKeyDown)
    document.body.style.overflow = 'hidden'
    return () => {
      document.removeEventListener('keydown', onKeyDown)
      document.body.style.overflow = ''
    }
  }, [open])

  return (
    <>
      {/* Mobile top bar */}
      <div className="flex items-center justify-between bg-surface px-4 py-3 lg:hidden">
        <img src={logo} alt="JobNova" className="h-8 w-auto" />
        <button
          type="button"
          onClick={() => setOpen(true)}
          aria-label="Open menu"
          aria-expanded={open}
          className="flex size-9 items-center justify-center rounded-pill text-ink-2 focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-primary focus-visible:ring-offset-2"
        >
          <HamburgerIcon />
        </button>
      </div>

      {/* Mobile drawer */}
      {open && (
        <div className="fixed inset-0 z-50 lg:hidden">
          <button
            type="button"
            aria-label="Close menu"
            onClick={() => setOpen(false)}
            className="absolute inset-0 bg-black/40"
          />
          <div className="absolute inset-y-0 left-0 flex w-72 max-w-[80vw] flex-col bg-surface shadow-xl">
            <div className="flex items-center justify-between px-4 pt-4 pb-2">
              <img src={logo} alt="JobNova" className="h-8 w-auto" />
              <button
                type="button"
                onClick={() => setOpen(false)}
                aria-label="Close menu"
                className="flex size-9 items-center justify-center rounded-pill text-ink-2 focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-primary focus-visible:ring-offset-2"
              >
                <CloseIcon />
              </button>
            </div>
            <NavContent onNavigate={() => setOpen(false)} />
          </div>
        </div>
      )}

      {/* Desktop sidebar */}
      <aside className="hidden bg-surface lg:sticky lg:top-0 lg:flex lg:h-svh lg:w-[219px] lg:shrink-0 lg:flex-col">
        <div className="px-3 pt-5 pb-2">
          <img src={logo} alt="JobNova" className="h-10 w-auto" />
        </div>
        <NavContent />
      </aside>
    </>
  )
}
