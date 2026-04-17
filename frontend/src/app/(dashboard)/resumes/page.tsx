'use client'

import Link from 'next/link'
import { FileText, Plus } from 'lucide-react'
import { buttonVariants } from '@/components/ui/button'
import { PageHeader } from '@/components/layout/PageHeader'
import { ResumeCard } from '@/components/resume/ResumeCard'
import { useResumes } from '@/lib/hooks/useResumes'
import { cn } from '@/lib/utils'

function SkeletonGrid() {
  return (
    <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-3">
      {Array.from({ length: 3 }).map((_, i) => (
        <div key={i} className="h-36 rounded-xl shimmer" />
      ))}
    </div>
  )
}

export default function ResumesPage() {
  const { data: resumes, isLoading, isError } = useResumes()

  return (
    <div className="space-y-6">
      <PageHeader
        title="My Resumes"
        description="Manage and analyze your resumes"
        action={
          <Link href="/resumes/new" className={cn(buttonVariants({ size: 'sm' }))}>
            <Plus size={14} className="mr-1.5" />
            New resume
          </Link>
        }
      />

      {isLoading && <SkeletonGrid />}

      {isError && (
        <p className="text-sm text-destructive">Failed to load resumes. Please refresh the page.</p>
      )}

      {!isLoading && !isError && resumes?.length === 0 && (
        <div className="flex flex-col items-center gap-4 py-24 text-center">
          <div className="flex size-16 items-center justify-center rounded-2xl bg-muted">
            <FileText size={26} className="text-muted-foreground" />
          </div>
          <div className="space-y-1">
            <p className="font-medium">No resumes yet</p>
            <p className="text-sm text-muted-foreground">Upload a PDF or paste your resume to get started</p>
          </div>
          <Link href="/resumes/new" className={cn(buttonVariants({ size: 'sm' }))}>
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
