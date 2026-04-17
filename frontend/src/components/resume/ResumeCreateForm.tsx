'use client'

import { useRef, useState } from 'react'
import { useForm } from 'react-hook-form'
import { zodResolver } from '@hookform/resolvers/zod'
import { z } from 'zod'
import { useRouter } from 'next/navigation'
import { Upload, FileText } from 'lucide-react'
import { Button } from '@/components/ui/button'
import { Input } from '@/components/ui/input'
import { Label } from '@/components/ui/label'
import { Textarea } from '@/components/ui/textarea'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
import { cn } from '@/lib/utils'
import { useCreateResume } from '@/lib/hooks/useResumes'
import { resumesApi } from '@/lib/api/resumes'
import { ApiClientError } from '@/lib/api/client'

const MAX_FILE_SIZE = 5 * 1024 * 1024 // 5 MB

const textSchema = z.object({
  raw_text: z.string().min(50, 'Resume text must be at least 50 characters'),
  email: z.email('Enter a valid email'),
  phone: z.string().min(1, 'Phone is required'),
  location: z.string().min(1, 'Location is required'),
})

const contactSchema = z.object({
  email: z.email('Enter a valid email'),
  phone: z.string().min(1, 'Phone is required'),
  location: z.string().min(1, 'Location is required'),
})

type TextFormValues = z.infer<typeof textSchema>
type ContactFormValues = z.infer<typeof contactSchema>

export function ResumeCreateForm() {
  const router = useRouter()
  const [mode, setMode] = useState<'text' | 'pdf'>('text')
  const [serverError, setServerError] = useState('')
  const [selectedFile, setSelectedFile] = useState<File | null>(null)
  const [fileError, setFileError] = useState('')
  const [isUploading, setIsUploading] = useState(false)
  const fileInputRef = useRef<HTMLInputElement>(null)
  const createResume = useCreateResume()

  const textForm = useForm<TextFormValues>({ resolver: zodResolver(textSchema) })
  const contactForm = useForm<ContactFormValues>({ resolver: zodResolver(contactSchema) })

  const handleFileChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0] ?? null
    setFileError('')
    if (!file) { setSelectedFile(null); return }
    if (file.type !== 'application/pdf') {
      setFileError('Only PDF files are accepted.')
      setSelectedFile(null)
      return
    }
    if (file.size > MAX_FILE_SIZE) {
      setFileError('File must be under 5 MB.')
      setSelectedFile(null)
      return
    }
    setSelectedFile(file)
  }

  const onTextSubmit = async (data: TextFormValues) => {
    setServerError('')
    try {
      const dto = await createResume.mutateAsync(data)
      router.push(`/resumes/${dto.resume_id}`)
    } catch (err) {
      setServerError(err instanceof ApiClientError ? err.detail : 'Something went wrong.')
    }
  }

  const onPdfSubmit = async (data: ContactFormValues) => {
    if (!selectedFile) { setFileError('Please select a PDF file.'); return }
    setServerError('')
    setIsUploading(true)
    try {
      const formData = new FormData()
      formData.append('file', selectedFile)
      formData.append('email', data.email)
      formData.append('phone', data.phone)
      formData.append('location', data.location)
      const dto = await resumesApi.uploadFile(formData)
      router.push(`/resumes/${dto.resume_id}`)
    } catch (err) {
      setServerError(err instanceof ApiClientError ? err.detail : 'Something went wrong.')
    } finally {
      setIsUploading(false)
    }
  }

  return (
    <Card className="max-w-2xl">
      <CardHeader>
        <CardTitle>New resume</CardTitle>
        <CardDescription>Add a resume by uploading a PDF or pasting the text directly</CardDescription>
      </CardHeader>
      <CardContent className="space-y-5">
        {/* Mode toggle */}
        <div className="inline-flex rounded-lg border p-1 gap-1">
          <button
            type="button"
            onClick={() => { setMode('text'); setServerError('') }}
            className={cn(
              'flex items-center gap-1.5 rounded-md px-3 py-1.5 text-sm font-medium transition-colors',
              mode === 'text' ? 'bg-primary text-primary-foreground' : 'text-muted-foreground hover:text-foreground',
            )}
          >
            <FileText size={14} />
            Paste text
          </button>
          <button
            type="button"
            onClick={() => { setMode('pdf'); setServerError('') }}
            className={cn(
              'flex items-center gap-1.5 rounded-md px-3 py-1.5 text-sm font-medium transition-colors',
              mode === 'pdf' ? 'bg-primary text-primary-foreground' : 'text-muted-foreground hover:text-foreground',
            )}
          >
            <Upload size={14} />
            Upload PDF
          </button>
        </div>

        {/* Text mode */}
        {mode === 'text' && (
          <form onSubmit={textForm.handleSubmit(onTextSubmit)} className="space-y-5">
            <div className="space-y-1.5">
              <Label htmlFor="raw_text">Resume text</Label>
              <Textarea
                id="raw_text"
                {...textForm.register('raw_text')}
                rows={10}
                placeholder="Paste your full resume content here…"
                className="resize-y"
              />
              {textForm.formState.errors.raw_text && (
                <p className="text-sm text-destructive">{textForm.formState.errors.raw_text.message}</p>
              )}
            </div>

            <div className="grid grid-cols-2 gap-4">
              <div className="space-y-1.5">
                <Label htmlFor="email-text">Email</Label>
                <Input id="email-text" type="email" {...textForm.register('email')} />
                {textForm.formState.errors.email && (
                  <p className="text-sm text-destructive">{textForm.formState.errors.email.message}</p>
                )}
              </div>
              <div className="space-y-1.5">
                <Label htmlFor="phone-text">Phone</Label>
                <Input id="phone-text" type="tel" {...textForm.register('phone')} />
                {textForm.formState.errors.phone && (
                  <p className="text-sm text-destructive">{textForm.formState.errors.phone.message}</p>
                )}
              </div>
            </div>

            <div className="space-y-1.5">
              <Label htmlFor="location-text">Location</Label>
              <Input id="location-text" {...textForm.register('location')} placeholder="City, Country" />
              {textForm.formState.errors.location && (
                <p className="text-sm text-destructive">{textForm.formState.errors.location.message}</p>
              )}
            </div>

            {serverError && <p className="text-sm text-destructive">{serverError}</p>}

            <div className="flex gap-3">
              <Button type="submit" disabled={textForm.formState.isSubmitting}>
                {textForm.formState.isSubmitting ? 'Creating…' : 'Create resume'}
              </Button>
              <Button type="button" variant="outline" onClick={() => router.back()}>
                Cancel
              </Button>
            </div>
          </form>
        )}

        {/* PDF mode */}
        {mode === 'pdf' && (
          <form onSubmit={contactForm.handleSubmit(onPdfSubmit)} className="space-y-5">
            <div className="space-y-1.5">
              <Label>PDF file</Label>
              <div
                onClick={() => fileInputRef.current?.click()}
                className={cn(
                  'flex cursor-pointer flex-col items-center justify-center gap-2 rounded-lg border-2 border-dashed px-6 py-10 text-center transition-colors hover:border-ring hover:bg-accent/30',
                  selectedFile && 'border-ring bg-accent/20',
                )}
              >
                <Upload size={24} className="text-muted-foreground" />
                {selectedFile ? (
                  <p className="text-sm font-medium">{selectedFile.name}</p>
                ) : (
                  <p className="text-sm text-muted-foreground">
                    Click to select a PDF <span className="text-xs">(max 5 MB)</span>
                  </p>
                )}
                <input
                  ref={fileInputRef}
                  type="file"
                  accept=".pdf,application/pdf"
                  className="hidden"
                  onChange={handleFileChange}
                />
              </div>
              {fileError && <p className="text-sm text-destructive">{fileError}</p>}
            </div>

            <div className="grid grid-cols-2 gap-4">
              <div className="space-y-1.5">
                <Label htmlFor="email-pdf">Email</Label>
                <Input id="email-pdf" type="email" {...contactForm.register('email')} />
                {contactForm.formState.errors.email && (
                  <p className="text-sm text-destructive">{contactForm.formState.errors.email.message}</p>
                )}
              </div>
              <div className="space-y-1.5">
                <Label htmlFor="phone-pdf">Phone</Label>
                <Input id="phone-pdf" type="tel" {...contactForm.register('phone')} />
                {contactForm.formState.errors.phone && (
                  <p className="text-sm text-destructive">{contactForm.formState.errors.phone.message}</p>
                )}
              </div>
            </div>

            <div className="space-y-1.5">
              <Label htmlFor="location-pdf">Location</Label>
              <Input id="location-pdf" {...contactForm.register('location')} placeholder="City, Country" />
              {contactForm.formState.errors.location && (
                <p className="text-sm text-destructive">{contactForm.formState.errors.location.message}</p>
              )}
            </div>

            {serverError && <p className="text-sm text-destructive">{serverError}</p>}

            <div className="flex gap-3">
              <Button type="submit" disabled={isUploading || !selectedFile}>
                {isUploading ? 'Uploading…' : 'Upload & analyze'}
              </Button>
              <Button type="button" variant="outline" onClick={() => router.back()}>
                Cancel
              </Button>
            </div>
          </form>
        )}
      </CardContent>
    </Card>
  )
}
