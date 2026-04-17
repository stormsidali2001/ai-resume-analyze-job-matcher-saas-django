'use client'

import { Briefcase } from 'lucide-react'
import { PageHeader } from '@/components/layout/PageHeader'
import { JobCard } from '@/components/job/JobCard'
import { useJobs } from '@/lib/hooks/useJobs'

function SkeletonGrid() {
  return (
    <div className="grid grid-cols-1 gap-4 sm:grid-cols-2 lg:grid-cols-3">
      {Array.from({ length: 6 }).map((_, i) => (
        <div key={i} className="h-44 rounded-xl shimmer" />
      ))}
    </div>
  )
}

export default function JobsPage() {
  const { data: jobs, isLoading } = useJobs()

  return (
    <div className="space-y-6">
      <PageHeader
        title="Jobs"
        description="Browse open positions and match your resume"
      />

      {isLoading && <SkeletonGrid />}

      {!isLoading && (!jobs || jobs.length === 0) && (
        <div className="flex flex-col items-center gap-4 py-24 text-center">
          <div className="flex size-16 items-center justify-center rounded-2xl bg-muted">
            <Briefcase size={26} className="text-muted-foreground" />
          </div>
          <div className="space-y-1">
            <p className="font-medium">No jobs available yet</p>
            <p className="text-sm text-muted-foreground">Check back soon for new postings</p>
          </div>
        </div>
      )}

      {!isLoading && jobs && jobs.length > 0 && (
        <div className="grid grid-cols-1 gap-4 sm:grid-cols-2 lg:grid-cols-3">
          {jobs.map((job) => (
            <JobCard key={job.job_id} job={job} />
          ))}
        </div>
      )}
    </div>
  )
}
