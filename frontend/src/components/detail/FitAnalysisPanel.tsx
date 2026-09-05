import aiGenerate from '../../assets/icons/ai-generate.svg'
import { useSubscription } from '../../context/SubscriptionContext'
import { sharedJobDetail } from '../../data/jobDetail'
import { MatchRing } from '../jobs/MatchRing'
import { Button } from '../ui/Button'
import { MobileFloatingPanel } from '../ui/MobileFloatingPanel'

const { subScores, verdicts } = sharedJobDetail.fitAnalysis
const title = 'Why is this job a good fit for me?'

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
  return (
    <>
      <aside className="hidden lg:block lg:w-[290px] lg:shrink-0">
        <div className="sticky top-6 overflow-hidden rounded-2xl bg-surface p-6">
          <h3 className="text-base font-semibold text-ink">{title}</h3>
          <PanelBody />
        </div>
      </aside>

      <MobileFloatingPanel label="Fit" icon={aiGenerate} title={title}>
        <PanelBody />
      </MobileFloatingPanel>
    </>
  )
}
