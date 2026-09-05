import { Outlet } from 'react-router-dom'
import { UpgradeModal } from '../ui/UpgradeModal'
import { Sidebar } from './Sidebar'

export function AppLayout() {
  return (
    <div className="flex min-h-svh flex-col bg-bg lg:flex-row">
      <Sidebar />
      <main className="min-w-0 flex-1">
        <Outlet />
      </main>
      <UpgradeModal />
    </div>
  )
}
