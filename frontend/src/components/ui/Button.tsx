import type { ButtonHTMLAttributes, ReactNode } from 'react'

// Hover styling matches the actual hover variants defined in the Figma
// component set (Button, componentSetId 297:611): "second" (white/outline)
// buttons swap their border to lime on hover; "Primary" buttons swap their
// fill to lime (with dark text/icons for contrast, since lime is light).
const variants = {
  white: 'bg-white text-ink-2 border border-[#b1adad]/50 hover:border-lime',
  lime: 'bg-lime text-ink-2',
  dark: 'bg-ink text-white hover:bg-lime hover:text-ink-2',
  purple: 'bg-primary text-white',
} as const

const iconVariants = {
  white: '',
  lime: '',
  dark: 'group-hover:invert',
  purple: '',
} as const

export function Button({
  variant = 'white',
  leftIcon,
  rightIcon,
  children,
  className = '',
  ...rest
}: {
  variant?: keyof typeof variants
  leftIcon?: string
  rightIcon?: string
  children: ReactNode
  className?: string
} & ButtonHTMLAttributes<HTMLButtonElement>) {
  const iconClass = `size-4 ${iconVariants[variant]}`

  return (
    <button
      type="button"
      className={`group flex items-center justify-center gap-2.5 rounded-pill px-4.5 py-2.5 text-sm font-medium transition-colors duration-300 disabled:cursor-not-allowed disabled:opacity-60 focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-primary focus-visible:ring-offset-2 ${variants[variant]} ${className}`}
      {...rest}
    >
      {leftIcon && <img src={leftIcon} alt="" className={iconClass} />}
      {children}
      {rightIcon && <img src={rightIcon} alt="" className={iconClass} />}
    </button>
  )
}
