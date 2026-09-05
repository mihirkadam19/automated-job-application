import { Link } from 'react-router-dom'

export function JobDetailPage() {
  return (
    <div className="mx-auto flex max-w-[1400px] gap-6 p-4 lg:p-6">
      <div className="min-w-0 flex-1 space-y-4">
        <Link to="/" className="text-sm font-medium text-accent">
          ← Back to jobs
        </Link>
        <div className="flex h-40 items-center justify-center rounded-2xl border border-dashed border-black/10 text-sm text-muted-2">
          Job detail content goes here (Stage 4)
        </div>
      </div>
      <div className="w-[290px] shrink-0">
        <div className="flex h-40 items-center justify-center rounded-2xl border border-dashed border-black/10 text-sm text-muted-2">
          Fit analysis panel (Stage 4)
        </div>
      </div>
    </div>
  )
}
