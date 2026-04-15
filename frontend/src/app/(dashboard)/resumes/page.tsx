'use client'

import Link from 'next/link'
import { Plus } from 'lucide-react'
import { buttonVariants } from '@/components/ui/button'
import { ResumeCard } from '@/components/resume/ResumeCard'
import { useResumes } from '@/lib/hooks/useResumes'
import { cn } from '@/lib/utils'

export default function ResumesPage() {
  const { data: resumes, isLoading, isError } = useResumes()

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <h1 className="text-2xl font-semibold">My Resumes</h1>
        <Link href="/resumes/new" className={cn(buttonVariants({ size: 'sm' }))}>
          <Plus size={15} className="mr-1" />
          New resume
        </Link>
      </div>

      {isLoading && (
        <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-3">
          {Array.from({ length: 3 }).map((_, i) => (
            <div key={i} className="h-36 rounded-lg bg-muted animate-pulse" />
          ))}
        </div>
      )}

      {isError && (
        <p className="text-sm text-destructive">Failed to load resumes. Please refresh the page.</p>
      )}

      {!isLoading && !isError && resumes?.length === 0 && (
        <div className="flex flex-col items-center justify-center gap-3 py-20 text-center">
          <p className="text-muted-foreground">No resumes yet.</p>
          <Link href="/resumes/new" className={cn(buttonVariants({ variant: 'outline' }))}>
            Create your first resume
          </Link>
        </div>
      )}

      {resumes && resumes.length > 0 && (
        <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-3">
          {resumes.map((resume) => (
            <ResumeCard key={resume.resume_id} resume={resume} />
          ))}
        </div>
      )}
    </div>
  )
}
