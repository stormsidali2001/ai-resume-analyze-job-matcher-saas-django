'use client'

import { useEffect } from 'react'
import { useRouter } from 'next/navigation'
import { useCurrentUser } from '@/lib/hooks/useCurrentUser'

export default function DashboardPage() {
  const router = useRouter()
  const { data: user, isLoading } = useCurrentUser()

  useEffect(() => {
    if (isLoading) return
    if (user?.role === 'recruiter') {
      router.replace('/recruiter/jobs')
    } else {
      router.replace('/resumes')
    }
  }, [user, isLoading, router])

  return null
}
