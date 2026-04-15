import Link from 'next/link'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'
import { Badge } from '@/components/ui/badge'
import { formatMonths } from '@/lib/utils'
import type { ResumeDTO } from '@/types/api'

const statusVariant: Record<string, 'default' | 'secondary' | 'outline'> = {
  draft: 'outline',
  active: 'default',
  archived: 'secondary',
}

export function ResumeCard({ resume }: { resume: ResumeDTO }) {
  return (
    <Link href={`/resumes/${resume.resume_id}`}>
      <Card className="hover:shadow-md transition-shadow cursor-pointer h-full">
        <CardHeader className="pb-2">
          <div className="flex items-start justify-between gap-2">
            <CardTitle className="text-base leading-snug">
              {resume.contact_info.email || 'Untitled resume'}
            </CardTitle>
            <Badge variant={statusVariant[resume.status] ?? 'outline'} className="shrink-0 capitalize">
              {resume.status}
            </Badge>
          </div>
        </CardHeader>
        <CardContent className="space-y-2">
          <p className="text-sm text-muted-foreground line-clamp-2">{resume.raw_text_preview}</p>
          <div className="flex items-center gap-3 text-xs text-muted-foreground">
            <span>{resume.skills.length} skills</span>
            {resume.total_experience_months > 0 && (
              <span>{formatMonths(resume.total_experience_months)} exp</span>
            )}
            {resume.contact_info.location && <span>{resume.contact_info.location}</span>}
          </div>
        </CardContent>
      </Card>
    </Link>
  )
}
