import heartIcon from '../../assets/icons/heart.svg'
import locationPin from '../../assets/icons/location-pin.svg'
import workModeIcon from '../../assets/icons/work-mode.svg'
import type { Job } from '../../data/jobs'
import { MatchRing } from '../jobs/MatchRing'

export function DetailHero({ job }: { job: Job }) {
  return (
    <div className="flex items-start gap-3 lg:gap-6">
      <span className="size-16 shrink-0 rounded-card bg-bg lg:size-[90px]" />

      <div className="min-w-0 flex-1">
        <div className="flex items-center gap-1.5">
          <img src={heartIcon} alt="" className="size-4 opacity-60" />
          <span className="rounded-pill bg-accent/[0.12] px-3 py-1 text-sm text-ink-2">
            {job.postedAt}
          </span>
        </div>

        <h1 className="mt-3 min-w-0 text-lg font-semibold text-black lg:text-2xl">
          {job.title}
        </h1>
        <p className="mt-2 text-base font-medium text-muted">{job.company}</p>

        <div className="mt-3 flex flex-wrap items-center gap-2 text-sm text-ink-2">
          <span className="flex items-center gap-1">
            <img src={locationPin} alt="" className="size-3.5" />
            {job.location}
          </span>
          <span className="size-1.5 rounded-full bg-accent" />
          <span>{job.postedAt}</span>
          <span className="size-1.5 rounded-full bg-accent" />
          <span className="flex items-center gap-1.5">
            <img src={workModeIcon} alt="" className="size-3.5" />
            {job.workMode}
          </span>
        </div>
      </div>

      <span className="shrink-0">
        <MatchRing score={job.matchScore} size={93} />
      </span>
    </div>
  )
}
