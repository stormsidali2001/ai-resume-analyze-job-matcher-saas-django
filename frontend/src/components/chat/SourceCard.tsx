import { Briefcase, User } from 'lucide-react'
import type { ChatSource } from '@/types/api'

interface SourceCardProps {
  source: ChatSource
  index: number
  isJobSource: boolean
}

export function SourceCard({ source, index, isJobSource }: SourceCardProps) {
  return (
    <div className="flex items-start gap-2.5 rounded-lg border border-border bg-card px-3 py-2.5 text-sm min-w-0">
      <div className="mt-0.5 flex size-6 shrink-0 items-center justify-center rounded-full bg-muted text-muted-foreground text-xs font-semibold">
        {index + 1}
      </div>
      <div className="flex-1 min-w-0">
        <div className="flex items-center gap-1.5">
          {isJobSource ? (
            <Briefcase size={12} className="shrink-0 text-muted-foreground" />
          ) : (
            <User size={12} className="shrink-0 text-muted-foreground" />
          )}
          <span className="font-medium text-foreground truncate">{source.title}</span>
        </div>
        <p className="mt-0.5 text-xs text-muted-foreground truncate">{source.subtitle}</p>
        {source.detail && (
          <span className="mt-1 inline-block rounded-full bg-muted px-2 py-0.5 text-xs text-muted-foreground">
            {source.detail}
          </span>
        )}
      </div>
    </div>
  )
}
