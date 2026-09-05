import aiGenerate from '../../assets/icons/ai-generate.svg'
import searchWindowWhite from '../../assets/icons/search-window-white.svg'
import { Button } from '../ui/Button'

const features = [
  {
    title: 'Job-Specific Simulations:',
    body: 'Practice with questions tailored to your target role, ensuring relevance and preparation.',
  },
  {
    title: 'Actionable Feedback',
    body: 'Get detailed analysis of your responses and practical, step-by-step improvement suggestions.',
  },
  {
    title: 'Boost Success Rates:',
    body: 'Perfect your interview skills and increase your chances of landing the job you want.',
  },
]

export function InterviewPromo() {
  return (
    <div className="rounded-[24px] bg-lime p-8">
      <div className="flex items-start gap-6">
        <span className="flex size-12 shrink-0 items-center justify-center">
          <img src={aiGenerate} alt="" className="size-full" />
        </span>
        <div>
          <h3 className="text-lg font-semibold text-black">
            Maximize your interview success
          </h3>
          <p className="mt-2.5 text-sm leading-relaxed text-black/80">
            Our platform simulates real interview scenarios, helping you
            refine your responses and boost your confidence.
          </p>
        </div>
      </div>

      <div className="mt-6 grid grid-cols-1 gap-6 sm:grid-cols-3">
        {features.map((f) => (
          <div key={f.title}>
            <p className="text-base font-semibold text-ink-2">{f.title}</p>
            <p className="mt-2 text-sm leading-relaxed text-black/80">
              {f.body}
            </p>
          </div>
        ))}
      </div>

      <div className="mt-6 flex justify-end">
        <Button variant="dark" leftIcon={searchWindowWhite}>
          Start Interview
        </Button>
      </div>
    </div>
  )
}
