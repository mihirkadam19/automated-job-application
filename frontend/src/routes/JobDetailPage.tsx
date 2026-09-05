import { Link, useNavigate, useParams } from 'react-router-dom'
import { BenefitsSection } from '../components/detail/BenefitsSection'
import { BulletSection } from '../components/detail/BulletSection'
import { CompanySection } from '../components/detail/CompanySection'
import { DetailHeader } from '../components/detail/DetailHeader'
import { DetailHero } from '../components/detail/DetailHero'
import { DetailTagRow } from '../components/detail/DetailTagRow'
import { FitAnalysisPanel } from '../components/detail/FitAnalysisPanel'
import { InterviewPromo } from '../components/detail/InterviewPromo'
import { QualificationSection } from '../components/detail/QualificationSection'
import { TabBar, type JobTab } from '../components/jobs/TabBar'
import { defaultAppliedIds, defaultLikedIds, jobs } from '../data/jobs'
import { sharedJobDetail } from '../data/jobDetail'
import { useJobInteractions } from '../hooks/useJobInteractions'

export function JobDetailPage() {
  const { jobId } = useParams()
  const navigate = useNavigate()
  const job = jobs.find((j) => j.id === jobId)
  const { appliedIds, markApplied, likedIds } = useJobInteractions(
    defaultLikedIds,
    defaultAppliedIds,
  )

  if (!job) {
    return (
      <div className="p-6">
        <p className="text-sm text-muted-2">Job not found.</p>
        <Link to="/" className="text-sm font-medium text-accent">
          ← Back to jobs
        </Link>
      </div>
    )
  }

  const handleTabChange = (tab: JobTab) => {
    navigate(`/?tab=${tab}`)
  }

  return (
    <div>
      <TabBar
        active="matched"
        onChange={handleTabChange}
        counts={{ liked: likedIds.size, applied: appliedIds.size }}
      />

      <div className="flex gap-6 p-6">
        <div className="min-w-0 flex-1 space-y-4">
          <DetailHeader
            applicants={job.applicants}
            applied={appliedIds.has(job.id)}
            onApply={() => markApplied(job.id)}
          />

          <div className="rounded-card bg-surface p-8">
            <div className="flex flex-col gap-6">
              <DetailHero job={job} />
              <DetailTagRow
                levelTag={job.levelTag}
                workMode={job.workMode}
                experienceTag={job.experienceTag}
                salaryRange={job.salaryRange}
                seniority={job.seniority}
              />
              <p className="text-sm leading-relaxed text-black/80">
                {sharedJobDetail.jobDescription}
              </p>

              <InterviewPromo />

              <QualificationSection />
              <BulletSection title="Required" items={sharedJobDetail.required} />
              <BulletSection
                title="Preferred"
                items={sharedJobDetail.preferred}
              />
              <BulletSection
                title="Responsibilities"
                items={sharedJobDetail.responsibilities}
              />
              <BenefitsSection />
              <CompanySection company={job.company} />
            </div>
          </div>
        </div>

        <FitAnalysisPanel />
      </div>
    </div>
  )
}
