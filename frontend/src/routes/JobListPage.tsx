import { useEffect, useMemo, useState } from 'react'
import { useSearchParams } from 'react-router-dom'
import { RightRail } from '../components/layout/RightRail'
import { JobCard } from '../components/jobs/JobCard'
import { JobCardSkeleton } from '../components/jobs/JobCardSkeleton'
import { SearchBar } from '../components/jobs/SearchBar'
import { SortRow, type SortKey } from '../components/jobs/SortRow'
import { TabBar, type JobTab } from '../components/jobs/TabBar'
import { useToast } from '../context/ToastContext'
import { defaultAppliedIds, defaultLikedIds, jobs } from '../data/jobs'
import { useJobInteractions } from '../hooks/useJobInteractions'

const validTabs: JobTab[] = ['matched', 'liked', 'applied']

export function JobListPage() {
  const [searchParams] = useSearchParams()
  const initialTab = searchParams.get('tab')
  const [tab, setTab] = useState<JobTab>(
    validTabs.includes(initialTab as JobTab) ? (initialTab as JobTab) : 'matched',
  )
  const [sortKey, setSortKey] = useState<SortKey>('top-matched')
  const [search, setSearch] = useState('')
  const [loading, setLoading] = useState(true)
  const { likedIds, toggleLiked, appliedIds, markApplied } =
    useJobInteractions(defaultLikedIds, defaultAppliedIds)
  const { showToast } = useToast()

  useEffect(() => {
    const timer = setTimeout(() => setLoading(false), 600)
    return () => clearTimeout(timer)
  }, [])

  const visibleJobs = useMemo(() => {
    const filtered =
      tab === 'liked'
        ? jobs.filter((j) => likedIds.has(j.id))
        : tab === 'applied'
          ? jobs.filter((j) => appliedIds.has(j.id))
          : jobs

    const query = search.trim().toLowerCase()
    const searched = query
      ? filtered.filter((j) =>
          [j.title, j.company, j.location].some((field) =>
            field.toLowerCase().includes(query),
          ),
        )
      : filtered

    return [...searched].sort((a, b) => {
      if (sortKey === 'most-recent') return a.postedHoursAgo - b.postedHoursAgo
      if (sortKey === 'salary') return b.salaryMin - a.salaryMin
      return b.matchScore - a.matchScore
    })
  }, [tab, likedIds, appliedIds, sortKey, search])

  const handleToggleLike = (jobId: string, jobTitle: string) => {
    const wasLiked = likedIds.has(jobId)
    toggleLiked(jobId)
    showToast(wasLiked ? 'Removed from Liked' : `Saved "${jobTitle}" to Liked`)
  }

  const handleApply = (jobId: string, jobTitle: string) => {
    markApplied(jobId)
    showToast(`Application submitted for "${jobTitle}"`)
  }

  return (
    <div>
      <TabBar
        active={tab}
        onChange={setTab}
        counts={{ liked: likedIds.size, applied: appliedIds.size }}
      />

      <div className="flex flex-col gap-6 p-4 lg:flex-row lg:p-6">
        <div className="min-w-0 flex-1 space-y-4">
          <SearchBar value={search} onChange={setSearch} />
          <SortRow value={sortKey} onChange={setSortKey} />

          {loading ? (
            <>
              <JobCardSkeleton />
              <JobCardSkeleton />
              <JobCardSkeleton />
            </>
          ) : visibleJobs.length === 0 ? (
            <div className="flex h-40 flex-col items-center justify-center gap-1 rounded-card bg-surface text-sm text-muted-2">
              <span>
                {search
                  ? `No jobs match "${search}".`
                  : `No jobs in "${tab}" yet.`}
              </span>
            </div>
          ) : (
            visibleJobs.map((job) => (
              <JobCard
                key={job.id}
                job={job}
                liked={likedIds.has(job.id)}
                applied={appliedIds.has(job.id)}
                onToggleLike={() => handleToggleLike(job.id, job.title)}
                onApply={() => handleApply(job.id, job.title)}
              />
            ))
          )}
        </div>

        <RightRail />
      </div>
    </div>
  )
}
