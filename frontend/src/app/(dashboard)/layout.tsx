import { Sidebar } from '@/components/layout/Sidebar'
import { Topbar } from '@/components/layout/Topbar'
import { RouteGuard } from '@/components/layout/RouteGuard'

export default function DashboardLayout({ children }: { children: React.ReactNode }) {
  return (
    <RouteGuard>
      <div className="flex h-screen overflow-hidden">
        <Sidebar />
        <div className="flex flex-1 flex-col overflow-hidden">
          <Topbar />
          <main className="flex-1 overflow-y-auto bg-background px-8 py-6">{children}</main>
        </div>
      </div>
    </RouteGuard>
  )
}
