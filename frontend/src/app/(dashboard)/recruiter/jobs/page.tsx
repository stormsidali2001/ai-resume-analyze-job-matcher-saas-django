'use client'

import Link from 'next/link'
import { useRouter } from 'next/navigation'
import { useEffect } from 'react'
import { Briefcase, Plus } from 'lucide-react'
import { Badge } from '@/components/ui/badge'
import { buttonVariants } from '@/components/ui/button'
import { PageHeader } from '@/components/layout/PageHeader'
import { cn } from '@/lib/utils'
import { useMyJobs } from '@/lib/hooks/useJobs'
import { useCurrentUser } from '@/lib/hooks/useCurrentUser'
import type { JobDTO, JobStatus } from '@/types/api'

const statusVariant: Record<JobStatus, 'default' | 'secondary' | 'outline'> = {
  draft: 'outline',
  published: 'default',
  closed: 'secondary',
}

const statusDot: Record<JobStatus, string> = {
  draft: 'bg-amber-400',
  published: 'bg-indigo-500',
  closed: 'bg-muted-foreground/40',
}

function JobRow({ job }: { job: JobDTO }) {
  return (
    <Link href={`/recruiter/jobs/${job.job_id}`} className="block group">
      <div className="flex items-center justify-between rounded-lg border bg-card px-4 py-3 shadow-sm transition-all group-hover:shadow-md group-hover:border-primary/30">
        <div className="flex items-center gap-3">
          <span className={cn('size-2 rounded-full shrink-0', statusDot[job.status])} />
          <div>
            <p className="font-medium text-sm">{job.title}</p>
            <p className="text-xs text-muted-foreground">
              {job.company} · {job.required_skills.length} skill{job.required_skills.length !== 1 ? 's' : ''}
            </p>
          </div>
        </div>
        <Badge variant={statusVariant[job.status]} className="capitalize">
          {job.status}
        </Badge>
      </div>
    </Link>
  )
}

export default function RecruiterJobsPage() {
  const router = useRouter()
  const { data: user, isLoading: userLoading } = useCurrentUser()
  const { data: jobs, isLoading } = useMyJobs()

  useEffect(() => {
    if (!userLoading && user && user.role !== 'recruiter') {
      router.replace('/jobs')
    }
  }, [user, userLoading, router])

  const draft = jobs?.filter((j) => j.status === 'draft') ?? []
  const published = jobs?.filter((j) => j.status === 'published') ?? []
  const closed = jobs?.filter((j) => j.status === 'closed') ?? []

  if (isLoading || userLoading) {
    return (
      <div className="space-y-6">
        <div className="space-y-4">
          <div className="h-7 w-32 rounded-lg shimmer" />
          <div className="h-px bg-border" />
        </div>
        <div className="space-y-2">
          {Array.from({ length: 4 }).map((_, i) => (
            <div key={i} className="h-16 rounded-lg shimmer" />
          ))}
        </div>
      </div>
    )
  }

  return (
    <div className="space-y-6">
      <PageHeader
        title="My Jobs"
        description="Manage your job postings"
        action={
          <Link href="/recruiter/jobs/new" className={buttonVariants({ size: 'sm' })}>
            <Plus size={14} className="mr-1.5" />
            New job
          </Link>
        }
      />

      {(!jobs || jobs.length === 0) ? (
        <div className="flex flex-col items-center gap-4 py-24 text-center">
          <div className="flex size-16 items-center justify-center rounded-2xl bg-muted">
            <Briefcase size={26} className="text-muted-foreground" />
          </div>
          <div className="space-y-1">
            <p className="font-medium">No job postings yet</p>
            <p className="text-sm text-muted-foreground">Create your first job to start finding candidates</p>
          </div>
          <Link href="/recruiter/jobs/new" className={buttonVariants({ size: 'sm' })}>
            Create a job
          </Link>
        </div>
      ) : (
        <div className="space-y-6">
          {draft.length > 0 && (
            <section className="space-y-2">
              <h2 className="text-xs font-semibold text-muted-foreground uppercase tracking-widest">
                Draft · {draft.length}
              </h2>
              <div className="space-y-2">{draft.map((j) => <JobRow key={j.job_id} job={j} />)}</div>
            </section>
          )}
          {published.length > 0 && (
            <section className="space-y-2">
              <h2 className="text-xs font-semibold text-muted-foreground uppercase tracking-widest">
                Published · {published.length}
              </h2>
              <div className="space-y-2">{published.map((j) => <JobRow key={j.job_id} job={j} />)}</div>
            </section>
          )}
          {closed.length > 0 && (
            <section className="space-y-2">
              <h2 className="text-xs font-semibold text-muted-foreground uppercase tracking-widest">
                Closed · {closed.length}
              </h2>
              <div className="space-y-2">{closed.map((j) => <JobRow key={j.job_id} job={j} />)}</div>
            </section>
          )}
        </div>
      )}
    </div>
  )
}
