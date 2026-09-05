import { createContext, useContext, useState, type ReactNode } from 'react'

type SubscriptionContextValue = {
  isSubscribed: boolean
  isModalOpen: boolean
  openUpgradeModal: () => void
  closeUpgradeModal: () => void
  upgrade: () => void
}

const SubscriptionContext = createContext<SubscriptionContextValue | null>(null)

export function SubscriptionProvider({ children }: { children: ReactNode }) {
  const [isSubscribed, setIsSubscribed] = useState(false)
  const [isModalOpen, setIsModalOpen] = useState(false)

  return (
    <SubscriptionContext.Provider
      value={{
        isSubscribed,
        isModalOpen,
        openUpgradeModal: () => setIsModalOpen(true),
        closeUpgradeModal: () => setIsModalOpen(false),
        upgrade: () => {
          setIsSubscribed(true)
          setIsModalOpen(false)
        },
      }}
    >
      {children}
    </SubscriptionContext.Provider>
  )
}

export function useSubscription() {
  const ctx = useContext(SubscriptionContext)
  if (!ctx) {
    throw new Error('useSubscription must be used within a SubscriptionProvider')
  }
  return ctx
}
