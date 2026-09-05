import aiGenerate from '../../assets/icons/ai-generate.svg'
import generateB from '../../assets/icons/generate-b.svg'
import searchIcon from '../../assets/icons/search-window-white.svg'
import railBlob from '../../assets/images/rail-blob.png'

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

export function RightRail() {
  return (
    <aside className="w-full lg:w-[290px] lg:shrink-0">
      <div className="overflow-hidden rounded-2xl bg-surface p-6 lg:sticky lg:top-6">
        <img
          src={railBlob}
          alt=""
          aria-hidden
          className="pointer-events-none absolute -right-24 -top-16 w-[395px] max-w-none"
        />
        <img
          src={generateB}
          alt=""
          aria-hidden
          className="pointer-events-none absolute right-10 top-[190px] size-[22px]"
        />

        <div className="relative">
          <img src={aiGenerate} alt="" className="size-[30px]" />

          <h3 className="mt-3 text-base font-semibold text-ink">
            Ace Your Interviews with AI-Powered Mock Sessions!
          </h3>
          <p className="mt-3 text-sm leading-relaxed text-ink-2/80">
            Struggling with interview nerves or unsure how to prepare? Let our
            cutting-edge AI mock interviews help you shine!
          </p>

          <hr className="my-5 border-t border-black/5" />

          <h4 className="text-sm font-semibold text-ink">
            Why Choose Our AI Mock Interviews?
          </h4>

          <ul className="mt-4 flex flex-col gap-4">
            {features.map((f) => (
              <li key={f.title}>
                <p className="text-sm font-semibold text-ink-2">{f.title}</p>
                <p className="mt-1 text-sm leading-relaxed text-ink-2/80">
                  {f.body}
                </p>
              </li>
            ))}
          </ul>

          <button
            type="button"
            className="mt-6 flex w-full items-center justify-center gap-2 rounded-pill bg-ink py-3 text-sm font-medium text-white"
          >
            <img src={searchIcon} alt="" className="size-4" />
            Mock Interview
          </button>
        </div>
      </div>
    </aside>
  )
}
