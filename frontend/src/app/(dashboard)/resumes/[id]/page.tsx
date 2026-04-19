'use client'

import { use, useState } from 'react'
import { useRouter } from 'next/navigation'
import Link from 'next/link'
import { ArrowLeft, Mail, Phone, MapPin, Sparkles, Loader2, Archive, Pencil } from 'lucide-react'
import { Badge } from '@/components/ui/badge'
import { Button } from '@/components/ui/button'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'
import { Separator } from '@/components/ui/separator'
import { Textarea } from '@/components/ui/textarea'
import { SkillBadge } from '@/components/resume/SkillBadge'
import { AddSkillForm } from '@/components/resume/AddSkillForm'
import { useResume, useAnalyzeResume, useArchiveResume, useUpdateResume } from '@/lib/hooks/useResumes'
import { useResumeStatusSocket } from '@/lib/hooks/useResumeStatusSocket'
import { SKILL_CATEGORIES, CATEGORY_PRIORITY } from '@/lib/constants/skillCategories'
import { formatMonths } from '@/lib/utils'
import { ApiClientError } from '@/lib/api/client'

const statusVariant: Record<string, 'default' | 'secondary' | 'outline'> = {
  draft: 'outline',
  active: 'default',
  archived: 'secondary',
}

export default function ResumeDetailPage({ params }: { params: Promise<{ id: string }> }) {
  const { id } = use(params)
  const router = useRouter()

  const { data: resume, isLoading, error } = useResume(id)
  const { mutate: analyze, isPending: isAnalyzing, error: analyzeError } = useAnalyzeResume(id)
  const { mutate: archive, isPending: isArchiving } = useArchiveResume(id)
  const updateResume = useUpdateResume(id)

  // Open a WebSocket to receive real-time analysis_status updates from the
  // Celery worker. The hook self-closes once a terminal state arrives.
  const isAnalysisPending =
    resume?.analysis_status === 'pending' || resume?.analysis_status === 'processing'
  useResumeStatusSocket(id, !!resume && isAnalysisPending)

  const [confirmArchive, setConfirmArchive] = useState(false)
  const [editing, setEditing] = useState(false)
  const [draftText, setDraftText] = useState('')

  if (isLoading) {
    return (
      <div className="space-y-4 max-w-3xl">
        <div className="h-8 w-56 rounded-lg shimmer" />
        <div className="h-40 rounded-xl shimmer" />
        <div className="h-32 rounded-xl shimmer" />
      </div>
    )
  }

  if (error) {
    const status = error instanceof ApiClientError ? error.status : 0
    return (
      <div className="flex flex-col items-center justify-center gap-3 py-20 text-center">
        <p className="text-muted-foreground">
          {status === 404
            ? 'Resume not found.'
            : status === 403
              ? "You don't have access to this resume."
              : 'Failed to load resume.'}
        </p>
        <Link href="/resumes" className="text-sm underline underline-offset-4">
          Back to resumes
        </Link>
      </div>
    )
  }

  if (!resume) return null

  const isArchived = resume.status === 'archived'

  const handleArchiveConfirm = () => {
    archive(undefined, {
      onSuccess: () => router.push('/resumes'),
    })
  }

  const handleSaveEdit = () => {
    updateResume.mutate(
      { new_raw_text: draftText },
      { onSuccess: () => setEditing(false) },
    )
  }

  return (
    <div className="space-y-5 max-w-3xl">
      {/* Header */}
      <div className="flex items-center gap-3">
        <Link href="/resumes" className="text-muted-foreground hover:text-foreground transition-colors">
          <ArrowLeft size={17} />
        </Link>
        <h1 className="text-xl font-semibold flex-1 truncate">
          {resume.contact_info.email || 'Resume'}
        </h1>
        <Badge variant={statusVariant[resume.status] ?? 'outline'} className="capitalize shrink-0">
          {resume.status}
        </Badge>

        {/* Re-analyze */}
        <Button
          size="sm"
          variant="outline"
          onClick={() => analyze()}
          disabled={isAnalyzing || isArchived}
        >
          {isAnalyzing ? (
            <><Loader2 size={13} className="mr-1.5 animate-spin" />Analyzing…</>
          ) : (
            <><Sparkles size={13} className="mr-1.5" />Re-analyze</>
          )}
        </Button>

        {/* Archive (two-step) */}
        {!isArchived && (
          confirmArchive ? (
            <div className="flex items-center gap-1.5 shrink-0">
              <Button
                size="sm"
                variant="destructive"
                onClick={handleArchiveConfirm}
                disabled={isArchiving}
              >
                {isArchiving ? <Loader2 size={13} className="animate-spin" /> : 'Confirm?'}
              </Button>
              <Button
                size="sm"
                variant="ghost"
                onClick={() => setConfirmArchive(false)}
                disabled={isArchiving}
              >
                Cancel
              </Button>
            </div>
          ) : (
            <Button
              size="sm"
              variant="outline"
              onClick={() => setConfirmArchive(true)}
              className="shrink-0"
            >
              <Archive size={13} className="mr-1.5" />
              Archive
            </Button>
          )
        )}
      </div>

      {analyzeError && (
        <p className="text-sm text-destructive">
          {analyzeError instanceof ApiClientError ? analyzeError.detail : 'Analysis failed. Please try again.'}
        </p>
      )}

      {/* AI analysis status banner */}
      {(resume.analysis_status === 'pending' || resume.analysis_status === 'processing') && (
        <div className="flex items-center gap-2 rounded-lg border border-indigo-200 bg-indigo-50 px-4 py-2.5 text-sm text-indigo-700 dark:border-indigo-800 dark:bg-indigo-950/40 dark:text-indigo-300">
          <Loader2 size={14} className="animate-spin shrink-0" />
          AI analysis in progress — skills and experience will appear shortly
        </div>
      )}
      {resume.analysis_status === 'failed' && (
        <div className="rounded-lg border border-destructive/30 bg-destructive/10 px-4 py-2.5 text-sm text-destructive">
          AI analysis failed. Click <strong>Re-analyze</strong> to try again.
        </div>
      )}

      {/* Contact info */}
      <Card>
        <CardHeader className="pb-2">
          <CardTitle className="text-sm font-semibold text-muted-foreground uppercase tracking-wider">
            Contact
          </CardTitle>
        </CardHeader>
        <CardContent className="flex flex-wrap gap-4 text-sm">
          {resume.contact_info.email && (
            <span className="flex items-center gap-1.5 text-muted-foreground">
              <Mail size={13} />
              {resume.contact_info.email}
            </span>
          )}
          {resume.contact_info.phone && (
            <span className="flex items-center gap-1.5 text-muted-foreground">
              <Phone size={13} />
              {resume.contact_info.phone}
            </span>
          )}
          {resume.contact_info.location && (
            <span className="flex items-center gap-1.5 text-muted-foreground">
              <MapPin size={13} />
              {resume.contact_info.location}
            </span>
          )}
          {resume.total_experience_months > 0 && (
            <span className="font-semibold text-foreground">
              {formatMonths(resume.total_experience_months)} exp.
            </span>
          )}
        </CardContent>
      </Card>

      {/* Skills */}
      <Card>
        <CardHeader className="pb-2">
          <CardTitle className="text-sm font-semibold text-muted-foreground uppercase tracking-wider">
            Skills {resume.skills.length > 0 && (
              <span className="ml-1.5 rounded-full bg-primary/10 text-primary px-1.5 py-0.5 text-xs normal-case font-medium">
                {resume.skills.length}
              </span>
            )}
          </CardTitle>
        </CardHeader>
        <CardContent className="space-y-4">
          {resume.skills.length === 0 ? (
            <p className="text-sm text-muted-foreground">
              No skills yet. Re-analyze to extract them automatically, or add one below.
            </p>
          ) : (() => {
            const grouped = resume.skills.reduce<Record<string, typeof resume.skills>>((acc, skill) => {
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
                        {grouped[cat].map((skill, i) => <SkillBadge key={i} skill={skill} />)}
                      </div>
                    </div>
                  )
                })}
              </div>
            )
          })()}
          <AddSkillForm resumeId={id} />
        </CardContent>
      </Card>

      {/* Experience */}
      {resume.experiences.length > 0 && (
        <Card>
          <CardHeader className="pb-2">
            <CardTitle className="text-sm font-semibold text-muted-foreground uppercase tracking-wider">
              Experience
            </CardTitle>
          </CardHeader>
          <CardContent className="space-y-4">
            {resume.experiences.map((exp, i) => (
              <div key={i}>
                {i > 0 && <Separator className="mb-4" />}
                <div className="flex justify-between items-start">
                  <div>
                    <p className="font-semibold text-sm">{exp.role}</p>
                    <p className="text-sm text-muted-foreground">{exp.company}</p>
                  </div>
                  <span className="text-xs text-muted-foreground shrink-0 bg-muted rounded px-1.5 py-0.5">
                    {formatMonths(exp.duration_months)}
                  </span>
                </div>
              </div>
            ))}
          </CardContent>
        </Card>
      )}

      {/* Education */}
      {resume.education.length > 0 && (
        <Card>
          <CardHeader className="pb-2">
            <CardTitle className="text-sm font-semibold text-muted-foreground uppercase tracking-wider">
              Education
            </CardTitle>
          </CardHeader>
          <CardContent className="space-y-3">
            {resume.education.map((edu, i) => (
              <div key={i} className="flex justify-between items-start text-sm">
                <div>
                  <p className="font-semibold">{edu.degree}</p>
                  <p className="text-muted-foreground">{edu.institution}</p>
                </div>
                <span className="text-muted-foreground shrink-0 text-xs">{edu.graduation_year}</span>
              </div>
            ))}
          </CardContent>
        </Card>
      )}

      {/* Raw text preview / inline editor */}
      <Card>
        <CardHeader className="pb-2">
          <div className="flex items-center justify-between">
            <CardTitle className="text-sm font-semibold text-muted-foreground uppercase tracking-wider">
              Raw text preview
            </CardTitle>
            {!isArchived && !editing && (
              <Button
                variant="ghost"
                size="sm"
                className="h-7 px-2 text-xs"
                onClick={() => {
                  setDraftText(resume.raw_text_preview)
                  setEditing(true)
                }}
              >
                <Pencil size={11} className="mr-1" />
                Edit
              </Button>
            )}
          </div>
        </CardHeader>
        <CardContent className="space-y-3">
          {editing ? (
            <>
              <p className="text-xs text-amber-600 dark:text-amber-400 bg-amber-50 dark:bg-amber-950/40 border border-amber-200 dark:border-amber-800 rounded-lg px-3 py-2">
                Saving will clear all extracted skills. Click Re-analyze afterwards to re-extract them.
              </p>
              <Textarea
                value={draftText}
                onChange={(e) => setDraftText(e.target.value)}
                rows={12}
                className="font-mono text-xs resize-y"
              />
              <div className="flex gap-2">
                <Button
                  size="sm"
                  onClick={handleSaveEdit}
                  disabled={updateResume.isPending || !draftText.trim()}
                >
                  {updateResume.isPending ? (
                    <><Loader2 size={13} className="mr-1.5 animate-spin" />Saving…</>
                  ) : 'Save'}
                </Button>
                <Button
                  size="sm"
                  variant="outline"
                  onClick={() => setEditing(false)}
                  disabled={updateResume.isPending}
                >
                  Cancel
                </Button>
              </div>
              {updateResume.error && (
                <p className="text-sm text-destructive">
                  {updateResume.error instanceof ApiClientError
                    ? updateResume.error.detail
                    : 'Failed to save. Please try again.'}
                </p>
              )}
            </>
          ) : (
            <p className="text-sm text-muted-foreground whitespace-pre-wrap leading-relaxed font-mono text-xs">
              {resume.raw_text_preview}
            </p>
          )}
        </CardContent>
      </Card>
    </div>
  )
}
