'use client'

import { use, useState } from 'react'
import Link from 'next/link'
import { ArrowLeft, MapPin, Globe, Briefcase, Clock } from 'lucide-react'
import { Badge } from '@/components/ui/badge'
import { Button } from '@/components/ui/button'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from '@/components/ui/select'
import { MatchResult } from '@/components/match/MatchResult'
import { useJob } from '@/lib/hooks/useJobs'
import { useResumes } from '@/lib/hooks/useResumes'
import { useRunMatch } from '@/lib/hooks/useMatch'
import { useCurrentUser } from '@/lib/hooks/useCurrentUser'
import { SKILL_CATEGORIES, CATEGORY_PRIORITY } from '@/lib/constants/skillCategories'
import { ApiClientError } from '@/lib/api/client'
import type { MatchResultDTO } from '@/types/api'

const employmentLabels: Record<string, string> = {
  full_time: 'Full-time',
  part_time: 'Part-time',
  contract: 'Contract',
  freelance: 'Freelance',
  internship: 'Internship',
}

export default function JobDetailPage({ params }: { params: Promise<{ id: string }> }) {
  const { id } = use(params)
  const { data: job, isLoading, error } = useJob(id)
  const { data: user } = useCurrentUser()
  const { data: resumes } = useResumes()
  const runMatch = useRunMatch()

  const [selectedResumeId, setSelectedResumeId] = useState<string>('')
  const [matchResult, setMatchResult] = useState<MatchResultDTO | null>(null)
  const [matchError, setMatchError] = useState('')

  const isCandidate = !user || user.role === 'candidate'

  const handleMatch = async () => {
    if (!selectedResumeId) return
    setMatchError('')
    setMatchResult(null)
    try {
      const result = await runMatch.mutateAsync({ resume_id: selectedResumeId, job_id: id })
      setMatchResult(result)
    } catch (err) {
      setMatchError(
        err instanceof ApiClientError ? err.detail : 'Match failed. Please try again.',
      )
    }
  }

  if (isLoading) {
    return (
      <div className="space-y-4 max-w-3xl">
        <div className="h-8 w-56 rounded-lg shimmer" />
        <div className="h-5 w-36 rounded shimmer" />
        <div className="h-20 rounded-xl shimmer" />
        <div className="h-32 rounded-xl shimmer" />
        <div className="h-24 rounded-xl shimmer" />
      </div>
    )
  }

  if (error || !job) {
    return (
      <div className="flex flex-col items-center justify-center gap-3 py-20 text-center">
        <p className="text-muted-foreground">
          {error instanceof ApiClientError && error.status === 404
            ? 'Job not found.'
            : 'Failed to load job.'}
        </p>
        <Link href="/jobs" className="text-sm underline underline-offset-4">
          Back to jobs
        </Link>
      </div>
    )
  }

  return (
    <div className="space-y-5 max-w-3xl">
      {/* Header */}
      <div className="flex items-center gap-3">
        <Link href="/jobs" className="text-muted-foreground hover:text-foreground transition-colors">
          <ArrowLeft size={17} />
        </Link>
        <div className="flex-1 min-w-0">
          <h1 className="text-xl font-semibold truncate">{job.title}</h1>
          <p className="text-sm text-muted-foreground">{job.company}</p>
        </div>
        <Badge variant="secondary" className="shrink-0 capitalize">
          {employmentLabels[job.employment_type] ?? job.employment_type}
        </Badge>
      </div>

      {/* Meta */}
      <Card>
        <CardContent className="flex flex-wrap gap-4 text-sm text-muted-foreground pt-5">
          <span className="flex items-center gap-1.5">
            <MapPin size={13} />
            {job.location.city}, {job.location.country}
          </span>
          {job.location.remote && (
            <span className="flex items-center gap-1.5">
              <Globe size={13} />
              Remote
            </span>
          )}
          {job.required_experience_months > 0 && (
            <span className="flex items-center gap-1.5">
              <Clock size={13} />
              {job.required_experience_months} months experience
            </span>
          )}
          {job.salary_range && (
            <span className="flex items-center gap-1.5">
              <Briefcase size={13} />
              {job.salary_range.min_salary.toLocaleString()}–{job.salary_range.max_salary.toLocaleString()} {job.salary_range.currency}
            </span>
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
      {job.required_skills.length > 0 && (() => {
        const grouped = job.required_skills.reduce<Record<string, typeof job.required_skills>>((acc, skill) => {
          const cat = skill.category
          return { ...acc, [cat]: [...(acc[cat] ?? []), skill] }
        }, {})
        const sortedCats = Object.keys(grouped).sort(
          (a, b) => (CATEGORY_PRIORITY[a] ?? 99) - (CATEGORY_PRIORITY[b] ?? 99)
        )
        return (
          <Card>
            <CardHeader className="pb-2">
              <CardTitle className="text-sm font-semibold text-muted-foreground uppercase tracking-wider">
                Required Skills{' '}
                <span className="ml-1.5 rounded-full bg-primary/10 text-primary px-1.5 py-0.5 text-xs normal-case font-medium">
                  {job.required_skills.length}
                </span>
              </CardTitle>
            </CardHeader>
            <CardContent className="space-y-3">
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
            </CardContent>
          </Card>
        )
      })()}

      {/* Match section — candidates only */}
      {isCandidate && (
        <Card>
          <CardHeader className="pb-2">
            <CardTitle className="text-sm font-semibold text-muted-foreground uppercase tracking-wider">
              Match this job
            </CardTitle>
          </CardHeader>
          <CardContent className="space-y-4">
            <div className="flex gap-3 items-end">
              <div className="flex-1 space-y-1">
                <p className="text-sm text-muted-foreground">Select a resume to match against this job</p>
                <Select
                  value={selectedResumeId}
                  onValueChange={(v) => v && setSelectedResumeId(v)}
                >
                  <SelectTrigger className="w-full">
                    <SelectValue placeholder="Choose a resume…" />
                  </SelectTrigger>
                  <SelectContent>
                    {resumes?.map((r) => (
                      <SelectItem key={r.resume_id} value={r.resume_id}>
                        {r.contact_info.email || r.resume_id}
                      </SelectItem>
                    ))}
                  </SelectContent>
                </Select>
              </div>
              <Button
                onClick={handleMatch}
                disabled={!selectedResumeId || runMatch.isPending}
              >
                {runMatch.isPending ? 'Matching…' : 'Match'}
              </Button>
            </div>

            {matchError && <p className="text-sm text-destructive">{matchError}</p>}

            {matchResult && <MatchResult result={matchResult} />}
          </CardContent>
        </Card>
      )}
    </div>
  )
}
