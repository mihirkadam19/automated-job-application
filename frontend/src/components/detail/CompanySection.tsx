import socialX from '../../assets/icons/social-1.svg'
import socialLinkedIn from '../../assets/icons/social-2.svg'
import { sharedJobDetail } from '../../data/jobDetail'

export function CompanySection({ company }: { company: string }) {
  const { founded, location, employees, description } = sharedJobDetail.company

  return (
    <section>
      <h2 className="text-xl font-semibold text-black">Company</h2>
      <div className="mt-5 flex gap-4">
        <span className="size-[103px] shrink-0 rounded-card bg-bg" />
        <div className="flex-1">
          <h3 className="text-xl font-semibold text-black">{company}</h3>
          <div className="mt-2 flex flex-wrap items-center gap-2 text-sm text-muted-2">
            <span>{founded}</span>
            <span className="size-1.5 rounded-full bg-accent" />
            <span>{location}</span>
            <span className="size-1.5 rounded-full bg-accent" />
            <span>{employees}</span>
            <span className="size-1.5 rounded-full bg-accent" />
            <span>Website</span>
          </div>
          <div className="mt-3 flex gap-2">
            <img src={socialX} alt="X (Twitter)" className="size-6" />
            <img src={socialLinkedIn} alt="LinkedIn" className="size-6" />
          </div>
        </div>
      </div>
      <p className="mt-5 text-sm leading-relaxed text-black/80">
        {description}
      </p>
    </section>
  )
}
