import { Badge } from '@/components/ui/badge'
import { cn } from '@/lib/utils'
import type { MatchResultDTO } from '@/types/api'

const scoreConfig: Record<string, { stroke: string; text: string; bg: string; label: string }> = {
  strong:     { stroke: 'stroke-indigo-500',  text: 'text-indigo-600 dark:text-indigo-400',  bg: 'bg-indigo-50 text-indigo-700 dark:bg-indigo-950/50 dark:text-indigo-300',  label: 'Strong' },
  acceptable: { stroke: 'stroke-amber-400',   text: 'text-amber-600 dark:text-amber-400',   bg: 'bg-amber-50 text-amber-700 dark:bg-amber-950/50 dark:text-amber-300',   label: 'Acceptable' },
  weak:       { stroke: 'stroke-orange-400',  text: 'text-orange-600 dark:text-orange-400', bg: 'bg-orange-50 text-orange-700 dark:bg-orange-950/50 dark:text-orange-300', label: 'Weak' },
  poor:       { stroke: 'stroke-red-500',     text: 'text-red-600 dark:text-red-400',       bg: 'bg-red-50 text-red-700 dark:bg-red-950/50 dark:text-red-300',       label: 'Poor' },
}

const priorityVariant: Record<string, 'default' | 'secondary' | 'outline' | 'destructive'> = {
  high: 'destructive',
  medium: 'secondary',
  low: 'outline',
}

function ScoreGauge({ score, label }: { score: number; label: string }) {
  // score is 0–100 integer from the backend
  const pct = Math.round(score)
  const config = scoreConfig[label] ?? scoreConfig.poor
  const radius = 44
  const circumference = 2 * Math.PI * radius
  const offset = circumference * (1 - score / 100)

  return (
    <div className="flex items-center gap-5">
      <div className="relative flex size-28 items-center justify-center">
        <svg className="-rotate-90" width="112" height="112" viewBox="0 0 112 112">
          {/* Track */}
          <circle
            cx="56" cy="56" r={radius}
            fill="none"
            className="stroke-muted"
            strokeWidth="8"
          />
          {/* Progress */}
          <circle
            cx="56" cy="56" r={radius}
            fill="none"
            className={cn('transition-all duration-700', config.stroke)}
            strokeWidth="8"
            strokeLinecap="round"
            strokeDasharray={circumference}
            strokeDashoffset={offset}
          />
        </svg>
        <div className="absolute inset-0 flex flex-col items-center justify-center">
          <span className={cn('text-3xl font-bold tabular-nums leading-none', config.text)}>
            {pct}
          </span>
          <span className="text-[10px] text-muted-foreground mt-0.5">/ 100</span>
        </div>
      </div>

      <div className="space-y-1.5">
        <span className={cn('inline-block rounded-full px-3 py-1 text-sm font-semibold', config.bg)}>
          {config.label}
        </span>
        <p className="text-xs text-muted-foreground">match score</p>
      </div>
    </div>
  )
}

export function MatchResult({ result }: { result: MatchResultDTO }) {
  return (
    <div className="space-y-6">
      <ScoreGauge score={result.score} label={result.score_label} />

      {result.gaps.length > 0 && (
        <div className="space-y-2">
          <div className="flex items-center gap-2">
            <span className="size-2 rounded-full bg-destructive/70" />
            <h4 className="text-sm font-semibold">Gaps</h4>
          </div>
          <ul className="space-y-1.5">
            {result.gaps.map((gap, i) => (
              <li key={i} className="rounded-lg border border-destructive/15 bg-destructive/5 px-3 py-2 text-sm">
                <span className="font-medium capitalize">{gap.gap_type.replace('_', ' ')}</span>
                {gap.description && (
                  <span className="text-muted-foreground"> — {gap.description}</span>
                )}
              </li>
            ))}
          </ul>
        </div>
      )}

      {result.suggestions.length > 0 && (
        <div className="space-y-2">
          <div className="flex items-center gap-2">
            <span className="size-2 rounded-full bg-primary/70" />
            <h4 className="text-sm font-semibold">Suggestions</h4>
          </div>
          <ul className="space-y-1.5">
            {result.suggestions.map((s, i) => (
              <li key={i} className="flex items-start gap-2.5 text-sm">
                <Badge
                  variant={priorityVariant[s.priority] ?? 'outline'}
                  className="shrink-0 capitalize text-xs mt-0.5"
                >
                  {s.priority}
                </Badge>
                <span className="text-muted-foreground">{s.text}</span>
              </li>
            ))}
          </ul>
        </div>
      )}
    </div>
  )
}
