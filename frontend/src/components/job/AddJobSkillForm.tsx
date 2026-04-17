'use client'

import { useState } from 'react'
import { useForm } from 'react-hook-form'
import { zodResolver } from '@hookform/resolvers/zod'
import { z } from 'zod'
import { Button } from '@/components/ui/button'
import { Input } from '@/components/ui/input'
import { Label } from '@/components/ui/label'
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from '@/components/ui/select'
import { useAddJobSkill } from '@/lib/hooks/useJobs'
import { ApiClientError } from '@/lib/api/client'
import { SKILL_CATEGORIES } from '@/lib/constants/skillCategories'

const schema = z.object({
  name: z.string().min(1, 'Skill name is required'),
})

type FormValues = z.infer<typeof schema>

export function AddJobSkillForm({ jobId }: { jobId: string }) {
  const [open, setOpen] = useState(false)
  const [serverError, setServerError] = useState('')
  const [category, setCategory] = useState('language')
  const [proficiency, setProficiency] = useState('intermediate')
  const addSkill = useAddJobSkill(jobId)

  const {
    register,
    handleSubmit,
    reset,
    formState: { errors, isSubmitting },
  } = useForm<FormValues>({ resolver: zodResolver(schema) })

  const onSubmit = async (data: FormValues) => {
    setServerError('')
    try {
      await addSkill.mutateAsync({ ...data, category, proficiency_level: proficiency })
      reset()
      setCategory('language')
      setProficiency('intermediate')
      setOpen(false)
    } catch (err) {
      if (err instanceof ApiClientError) {
        setServerError(err.detail)
      } else {
        setServerError('Something went wrong. Please try again.')
      }
    }
  }

  if (!open) {
    return (
      <Button variant="outline" size="sm" onClick={() => setOpen(true)}>
        + Add skill
      </Button>
    )
  }

  return (
    <form onSubmit={handleSubmit(onSubmit)} className="space-y-3 rounded-lg border p-4">
      <div className="grid grid-cols-2 gap-3">
        <div className="space-y-1">
          <Label htmlFor="job-skill-name">Skill name</Label>
          <Input id="job-skill-name" {...register('name')} placeholder="e.g. Python" />
          {errors.name && <p className="text-xs text-destructive">{errors.name.message}</p>}
        </div>
        <div className="space-y-1">
          <Label>Category</Label>
          <Select value={category} onValueChange={(v) => v && setCategory(v)}>
            <SelectTrigger className="w-full">
              <SelectValue />
            </SelectTrigger>
            <SelectContent>
              {SKILL_CATEGORIES.map((c) => (
                <SelectItem key={c.value} value={c.value}>
                  {c.label}
                </SelectItem>
              ))}
            </SelectContent>
          </Select>
        </div>
      </div>

      <div className="space-y-1">
        <Label>Proficiency level</Label>
        <Select value={proficiency} onValueChange={(v) => v && setProficiency(v)}>
          <SelectTrigger className="w-full">
            <SelectValue />
          </SelectTrigger>
          <SelectContent>
            <SelectItem value="beginner">Beginner</SelectItem>
            <SelectItem value="intermediate">Intermediate</SelectItem>
            <SelectItem value="advanced">Advanced</SelectItem>
            <SelectItem value="expert">Expert</SelectItem>
          </SelectContent>
        </Select>
      </div>

      {serverError && <p className="text-xs text-destructive">{serverError}</p>}

      <div className="flex gap-2">
        <Button type="submit" size="sm" disabled={isSubmitting}>
          {isSubmitting ? 'Adding…' : 'Add skill'}
        </Button>
        <Button
          type="button"
          size="sm"
          variant="outline"
          onClick={() => {
            setOpen(false)
            setServerError('')
            reset()
          }}
        >
          Cancel
        </Button>
      </div>
    </form>
  )
}
