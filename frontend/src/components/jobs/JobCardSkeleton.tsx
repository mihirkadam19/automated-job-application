export function JobCardSkeleton() {
  return (
    <div className="animate-pulse rounded-card bg-surface px-[26px] py-4">
      <div className="flex items-start gap-5">
        <div className="size-[108px] shrink-0 rounded-full bg-bg" />

        <div className="min-w-0 flex-1">
          <div className="h-6 w-2/3 rounded bg-bg" />
          <div className="mt-3 h-4 w-1/3 rounded bg-bg" />
          <div className="mt-2 h-4 w-1/2 rounded bg-bg" />
        </div>
      </div>

      <div className="mt-6 flex flex-wrap gap-2">
        {[83, 94, 116, 91, 129].map((w, i) => (
          <div key={i} className="h-[30px] rounded-pill bg-bg" style={{ width: w }} />
        ))}
      </div>

      <div className="mt-4.5 flex items-center justify-between gap-3">
        <div className="h-8 w-40 rounded-pill bg-bg" />
        <div className="flex gap-3">
          <div className="h-[43px] w-[85px] rounded-pill bg-bg" />
          <div className="h-[43px] w-[162px] rounded-pill bg-bg" />
        </div>
      </div>
    </div>
  )
}
