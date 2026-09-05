import { MatchRing } from '../jobs/MatchRing'
import { sharedJobDetail } from '../../data/jobDetail'

const { subScores, verdicts } = sharedJobDetail.fitAnalysis

export function FitAnalysisPanel() {
  return (
    <aside className="w-[290px] shrink-0">
      <div className="sticky top-6 rounded-2xl bg-surface p-6">
        <h3 className="text-base font-semibold text-ink">
          Why is this job a good fit for me?
        </h3>

        <div className="mt-5 grid grid-cols-2 gap-3">
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
              <span className="text-xs font-medium text-black">
                {s.label}
              </span>
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
    </aside>
  )
}
