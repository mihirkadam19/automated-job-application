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

function NavRow({
  label,
  icon,
  to,
}: {
  label: string
  icon: string
  to: string | null
}) {
  const content = (isActive: boolean) => (
    <span
      className={`flex h-11 w-full items-center gap-2.5 rounded-pill px-3 text-[15px] font-medium transition-colors ${
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
      className="block rounded-pill focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-primary focus-visible:ring-offset-2"
    >
      {({ isActive }) => content(isActive)}
    </NavLink>
  )
}

export function Sidebar() {
  return (
    <aside className="sticky top-0 flex h-svh w-[219px] shrink-0 flex-col bg-surface">
      <div className="px-3 pt-5 pb-2">
        <img src={logo} alt="JobNova" className="h-10 w-auto" />
      </div>

      <nav className="flex flex-1 flex-col gap-2.5 overflow-y-auto px-3 py-4">
        <div className="flex flex-col gap-2.5">
          {primaryNav.map((item) => (
            <NavRow key={item.label} {...item} />
          ))}
        </div>
        <hr className="my-1 border-t border-black/5" />
        <div className="flex flex-col gap-2.5">
          {secondaryNav.map((item) => (
            <NavRow key={item.label} {...item} />
          ))}
        </div>
        <hr className="my-1 border-t border-black/5" />
        <div className="flex flex-col gap-2.5">
          {tertiaryNav.map((item) => (
            <NavRow key={item.label} {...item} />
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
    </aside>
  )
}
