'use client'

import { useState } from 'react'
import { useForm } from 'react-hook-form'
import { zodResolver } from '@hookform/resolvers/zod'
import { z } from 'zod'
import { useRouter } from 'next/navigation'
import { Button } from '@/components/ui/button'
import { Input } from '@/components/ui/input'
import { Label } from '@/components/ui/label'
import { Textarea } from '@/components/ui/textarea'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from '@/components/ui/select'
import { PageHeader } from '@/components/layout/PageHeader'
import { useCreateJob } from '@/lib/hooks/useJobs'
import { ApiClientError } from '@/lib/api/client'

const schema = z.object({
  title: z.string().min(1, 'Title is required'),
  company: z.string().min(1, 'Company is required'),
  description: z.string().min(20, 'Description must be at least 20 characters'),
  city: z.string().min(1, 'City is required'),
  country: z.string().min(1, 'Country is required'),
  required_experience_months: z.string().min(1),
  min_salary: z.string().optional(),
  max_salary: z.string().optional(),
  currency: z.string().optional(),
})

type FormValues = z.infer<typeof schema>

export default function NewJobPage() {
  const router = useRouter()
  const [employmentType, setEmploymentType] = useState('full_time')
  const [remote, setRemote] = useState('false')
  const [serverError, setServerError] = useState('')
  const createJob = useCreateJob()

  // eslint-disable-next-line @typescript-eslint/no-explicit-any
  const { register, handleSubmit, formState: { errors, isSubmitting } } = useForm<any>({
    resolver: zodResolver(schema),
    defaultValues: { required_experience_months: '0' },
  })

  const onSubmit = async (data: FormValues) => {
    setServerError('')
    try {
      const expMonths = parseInt(data.required_experience_months as unknown as string, 10) || 0
      const minSal = data.min_salary ? parseFloat(data.min_salary as unknown as string) : undefined
      const maxSal = data.max_salary ? parseFloat(data.max_salary as unknown as string) : undefined
      const payload: Parameters<typeof createJob.mutateAsync>[0] = {
        title: data.title,
        company: data.company,
        description: data.description,
        city: data.city,
        country: data.country,
        remote: remote === 'true',
        employment_type: employmentType as Parameters<typeof createJob.mutateAsync>[0]['employment_type'],
        required_experience_months: expMonths,
        ...(minSal && maxSal
          ? { salary_range: { min_salary: minSal, max_salary: maxSal, currency: data.currency || 'USD' } }
          : {}),
      }
      const job = await createJob.mutateAsync(payload)
      router.push(`/recruiter/jobs/${job.job_id}`)
    } catch (err) {
      if (err instanceof ApiClientError) {
        setServerError(err.detail)
      } else {
        setServerError('Something went wrong. Please try again.')
      }
    }
  }

  return (
    <div className="max-w-2xl space-y-6">
      <PageHeader
        title="Create a new job"
        description="Fill in the details. You can add required skills after creation."
      />
      <Card>
        <CardHeader>
          <CardTitle className="text-sm font-semibold text-muted-foreground uppercase tracking-wider">Job details</CardTitle>
        </CardHeader>
        <CardContent>
          <form onSubmit={handleSubmit(onSubmit)} className="space-y-5">
            <div className="grid grid-cols-2 gap-4">
              <div className="space-y-1.5">
                <Label htmlFor="title">Title</Label>
                <Input id="title" {...register('title')} placeholder="e.g. Senior Engineer" />
                {errors.title?.message && <p className="text-xs text-destructive">{String(errors.title.message)}</p>}
              </div>
              <div className="space-y-1.5">
                <Label htmlFor="company">Company</Label>
                <Input id="company" {...register('company')} placeholder="e.g. Acme Corp" />
                {errors.company?.message && <p className="text-xs text-destructive">{String(errors.company.message)}</p>}
              </div>
            </div>

            <div className="space-y-1.5">
              <Label htmlFor="description">Description</Label>
              <Textarea id="description" {...register('description')} rows={6} placeholder="Describe the role, responsibilities, and requirements…" className="resize-y" />
              {errors.description?.message && <p className="text-xs text-destructive">{String(errors.description.message)}</p>}
            </div>

            <div className="grid grid-cols-2 gap-4">
              <div className="space-y-1.5">
                <Label htmlFor="city">City</Label>
                <Input id="city" {...register('city')} placeholder="e.g. Paris" />
                {errors.city?.message && <p className="text-xs text-destructive">{String(errors.city.message)}</p>}
              </div>
              <div className="space-y-1.5">
                <Label htmlFor="country">Country</Label>
                <Input id="country" {...register('country')} placeholder="e.g. France" />
                {errors.country?.message && <p className="text-xs text-destructive">{String(errors.country.message)}</p>}
              </div>
            </div>

            <div className="grid grid-cols-3 gap-4">
              <div className="space-y-1.5">
                <Label>Employment type</Label>
                <Select value={employmentType} onValueChange={(v) => v && setEmploymentType(v)}>
                  <SelectTrigger className="w-full">
                    <SelectValue />
                  </SelectTrigger>
                  <SelectContent>
                    <SelectItem value="full_time">Full-time</SelectItem>
                    <SelectItem value="part_time">Part-time</SelectItem>
                    <SelectItem value="contract">Contract</SelectItem>
                    <SelectItem value="freelance">Freelance</SelectItem>
                    <SelectItem value="internship">Internship</SelectItem>
                  </SelectContent>
                </Select>
              </div>
              <div className="space-y-1.5">
                <Label>Remote</Label>
                <Select value={remote} onValueChange={(v) => v && setRemote(v)}>
                  <SelectTrigger className="w-full">
                    <SelectValue />
                  </SelectTrigger>
                  <SelectContent>
                    <SelectItem value="false">On-site</SelectItem>
                    <SelectItem value="true">Remote</SelectItem>
                  </SelectContent>
                </Select>
              </div>
              <div className="space-y-1.5">
                <Label htmlFor="exp">Experience (months)</Label>
                <Input id="exp" type="number" min={0} {...register('required_experience_months')} />
                {errors.required_experience_months?.message && (
                  <p className="text-xs text-destructive">{String(errors.required_experience_months.message)}</p>
                )}
              </div>
            </div>

            <div className="space-y-1.5">
              <Label className="text-muted-foreground">Salary range (optional)</Label>
              <div className="grid grid-cols-3 gap-3">
                <Input type="number" {...register('min_salary')} placeholder="Min" />
                <Input type="number" {...register('max_salary')} placeholder="Max" />
                <Input {...register('currency')} placeholder="Currency (USD)" />
              </div>
            </div>

            {serverError && <p className="text-sm text-destructive">{serverError}</p>}

            <div className="flex gap-3">
              <Button type="submit" disabled={isSubmitting}>
                {isSubmitting ? 'Creating…' : 'Create job'}
              </Button>
              <Button type="button" variant="outline" onClick={() => router.back()}>
                Cancel
              </Button>
            </div>
          </form>
        </CardContent>
      </Card>
    </div>
  )
}
