'use client'

import { useRouter, usePathname } from 'next/navigation'
import { LogOut, ChevronRight } from 'lucide-react'
import { Button } from '@/components/ui/button'
import { authApi } from '@/lib/api/auth'
import { useCurrentUser } from '@/lib/hooks/useCurrentUser'

const breadcrumbMap: Record<string, string> = {
  '/resumes': 'Resumes',
  '/resumes/new': 'New Resume',
  '/jobs': 'Jobs',
  '/recruiter/jobs': 'My Jobs',
  '/recruiter/jobs/new': 'New Job',
  '/dashboard': 'Dashboard',
}

function getBreadcrumb(pathname: string): { parent?: string; current: string } {
  if (breadcrumbMap[pathname]) {
    return { current: breadcrumbMap[pathname] }
  }
  if (pathname.startsWith('/resumes/') && pathname !== '/resumes/new') {
    return { parent: 'Resumes', current: 'Resume Detail' }
  }
  if (pathname.startsWith('/jobs/')) {
    return { parent: 'Jobs', current: 'Job Detail' }
  }
  if (pathname.startsWith('/recruiter/jobs/') && pathname !== '/recruiter/jobs/new') {
    return { parent: 'My Jobs', current: 'Job Detail' }
  }
  return { current: 'ResumeAI' }
}

export function Topbar() {
  const router = useRouter()
  const pathname = usePathname()
  const { data: user } = useCurrentUser()
  const { parent, current } = getBreadcrumb(pathname)

  const handleLogout = async () => {
    await authApi.logout()
    router.push('/login')
    router.refresh()
  }

  const initials = user?.username?.slice(0, 2).toUpperCase() ?? '?'

  return (
    <header className="flex h-12 items-center justify-between border-b bg-background px-6">
      {/* Breadcrumb */}
      <div className="flex items-center gap-1.5 text-sm text-muted-foreground">
        {parent && (
          <>
            <span>{parent}</span>
            <ChevronRight size={13} className="opacity-50" />
          </>
        )}
        <span className="font-medium text-foreground">{current}</span>
      </div>

      {/* Right side */}
      <div className="flex items-center gap-2">
        <div className="flex size-7 items-center justify-center rounded-full bg-primary/10 text-primary text-xs font-semibold select-none">
          {initials}
        </div>
        <Button
          variant="ghost"
          size="icon-sm"
          onClick={handleLogout}
          className="text-muted-foreground hover:text-foreground"
          title="Sign out"
        >
          <LogOut size={14} />
        </Button>
      </div>
    </header>
  )
}
