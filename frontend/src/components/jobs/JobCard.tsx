import { useNavigate } from 'react-router-dom'
import expandIcon from '../../assets/icons/expand.svg'
import heartIcon from '../../assets/icons/heart.svg'
import locationPin from '../../assets/icons/location-pin.svg'
import searchWindow from '../../assets/icons/search-window.svg'
import workMode from '../../assets/icons/work-mode.svg'
import type { Job } from '../../data/jobs'
import { Button } from '../ui/Button'
import { MatchRing } from './MatchRing'
import { TagPill } from './TagPill'

export function JobCard({
  job,
  liked,
  applied,
  onToggleLike,
  onApply,
}: {
  job: Job
  liked: boolean
  applied: boolean
  onToggleLike: () => void
  onApply: () => void
}) {
  const navigate = useNavigate()

  return (
    <article
      onClick={() => navigate(`/jobs/${job.id}`)}
      className="cursor-pointer rounded-card bg-surface px-[26px] py-4"
    >
      <div className="flex items-start gap-5">
        <MatchRing score={job.matchScore} />

        <div className="min-w-0 flex-1">
          <div className="flex items-start justify-between gap-4">
            <h3 className="text-2xl font-semibold leading-snug text-black">
              {job.title}
            </h3>
            <div className="flex shrink-0 items-center gap-3 pt-1.5">
              <button type="button" onClick={(e) => e.stopPropagation()}>
                <img src={expandIcon} alt="Expand" className="size-[19px]" />
              </button>
              <button
                type="button"
                onClick={(e) => {
                  e.stopPropagation()
                  onToggleLike()
                }}
                className={`rounded-full p-1 ${liked ? 'bg-primary/10' : ''}`}
              >
                <img
                  src={heartIcon}
                  alt={liked ? 'Unlike' : 'Like'}
                  className="size-[19px]"
                />
              </button>
            </div>
          </div>

          <div className="mt-3 flex items-center gap-1.5">
            <span className="size-[22px] shrink-0 rounded bg-bg" />
            <span className="text-base font-medium text-muted">
              {job.company}
            </span>
          </div>

          <div className="mt-2 flex flex-wrap items-center gap-2 text-[15px] text-ink-2">
            <span className="flex items-center gap-1">
              <img src={locationPin} alt="" className="size-3.5" />
              {job.location}
            </span>
            <span className="size-1.5 rounded-full bg-accent" />
            <span className="flex items-center gap-1.5">
              <img src={workMode} alt="" className="size-3.5" />
              {job.workMode}
            </span>
          </div>
        </div>
      </div>

      <div className="mt-6 flex flex-wrap gap-2">
        <TagPill>{job.employmentType}</TagPill>
        <TagPill>{job.levelTag}</TagPill>
        <TagPill>{job.experienceTag}</TagPill>
        <TagPill>{job.seniority}</TagPill>
        <TagPill>{job.salaryRange}</TagPill>
      </div>

      <div className="mt-4.5 flex flex-wrap items-center justify-between gap-3">
        <div className="flex items-center gap-3">
          <span className="flex items-center gap-1.5 rounded-pill bg-accent/[0.12] px-3 py-1.5 text-sm text-ink-2">
            <img src={locationPin} alt="" className="size-3.5" />
            {job.postedAt}
          </span>
          <span className="text-sm text-ink-2">{job.applicants} applicants</span>
        </div>

        <div
          className="flex items-center gap-3"
          onClick={(e) => e.stopPropagation()}
        >
          <Button
            variant="white"
            leftIcon={searchWindow}
            rightIcon={searchWindow}
            disabled={applied}
            onClick={onApply}
          >
            {applied ? 'Applied' : 'Apply'}
          </Button>
          <Button variant="lime" leftIcon={searchWindow} rightIcon={searchWindow}>
            Mock Interview
          </Button>
        </div>
      </div>
    </article>
  )
}
