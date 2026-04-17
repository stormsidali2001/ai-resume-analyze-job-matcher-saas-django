import Link from 'next/link'
import { MapPin } from 'lucide-react'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'
import { Badge } from '@/components/ui/badge'
import { cn, formatMonths } from '@/lib/utils'
import type { ResumeDTO } from '@/types/api'

const statusBorder: Record<string, string> = {
  draft: 'border-l-4 border-l-amber-400',
  active: 'border-l-4 border-l-indigo-500',
  archived: 'border-l-4 border-l-border',
}

const statusVariant: Record<string, 'default' | 'secondary' | 'outline'> = {
  draft: 'outline',
  active: 'default',
  archived: 'secondary',
}

export function ResumeCard({ resume }: { resume: ResumeDTO }) {
  return (
    <Link href={`/resumes/${resume.resume_id}`} className="block group">
      <Card className={cn(
        'h-full cursor-pointer transition-shadow group-hover:shadow-md',
        statusBorder[resume.status] ?? 'border-l-4 border-l-border',
      )}>
        <CardHeader className="pb-2">
          <div className="flex items-start justify-between gap-2">
            <CardTitle className="text-sm font-semibold leading-snug">
              {resume.contact_info.email || 'Untitled resume'}
            </CardTitle>
            <Badge variant={statusVariant[resume.status] ?? 'outline'} className="shrink-0 capitalize text-xs">
              {resume.status}
            </Badge>
          </div>
        </CardHeader>
        <CardContent className="space-y-3">
          <p className="text-xs text-muted-foreground line-clamp-2 leading-relaxed">
            {resume.raw_text_preview}
          </p>
          <div className="flex flex-wrap items-center gap-2">
            {resume.skills.length > 0 && (
              <Badge variant="secondary" className="text-xs font-normal">
                {resume.skills.length} skill{resume.skills.length !== 1 ? 's' : ''}
              </Badge>
            )}
            {resume.total_experience_months > 0 && (
              <span className="text-xs text-muted-foreground">
                {formatMonths(resume.total_experience_months)} exp
              </span>
            )}
            {resume.contact_info.location && (
              <span className="flex items-center gap-0.5 text-xs text-muted-foreground">
                <MapPin size={10} />
                {resume.contact_info.location}
              </span>
            )}
          </div>
        </CardContent>
      </Card>
    </Link>
  )
}
