import searchWindowWhite from '../../assets/icons/search-window-white.svg'
import { useSubscription } from '../../context/SubscriptionContext'
import { useToast } from '../../context/ToastContext'
import { Button } from './Button'

export function UpgradeModal() {
  const { isModalOpen, closeUpgradeModal, upgrade } = useSubscription()
  const { showToast } = useToast()

  if (!isModalOpen) return null

  const handleUpgrade = () => {
    upgrade()
    showToast("You're subscribed! Fit analysis unlocked.")
  }

  return (
    <div className="fixed inset-0 z-[60] flex items-center justify-center p-4">
      <button
        type="button"
        aria-label="Close"
        onClick={closeUpgradeModal}
        className="absolute inset-0 bg-black/40"
      />

      <div className="relative w-full max-w-sm rounded-2xl bg-surface p-6 text-center shadow-xl">
        <button
          type="button"
          onClick={closeUpgradeModal}
          aria-label="Close"
          className="absolute right-4 top-4 text-ink-2/50 focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-primary focus-visible:ring-offset-2"
        >
          ✕
        </button>

        <p className="text-lg font-semibold text-ink">Preview: Paid Subscription</p>
        <p className="mt-3 text-sm leading-relaxed text-ink-2/80">
          This is a preview of the paid plan. Subscribe to unlock the full AI
          fit analysis for every job.
        </p>

        <div className="mt-6 flex flex-col gap-2">
          <Button
            variant="dark"
            leftIcon={searchWindowWhite}
            onClick={handleUpgrade}
            className="w-full"
          >
            Upgrade Now
          </Button>
          <button
            type="button"
            onClick={closeUpgradeModal}
            className="py-2 text-sm font-medium text-ink-2/70 focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-primary focus-visible:ring-offset-2"
          >
            Maybe later
          </button>
        </div>
      </div>
    </div>
  )
}
