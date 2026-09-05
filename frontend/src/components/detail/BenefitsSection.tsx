import { sharedJobDetail } from '../../data/jobDetail'

export function BenefitsSection() {
  return (
    <section>
      <h2 className="text-xl font-semibold text-black">Benefits</h2>
      <p className="mt-4 text-base font-medium text-black">
        {sharedJobDetail.benefitsIntro}
      </p>
      <ul className="mt-2.5 flex flex-col gap-2.5">
        {sharedJobDetail.benefits.map((item) => (
          <li key={item} className="text-base leading-relaxed text-black">
            {item}
          </li>
        ))}
      </ul>
    </section>
  )
}
