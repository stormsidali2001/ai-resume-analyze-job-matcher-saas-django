'use client'

import { use } from 'react'
import Link from 'next/link'
import { ArrowLeft, Mail, Phone, MapPin } from 'lucide-react'
import { Badge } from '@/components/ui/badge'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'
import { Separator } from '@/components/ui/separator'
import { SkillBadge } from '@/components/resume/SkillBadge'
import { useResume } from '@/lib/hooks/useResumes'
import { formatMonths } from '@/lib/utils'
import { ApiClientError } from '@/lib/api/client'

const statusVariant: Record<string, 'default' | 'secondary' | 'outline'> = {
  draft: 'outline',
  active: 'default',
  archived: 'secondary',
}

export default function ResumeDetailPage({ params }: { params: Promise<{ id: string }> }) {
  const { id } = use(params)
  const { data: resume, isLoading, error } = useResume(id)

  if (isLoading) {
    return (
      <div className="space-y-4 max-w-3xl">
        <div className="h-8 w-48 bg-muted animate-pulse rounded" />
        <div className="h-40 bg-muted animate-pulse rounded-lg" />
        <div className="h-32 bg-muted animate-pulse rounded-lg" />
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
              ? 'You don\'t have access to this resume.'
              : 'Failed to load resume.'}
        </p>
        <Link href="/resumes" className="text-sm underline underline-offset-4">
          Back to resumes
        </Link>
      </div>
    )
  }

  if (!resume) return null

  return (
    <div className="space-y-6 max-w-3xl">
      {/* Header */}
      <div className="flex items-center gap-3">
        <Link href="/resumes" className="text-muted-foreground hover:text-foreground transition-colors">
          <ArrowLeft size={18} />
        </Link>
        <h1 className="text-2xl font-semibold flex-1">{resume.contact_info.email || 'Resume'}</h1>
        <Badge variant={statusVariant[resume.status] ?? 'outline'} className="capitalize">
          {resume.status}
        </Badge>
      </div>

      {/* Contact info */}
      <Card>
        <CardHeader className="pb-3">
          <CardTitle className="text-base">Contact</CardTitle>
        </CardHeader>
        <CardContent className="flex flex-wrap gap-4 text-sm text-muted-foreground">
          {resume.contact_info.email && (
            <span className="flex items-center gap-1.5">
              <Mail size={14} />
              {resume.contact_info.email}
            </span>
          )}
          {resume.contact_info.phone && (
            <span className="flex items-center gap-1.5">
              <Phone size={14} />
              {resume.contact_info.phone}
            </span>
          )}
          {resume.contact_info.location && (
            <span className="flex items-center gap-1.5">
              <MapPin size={14} />
              {resume.contact_info.location}
            </span>
          )}
          {resume.total_experience_months > 0 && (
            <span className="font-medium text-foreground">
              {formatMonths(resume.total_experience_months)} experience
            </span>
          )}
        </CardContent>
      </Card>

      {/* Skills */}
      <Card>
        <CardHeader className="pb-3">
          <CardTitle className="text-base">
            Skills{resume.skills.length > 0 && ` (${resume.skills.length})`}
          </CardTitle>
        </CardHeader>
        <CardContent>
          {resume.skills.length === 0 ? (
            <p className="text-sm text-muted-foreground">
              No skills yet. Use the analyze feature to extract them automatically.
            </p>
          ) : (
            <div className="flex flex-wrap gap-2">
              {resume.skills.map((skill, i) => (
                <SkillBadge key={i} skill={skill} />
              ))}
            </div>
          )}
        </CardContent>
      </Card>

      {/* Resume text preview */}
      <Card>
        <CardHeader className="pb-3">
          <CardTitle className="text-base">Resume preview</CardTitle>
        </CardHeader>
        <CardContent>
          <p className="text-sm text-muted-foreground whitespace-pre-wrap leading-relaxed">
            {resume.raw_text_preview}
          </p>
        </CardContent>
      </Card>

      {/* Experience */}
      {resume.experiences.length > 0 && (
        <Card>
          <CardHeader className="pb-3">
            <CardTitle className="text-base">Experience</CardTitle>
          </CardHeader>
          <CardContent className="space-y-4">
            {resume.experiences.map((exp, i) => (
              <div key={i}>
                {i > 0 && <Separator className="mb-4" />}
                <div className="flex justify-between items-start">
                  <div>
                    <p className="font-medium text-sm">{exp.role}</p>
                    <p className="text-sm text-muted-foreground">{exp.company}</p>
                  </div>
                  <span className="text-xs text-muted-foreground shrink-0">
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
          <CardHeader className="pb-3">
            <CardTitle className="text-base">Education</CardTitle>
          </CardHeader>
          <CardContent className="space-y-3">
            {resume.education.map((edu, i) => (
              <div key={i} className="flex justify-between items-start text-sm">
                <div>
                  <p className="font-medium">{edu.degree}</p>
                  <p className="text-muted-foreground">{edu.institution}</p>
                </div>
                <span className="text-muted-foreground shrink-0">{edu.graduation_year}</span>
              </div>
            ))}
          </CardContent>
        </Card>
      )}
    </div>
  )
}
