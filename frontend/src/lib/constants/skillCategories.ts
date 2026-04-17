export const SKILL_CATEGORIES = [
  { value: 'language',     label: 'Language',     hint: 'Python, Go, TypeScript, SQL' },
  { value: 'framework',    label: 'Framework',    hint: 'Django, React, FastAPI, Next.js' },
  { value: 'database',     label: 'Database',     hint: 'PostgreSQL, Redis, MongoDB' },
  { value: 'cloud',        label: 'Cloud',        hint: 'AWS, GCP, Azure' },
  { value: 'devops',       label: 'DevOps',       hint: 'Docker, Kubernetes, CI/CD' },
  { value: 'architecture', label: 'Architecture', hint: 'REST APIs, GraphQL, Microservices' },
  { value: 'data-science', label: 'Data Science', hint: 'Pandas, TensorFlow, scikit-learn' },
  { value: 'tooling',      label: 'Tooling',      hint: 'Git, Linux, VS Code' },
  { value: 'testing',      label: 'Testing',      hint: 'pytest, Jest, Cypress' },
  { value: 'methodology',  label: 'Methodology',  hint: 'Agile, Scrum, TDD' },
] as const

export type SkillCategory = typeof SKILL_CATEGORIES[number]['value']

/** Priority map — lower number = higher priority (matches backend CATEGORY_PRIORITY) */
export const CATEGORY_PRIORITY: Record<string, number> = Object.fromEntries(
  SKILL_CATEGORIES.map((c, i) => [c.value, i + 1])
)

/** Human-readable label for a category value (falls back to the raw value) */
export function categoryLabel(value: string): string {
  return SKILL_CATEGORIES.find((c) => c.value === value)?.label ?? value
}
