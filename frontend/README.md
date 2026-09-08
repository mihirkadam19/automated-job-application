# Frontend Assignment

This folder is the solution for the frontend assignment: a job-search UI built with React 19, TypeScript, Vite, React Router 7, and Tailwind CSS v4. All job data is mocked locally under `src/data/` — there is no backend call from this app.

## What it does

- **Job list** (`/`) with three tabs — Matched, Liked, Applied — plus free-text search over title/company/location and sorting by match score, recency, or salary. Cards show a match ring, tags, and inline Like / Apply actions, with a skeleton state on first load.
- **Job detail** (`/jobs/:jobId`) with hero, qualifications, bullet sections, benefits, and company info.
- **Fit analysis panel** — a per-job "why is this a good fit" breakdown that is blurred and gated behind a subscription. "Upgrade to check" opens an upgrade modal; upgrading (mocked, in-memory) reveals it.
- **Liked / applied state** is held client-side via `useJobInteractions`; toasts confirm each action.

## Project structure

```
src/
  App.tsx                  router + context providers
  routes/                  JobListPage, JobDetailPage
  components/
    layout/                AppLayout, Sidebar, RightRail
    jobs/                  JobCard, SearchBar, SortRow, TabBar, MatchRing, TagPill
    detail/                DetailHero, QualificationSection, FitAnalysisPanel, ...
    ui/                    Button, UpgradeModal, ToastContainer, MobileFloatingPanel
  context/                 SubscriptionContext, ToastContext
  hooks/                   useJobInteractions
  data/                    jobs.ts, jobDetail.ts  (mock data)
  lib/                     matchColor.ts
```

## How to run

```bash
npm install
npm run dev        # start the dev server (Vite)
npm run build      # type-check and produce a production build
npm run preview    # serve the production build
npm run lint       # oxlint
```
