import type { ButtonHTMLAttributes, ReactNode } from 'react'

const variants = {
  white: 'bg-white text-ink-2 border border-[#b1adad]/50',
  lime: 'bg-lime text-ink-2',
  dark: 'bg-ink text-white',
  purple: 'bg-primary text-white',
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
  return (
    <button
      type="button"
      className={`flex items-center justify-center gap-2.5 rounded-pill px-4.5 py-2.5 text-sm font-medium disabled:cursor-not-allowed disabled:opacity-60 ${variants[variant]} ${className}`}
      {...rest}
    >
      {leftIcon && <img src={leftIcon} alt="" className="size-4" />}
      {children}
      {rightIcon && <img src={rightIcon} alt="" className="size-4" />}
    </button>
  )
}
