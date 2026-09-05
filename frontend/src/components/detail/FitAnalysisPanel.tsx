import { useState } from 'react'
import aiGenerate from '../../assets/icons/ai-generate.svg'
import { useSubscription } from '../../context/SubscriptionContext'
import { sharedJobDetail } from '../../data/jobDetail'
import { MatchRing } from '../jobs/MatchRing'
import { Button } from '../ui/Button'

const { subScores, verdicts } = sharedJobDetail.fitAnalysis

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

function PanelBody() {
  const { isSubscribed, openUpgradeModal } = useSubscription()

  return (
    <div className="relative mt-5">
      <div
        className={
          isSubscribed ? undefined : 'pointer-events-none blur-md select-none'
        }
      >
        <div className="grid grid-cols-2 gap-3">
          {subScores.map((s) => (
            <div
              key={s.label}
              className="flex flex-col items-center gap-1.5 rounded-md bg-bg py-4"
            >
              <MatchRing
                score={s.score}
                size={46}
                color="var(--color-primary)"
                trackColor="#e8e8e8"
                showLabel={false}
              />
              <span className="text-xs font-medium text-black">{s.label}</span>
            </div>
          ))}
        </div>

        <hr className="my-5 border-t border-black/5" />

        <ul className="flex flex-col gap-4">
          {verdicts.map((v) => (
            <li key={v.label}>
              <p className="text-sm font-semibold text-ink-2">
                {v.label} {v.icon}
              </p>
              <p className="mt-1 text-sm leading-relaxed text-black/80">
                {v.body}
              </p>
            </li>
          ))}
        </ul>
      </div>

      {!isSubscribed && (
        <div className="absolute inset-0 flex items-center justify-center">
          <Button variant="dark" onClick={openUpgradeModal}>
            Upgrade to check
          </Button>
        </div>
      )}
    </div>
  )
}

export function FitAnalysisPanel() {
  const [expanded, setExpanded] = useState(false)

  return (
    <>
      {/* Desktop: normal inline panel */}
      <aside className="hidden lg:block lg:w-[290px] lg:shrink-0">
        <div className="sticky top-6 overflow-hidden rounded-2xl bg-surface p-6">
          <h3 className="text-base font-semibold text-ink">
            Why is this job a good fit for me?
          </h3>
          <PanelBody />
        </div>
      </aside>

      {/* Mobile: floating toggle + floating panel */}
      <div className="lg:hidden">
        <button
          type="button"
          onClick={() => setExpanded((e) => !e)}
          aria-expanded={expanded}
          aria-label={expanded ? 'Hide fit analysis' : 'Show fit analysis'}
          className="fixed right-4 bottom-4 z-40 flex items-center gap-2 rounded-pill bg-ink px-4 py-3 text-sm font-medium text-white shadow-lg focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-primary focus-visible:ring-offset-2"
        >
          <img src={aiGenerate} alt="" className="size-4 invert" />
          Fit
        </button>

        {expanded && (
          <div className="fixed inset-x-4 bottom-20 z-40 max-h-[70vh] overflow-y-auto rounded-2xl bg-surface p-6 shadow-2xl">
            <div className="flex items-start justify-between gap-2">
              <h3 className="text-base font-semibold text-ink">
                Why is this job a good fit for me?
              </h3>
              <button
                type="button"
                onClick={() => setExpanded(false)}
                aria-label="Close"
                className="shrink-0 text-ink-2/60 focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-primary focus-visible:ring-offset-2"
              >
                <CloseIcon className="size-5" />
              </button>
            </div>
            <PanelBody />
          </div>
        )}
      </div>
    </>
  )
}
