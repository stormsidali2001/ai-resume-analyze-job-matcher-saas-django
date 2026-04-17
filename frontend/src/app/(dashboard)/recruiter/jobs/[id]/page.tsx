'use client'

import { use } from 'react'
import Link from 'next/link'
import { ArrowLeft, MapPin, Globe, Clock } from 'lucide-react'
import { Badge } from '@/components/ui/badge'
import { Button } from '@/components/ui/button'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'
import { AddJobSkillForm } from '@/components/job/AddJobSkillForm'
import { useJob, usePublishJob, useCloseJob } from '@/lib/hooks/useJobs'
import { SKILL_CATEGORIES, CATEGORY_PRIORITY } from '@/lib/constants/skillCategories'
import { ApiClientError } from '@/lib/api/client'
import type { JobStatus } from '@/types/api'

const statusVariant: Record<JobStatus, 'default' | 'secondary' | 'outline'> = {
  draft: 'outline',
  published: 'default',
  closed: 'secondary',
}

export default function RecruiterJobDetailPage({ params }: { params: Promise<{ id: string }> }) {
  const { id } = use(params)
  const { data: job, isLoading, error } = useJob(id)
  const publish = usePublishJob(id)
  const close = useCloseJob(id)

  if (isLoading) {
    return (
      <div className="space-y-4 max-w-3xl">
        <div className="h-8 w-56 rounded-lg shimmer" />
        <div className="h-5 w-36 rounded shimmer" />
        <div className="h-20 rounded-xl shimmer" />
        <div className="h-32 rounded-xl shimmer" />
        <div className="h-28 rounded-xl shimmer" />
      </div>
    )
  }

  if (error || !job) {
    return (
      <div className="flex flex-col items-center justify-center gap-3 py-20 text-center">
        <p className="text-muted-foreground">
          {error instanceof ApiClientError && error.status === 404 ? 'Job not found.' : 'Failed to load job.'}
        </p>
        <Link href="/recruiter/jobs" className="text-sm underline underline-offset-4">
          Back to my jobs
        </Link>
      </div>
    )
  }

  const canPublish = job.status === 'draft' && job.required_skills.length > 0
  const canClose = job.status === 'published'

  return (
    <div className="space-y-5 max-w-3xl">
      {/* Header */}
      <div className="flex items-center gap-3">
        <Link href="/recruiter/jobs" className="text-muted-foreground hover:text-foreground transition-colors">
          <ArrowLeft size={17} />
        </Link>
        <div className="flex-1 min-w-0">
          <h1 className="text-xl font-semibold truncate">{job.title}</h1>
          <p className="text-sm text-muted-foreground">{job.company}</p>
        </div>
        <Badge variant={statusVariant[job.status]} className="capitalize shrink-0">
          {job.status}
        </Badge>
      </div>

      {/* Actions */}
      <div className="flex items-center gap-3">
        {canPublish && (
          <Button
            size="sm"
            onClick={() => publish.mutate()}
            disabled={publish.isPending}
          >
            {publish.isPending ? 'Publishing…' : 'Publish'}
          </Button>
        )}
        {!canPublish && job.status === 'draft' && (
          <p className="text-sm text-muted-foreground">
            Add at least one required skill to publish.
          </p>
        )}
        {canClose && (
          <Button
            size="sm"
            variant="outline"
            onClick={() => close.mutate()}
            disabled={close.isPending}
          >
            {close.isPending ? 'Closing…' : 'Close job'}
          </Button>
        )}
      </div>

      {/* Meta */}
      <Card>
        <CardContent className="flex flex-wrap gap-4 text-sm text-muted-foreground pt-5">
          <span className="flex items-center gap-1.5"><MapPin size={13} />{job.location.city}, {job.location.country}</span>
          {job.location.remote && (
            <span className="flex items-center gap-1.5"><Globe size={13} />Remote</span>
          )}
          {job.required_experience_months > 0 && (
            <span className="flex items-center gap-1.5"><Clock size={13} />{job.required_experience_months} months exp.</span>
          )}
          {job.salary_range && (
            <span>{job.salary_range.min_salary.toLocaleString()}–{job.salary_range.max_salary.toLocaleString()} {job.salary_range.currency}</span>
          )}
        </CardContent>
      </Card>

      {/* Description */}
      <Card>
        <CardHeader className="pb-2">
          <CardTitle className="text-sm font-semibold text-muted-foreground uppercase tracking-wider">
            Description
          </CardTitle>
        </CardHeader>
        <CardContent>
          <p className="text-sm text-muted-foreground whitespace-pre-wrap leading-relaxed">
            {job.description_preview}
          </p>
        </CardContent>
      </Card>

      {/* Required Skills */}
      <Card>
        <CardHeader className="pb-2">
          <CardTitle className="text-sm font-semibold text-muted-foreground uppercase tracking-wider">
            Required Skills{job.required_skills.length > 0 && (
              <span className="ml-1.5 rounded-full bg-primary/10 text-primary px-1.5 py-0.5 text-xs normal-case font-medium">
                {job.required_skills.length}
              </span>
            )}
          </CardTitle>
        </CardHeader>
        <CardContent className="space-y-4">
          {job.required_skills.length === 0 ? (
            <p className="text-sm text-muted-foreground">No skills yet. Add at least one to publish.</p>
          ) : (() => {
            const grouped = job.required_skills.reduce<Record<string, typeof job.required_skills>>((acc, skill) => {
              const cat = skill.category
              return { ...acc, [cat]: [...(acc[cat] ?? []), skill] }
            }, {})
            const sortedCats = Object.keys(grouped).sort(
              (a, b) => (CATEGORY_PRIORITY[a] ?? 99) - (CATEGORY_PRIORITY[b] ?? 99)
            )
            return (
              <div className="space-y-3">
                {sortedCats.map((cat) => {
                  const label = SKILL_CATEGORIES.find((c) => c.value === cat)?.label ?? cat
                  return (
                    <div key={cat} className="space-y-1.5">
                      <p className="text-xs font-semibold text-muted-foreground uppercase tracking-wider">{label}</p>
                      <div className="flex flex-wrap gap-1.5">
                        {grouped[cat].map((skill, i) => (
                          <Badge key={i} variant="secondary">
                            {skill.name}
                            <span className="ml-1 text-muted-foreground text-xs">· {skill.proficiency_level}</span>
                          </Badge>
                        ))}
                      </div>
                    </div>
                  )
                })}
              </div>
            )
          })()}
          {job.status !== 'closed' && <AddJobSkillForm jobId={id} />}
        </CardContent>
      </Card>
    </div>
  )
}
