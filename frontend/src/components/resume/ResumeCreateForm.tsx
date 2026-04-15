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
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
import { useCreateResume } from '@/lib/hooks/useResumes'
import { ApiClientError } from '@/lib/api/client'

const createResumeSchema = z.object({
  raw_text: z.string().min(50, 'Resume text must be at least 50 characters'),
  email: z.email('Enter a valid email'),
  phone: z.string().min(1, 'Phone is required'),
  location: z.string().min(1, 'Location is required'),
})

type CreateResumeFormValues = z.infer<typeof createResumeSchema>

export function ResumeCreateForm() {
  const router = useRouter()
  const [serverError, setServerError] = useState('')
  const createResume = useCreateResume()

  const {
    register,
    handleSubmit,
    formState: { errors, isSubmitting },
  } = useForm<CreateResumeFormValues>({ resolver: zodResolver(createResumeSchema) })

  const onSubmit = async (data: CreateResumeFormValues) => {
    setServerError('')
    try {
      const dto = await createResume.mutateAsync(data)
      router.push(`/resumes/${dto.resume_id}`)
    } catch (err) {
      if (err instanceof ApiClientError) {
        setServerError(err.detail)
      } else {
        setServerError('Something went wrong. Please try again.')
      }
    }
  }

  return (
    <Card className="max-w-2xl">
      <CardHeader>
        <CardTitle>New resume</CardTitle>
        <CardDescription>Paste your resume text and fill in your contact details</CardDescription>
      </CardHeader>
      <CardContent>
        <form onSubmit={handleSubmit(onSubmit)} className="space-y-5">
          <div className="space-y-1.5">
            <Label htmlFor="raw_text">Resume text</Label>
            <Textarea
              id="raw_text"
              {...register('raw_text')}
              rows={10}
              placeholder="Paste your full resume content here…"
              className="resize-y"
            />
            {errors.raw_text && (
              <p className="text-sm text-destructive">{errors.raw_text.message}</p>
            )}
          </div>

          <div className="grid grid-cols-2 gap-4">
            <div className="space-y-1.5">
              <Label htmlFor="email">Email</Label>
              <Input id="email" type="email" {...register('email')} />
              {errors.email && (
                <p className="text-sm text-destructive">{errors.email.message}</p>
              )}
            </div>

            <div className="space-y-1.5">
              <Label htmlFor="phone">Phone</Label>
              <Input id="phone" type="tel" {...register('phone')} />
              {errors.phone && (
                <p className="text-sm text-destructive">{errors.phone.message}</p>
              )}
            </div>
          </div>

          <div className="space-y-1.5">
            <Label htmlFor="location">Location</Label>
            <Input id="location" {...register('location')} placeholder="City, Country" />
            {errors.location && (
              <p className="text-sm text-destructive">{errors.location.message}</p>
            )}
          </div>

          {serverError && <p className="text-sm text-destructive">{serverError}</p>}

          <div className="flex gap-3">
            <Button type="submit" disabled={isSubmitting}>
              {isSubmitting ? 'Creating…' : 'Create resume'}
            </Button>
            <Button type="button" variant="outline" onClick={() => router.back()}>
              Cancel
            </Button>
          </div>
        </form>
      </CardContent>
    </Card>
  )
}
