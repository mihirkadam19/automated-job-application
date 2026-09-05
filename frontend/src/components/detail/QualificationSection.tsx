import { sharedJobDetail } from '../../data/jobDetail'

export function QualificationSection() {
  return (
    <section>
      <h2 className="text-xl font-semibold text-black">Qualification</h2>
      <p className="mt-4 text-sm leading-relaxed text-black/80">
        {sharedJobDetail.qualificationIntro}
      </p>
      <div className="mt-4 flex flex-wrap gap-2">
        {sharedJobDetail.qualificationTags.map((tag) => (
          <span
            key={tag}
            className="rounded-pill bg-[#e8e8e8] px-4 py-2 text-sm text-ink-2"
          >
            {tag}
          </span>
        ))}
      </div>
    </section>
  )
}
