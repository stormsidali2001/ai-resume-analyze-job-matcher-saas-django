import { Badge } from '@/components/ui/badge'
import type { Skill } from '@/types/api'

const variantMap: Record<string, 'default' | 'secondary' | 'outline'> = {
  expert: 'default',
  advanced: 'secondary',
  intermediate: 'outline',
  beginner: 'outline',
}

export function SkillBadge({ skill }: { skill: Skill }) {
  const variant = variantMap[skill.proficiency_level] ?? 'outline'
  return (
    <Badge variant={variant} className="text-xs">
      {skill.name}
      <span className="ml-1 opacity-60">· {skill.category}</span>
    </Badge>
  )
}
