import { useMemo, useState } from 'react'
import { RightRail } from '../components/layout/RightRail'
import { JobCard } from '../components/jobs/JobCard'
import { SortRow } from '../components/jobs/SortRow'
import { TabBar, type JobTab } from '../components/jobs/TabBar'
import { defaultAppliedIds, defaultLikedIds, jobs } from '../data/jobs'
import { useJobInteractions } from '../hooks/useJobInteractions'

export function JobListPage() {
  const [tab, setTab] = useState<JobTab>('matched')
  const { likedIds, toggleLiked, appliedIds, markApplied } =
    useJobInteractions(defaultLikedIds, defaultAppliedIds)

  const visibleJobs = useMemo(() => {
    if (tab === 'liked') return jobs.filter((j) => likedIds.has(j.id))
    if (tab === 'applied') return jobs.filter((j) => appliedIds.has(j.id))
    return jobs
  }, [tab, likedIds, appliedIds])

  return (
    <div>
      <TabBar
        active={tab}
        onChange={setTab}
        counts={{ liked: likedIds.size, applied: appliedIds.size }}
      />

      <div className="flex gap-6 p-6">
        <div className="min-w-0 flex-1 space-y-4">
          <SortRow />

          {visibleJobs.length === 0 ? (
            <div className="flex h-40 items-center justify-center rounded-card bg-surface text-sm text-muted-2">
              No jobs in "{tab}" yet.
            </div>
          ) : (
            visibleJobs.map((job) => (
              <JobCard
                key={job.id}
                job={job}
                liked={likedIds.has(job.id)}
                applied={appliedIds.has(job.id)}
                onToggleLike={() => toggleLiked(job.id)}
                onApply={() => markApplied(job.id)}
              />
            ))
          )}
        </div>

        <RightRail />
      </div>
    </div>
  )
}
