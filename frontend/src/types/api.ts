// src/types/api.ts
// TypeScript types derived from the Django REST Framework serializer shapes.

export type UserRole = 'candidate' | 'recruiter'
export type ResumeStatus = 'draft' | 'active' | 'archived'
export type JobStatus = 'draft' | 'published' | 'closed'
export type ProficiencyLevel = 'beginner' | 'intermediate' | 'advanced' | 'expert'
export type EmploymentType =
  | 'full_time'
  | 'part_time'
  | 'contract'
  | 'freelance'
  | 'internship'
export type ScoreLabel = 'poor' | 'weak' | 'acceptable' | 'strong'

// Auth
export interface AuthUser {
  id: string
  username: string
  email: string
  role: UserRole
}

export interface AuthResponse {
  user: AuthUser
  access: string
  refresh: string
}

export interface TokenRefreshResponse {
  access: string
}

// Resume
export interface ContactInfo {
  email: string
  phone: string
  location: string
}

export interface Skill {
  name: string
  category: string
  proficiency_level: ProficiencyLevel
}

export interface Experience {
  role: string
  company: string
  duration_months: number
  responsibilities: string[]
}

export interface Education {
  degree: string
  institution: string
  graduation_year: number
}

export interface ResumeDTO {
  resume_id: string
  candidate_id: string
  status: ResumeStatus
  raw_text_preview: string
  contact_info: ContactInfo
  skills: Skill[]
  experiences: Experience[]
  education: Education[]
  total_experience_months: number
  created_at: string
  updated_at: string
}

export interface CreateResumeRequest {
  raw_text: string
  email: string
  phone: string
  location: string
}

export interface UpdateResumeTextRequest {
  new_raw_text: string
}

export interface AddSkillRequest {
  name: string
  category: string
  proficiency_level: ProficiencyLevel
}

// Job
export interface JobLocation {
  city: string
  country: string
  remote: boolean
}

export interface SalaryRange {
  min_salary: number
  max_salary: number
  currency: string
}

export interface JobDTO {
  job_id: string
  recruiter_id: string
  title: string
  company: string
  description_preview: string
  required_skills: Skill[]
  required_experience_months: number
  location: JobLocation
  employment_type: EmploymentType
  salary_range: SalaryRange | null
  status: JobStatus
  created_at: string
}

// Match
export interface Gap {
  gap_type: string
  description: string
}

export interface Suggestion {
  text: string
  priority: string
  category: string
}

export interface MatchResultDTO {
  match_id: string
  resume_id: string
  job_id: string
  score: number
  score_label: ScoreLabel
  gaps: Gap[]
  suggestions: Suggestion[]
  calculated_at: string
}

export interface MatchRequest {
  resume_id: string
  job_id: string
}

// API error
export interface ApiError {
  detail: string | Record<string, unknown>[]
}
