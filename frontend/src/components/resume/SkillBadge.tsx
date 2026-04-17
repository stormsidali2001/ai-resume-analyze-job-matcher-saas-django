import { Badge } from '@/components/ui/badge'
import type { Skill } from '@/types/api'

const variantMap: Record<string, 'default' | 'secondary' | 'outline'> = {
  expert:       'default',
  advanced:     'secondary',
  intermediate: 'outline',
  beginner:     'outline',
}

const proficiencyShort: Record<string, string> = {
  expert:       'exp',
  advanced:     'adv',
  intermediate: 'int',
  beginner:     'beg',
}

export function SkillBadge({ skill }: { skill: Skill }) {
  const variant = variantMap[skill.proficiency_level] ?? 'outline'
  return (
    <Badge variant={variant} className="text-xs gap-1">
      {skill.name}
      <span className="opacity-50 font-normal">· {skill.category}</span>
      <span className="opacity-40 text-[10px] font-normal">
        {proficiencyShort[skill.proficiency_level] ?? skill.proficiency_level}
      </span>
    </Badge>
  )
}
