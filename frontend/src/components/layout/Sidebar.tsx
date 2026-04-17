'use client'

import Link from 'next/link'
import { usePathname } from 'next/navigation'
import { FileText, Briefcase } from 'lucide-react'
import { cn } from '@/lib/utils'
import { useCurrentUser } from '@/lib/hooks/useCurrentUser'

const candidateNav = [
  { href: '/resumes', label: 'Resumes', icon: FileText },
  { href: '/jobs', label: 'Jobs', icon: Briefcase },
]

const recruiterNav = [
  { href: '/recruiter/jobs', label: 'My Jobs', icon: Briefcase },
]

function UserFooter() {
  const { data: user } = useCurrentUser()
  if (!user) return null

  const initials = user.username.slice(0, 2).toUpperCase()
  const isRecruiter = user.role === 'recruiter'

  return (
    <div className="mt-auto border-t border-sidebar-border pt-3 px-2">
      <div className="flex items-center gap-2.5 rounded-md px-2 py-2">
        <div className="flex size-7 shrink-0 items-center justify-center rounded-full bg-sidebar-primary text-sidebar-primary-foreground text-xs font-semibold">
          {initials}
        </div>
        <div className="flex-1 min-w-0">
          <p className="text-xs font-medium text-sidebar-foreground truncate">{user.username}</p>
          <p className={cn(
            'text-xs truncate capitalize',
            isRecruiter ? 'text-amber-400' : 'text-sidebar-primary',
          )}>
            {user.role}
          </p>
        </div>
      </div>
    </div>
  )
}

export function Sidebar() {
  const pathname = usePathname()
  const { data: user } = useCurrentUser()

  const navItems = user?.role === 'recruiter' ? recruiterNav : candidateNav

  return (
    <aside className="hidden md:flex w-56 flex-col bg-sidebar px-3 py-4">
      {/* Logo */}
      <div className="mb-6 flex items-center gap-2 px-2">
        <div className="flex size-7 items-center justify-center rounded-lg bg-sidebar-primary text-sidebar-primary-foreground text-sm font-bold">
          R
        </div>
        <span className="text-sm font-semibold tracking-tight text-sidebar-foreground">
          ResumeAI
        </span>
      </div>

      {/* Nav */}
      <nav className="space-y-0.5">
        {navItems.map(({ href, label, icon: Icon }) => {
          const isActive = pathname.startsWith(href)
          return (
            <Link
              key={href}
              href={href}
              className={cn(
                'relative flex items-center gap-2.5 rounded-md px-3 py-2 text-sm font-medium transition-colors',
                isActive
                  ? 'bg-sidebar-primary text-sidebar-primary-foreground'
                  : 'text-sidebar-foreground/60 hover:bg-sidebar-accent hover:text-sidebar-accent-foreground',
              )}
            >
              <Icon size={15} className="shrink-0" />
              {label}
            </Link>
          )
        })}
      </nav>

      <UserFooter />
    </aside>
  )
}
