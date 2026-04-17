import Link from 'next/link'
import { MapPin, Globe, Clock } from 'lucide-react'
import { Badge } from '@/components/ui/badge'
import { Card, CardContent, CardHeader } from '@/components/ui/card'
import { cn } from '@/lib/utils'
import type { JobDTO } from '@/types/api'

const employmentLabels: Record<string, string> = {
  full_time: 'Full-time',
  part_time: 'Part-time',
  contract: 'Contract',
  freelance: 'Freelance',
  internship: 'Internship',
}

const employmentColors: Record<string, string> = {
  full_time: 'bg-indigo-50 text-indigo-700 dark:bg-indigo-950/50 dark:text-indigo-300',
  part_time: 'bg-violet-50 text-violet-700 dark:bg-violet-950/50 dark:text-violet-300',
  contract: 'bg-amber-50 text-amber-700 dark:bg-amber-950/50 dark:text-amber-300',
  freelance: 'bg-orange-50 text-orange-700 dark:bg-orange-950/50 dark:text-orange-300',
  internship: 'bg-emerald-50 text-emerald-700 dark:bg-emerald-950/50 dark:text-emerald-300',
}

export function JobCard({ job }: { job: JobDTO }) {
  const visibleSkills = job.required_skills.slice(0, 3)
  const remaining = job.required_skills.length - visibleSkills.length
  const companyInitial = job.company.charAt(0).toUpperCase()

  return (
    <Link href={`/jobs/${job.job_id}`} className="block group">
      <Card className="h-full cursor-pointer transition-shadow group-hover:shadow-md">
        <CardHeader className="pb-2">
          <div className="flex items-start gap-3">
            {/* Company avatar */}
            <div className="flex size-9 shrink-0 items-center justify-center rounded-lg bg-primary/10 text-primary text-sm font-semibold">
              {companyInitial}
            </div>
            <div className="flex-1 min-w-0">
              <p className="font-semibold text-sm leading-tight truncate">{job.title}</p>
              <p className="text-xs text-muted-foreground truncate mt-0.5">{job.company}</p>
            </div>
            <span className={cn(
              'shrink-0 rounded-full px-2 py-0.5 text-xs font-medium',
              employmentColors[job.employment_type] ?? 'bg-muted text-muted-foreground',
            )}>
              {employmentLabels[job.employment_type] ?? job.employment_type}
            </span>
          </div>
        </CardHeader>
        <CardContent className="space-y-3">
          <div className="flex flex-wrap gap-3 text-xs text-muted-foreground">
            <span className="flex items-center gap-1">
              <MapPin size={11} />
              {job.location.city}, {job.location.country}
            </span>
            {job.location.remote && (
              <span className="flex items-center gap-1">
                <Globe size={11} />
                Remote
              </span>
            )}
            {job.required_experience_months > 0 && (
              <span className="flex items-center gap-1">
                <Clock size={11} />
                {Math.round(job.required_experience_months / 12)}y exp
              </span>
            )}
          </div>

          {job.required_skills.length > 0 && (
            <div className="flex flex-wrap gap-1.5">
              {visibleSkills.map((skill, i) => (
                <Badge key={i} variant="secondary" className="text-xs font-normal">
                  {skill.name}
                </Badge>
              ))}
              {remaining > 0 && (
                <Badge variant="outline" className="text-xs text-muted-foreground">
                  +{remaining}
                </Badge>
              )}
            </div>
          )}
        </CardContent>
      </Card>
    </Link>
  )
}
