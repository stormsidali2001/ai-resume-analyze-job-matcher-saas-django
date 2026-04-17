'use client'

import { useEffect } from 'react'
import { useRouter, usePathname } from 'next/navigation'
import { useCurrentUser } from '@/lib/hooks/useCurrentUser'

/**
 * Client-side role guard that complements the middleware cookie check.
 * Middleware can only see the access_token cookie — it can't read the role.
 * This component redirects users who land on a route their role doesn't own.
 */
export function RouteGuard({ children }: { children: React.ReactNode }) {
  const router = useRouter()
  const pathname = usePathname()
  const { data: user, isLoading } = useCurrentUser()

  const isRecruiterPath = pathname.startsWith('/recruiter')

  useEffect(() => {
    if (isLoading || !user) return

    if (user.role === 'recruiter' && !isRecruiterPath) {
      router.replace('/recruiter/jobs')
    } else if (user.role === 'candidate' && isRecruiterPath) {
      router.replace('/resumes')
    }
  }, [user, isLoading, isRecruiterPath, router])

  // Suppress rendering until we know the user isn't on the wrong route
  if (!isLoading && user) {
    if (user.role === 'recruiter' && !isRecruiterPath) return null
    if (user.role === 'candidate' && isRecruiterPath) return null
  }

  return <>{children}</>
}
