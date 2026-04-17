'use client'

import { useState } from 'react'
import { useForm } from 'react-hook-form'
import { zodResolver } from '@hookform/resolvers/zod'
import { z } from 'zod'
import { useRouter } from 'next/navigation'
import { useQueryClient } from '@tanstack/react-query'
import Link from 'next/link'
import { FileText, Briefcase } from 'lucide-react'
import { Button } from '@/components/ui/button'
import { Input } from '@/components/ui/input'
import { Label } from '@/components/ui/label'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
import { Separator } from '@/components/ui/separator'
import { authApi } from '@/lib/api/auth'
import { ApiClientError } from '@/lib/api/client'

const loginSchema = z.object({
  username: z.string().min(1, 'Username is required'),
  password: z.string().min(1, 'Password is required'),
})

type LoginFormValues = z.infer<typeof loginSchema>

const DEMO_ACCOUNTS = [
  {
    username: 'demo_candidate',
    password: 'demo1234',
    label: 'Candidate',
    description: 'Resume, skills & job matching',
    icon: FileText,
    redirectTo: '/resumes',
    color: 'text-indigo-600 dark:text-indigo-400',
    bg: 'bg-indigo-50 dark:bg-indigo-950/40',
    border: 'border-indigo-200 dark:border-indigo-800',
    hover: 'hover:border-indigo-400 dark:hover:border-indigo-600 hover:bg-indigo-100 dark:hover:bg-indigo-950/60',
  },
  {
    username: 'demo_recruiter',
    password: 'demo1234',
    label: 'Recruiter',
    description: 'Job postings & candidates',
    icon: Briefcase,
    redirectTo: '/recruiter/jobs',
    color: 'text-amber-600 dark:text-amber-400',
    bg: 'bg-amber-50 dark:bg-amber-950/40',
    border: 'border-amber-200 dark:border-amber-800',
    hover: 'hover:border-amber-400 dark:hover:border-amber-600 hover:bg-amber-100 dark:hover:bg-amber-950/60',
  },
] as const

export function LoginForm() {
  const router = useRouter()
  const queryClient = useQueryClient()
  const [serverError, setServerError] = useState('')
  const [demoLoading, setDemoLoading] = useState<string | null>(null)

  const {
    register,
    handleSubmit,
    formState: { errors, isSubmitting },
  } = useForm<LoginFormValues>({ resolver: zodResolver(loginSchema) })

  const onSubmit = async (data: LoginFormValues) => {
    setServerError('')
    try {
      await authApi.login(data.username, data.password)
      queryClient.clear()
      router.push('/resumes')
    } catch (err) {
      if (err instanceof ApiClientError) {
        setServerError(err.detail)
      } else {
        setServerError('Something went wrong. Please try again.')
      }
    }
  }

  const loginAsDemo = async (account: typeof DEMO_ACCOUNTS[number]) => {
    setServerError('')
    setDemoLoading(account.username)
    try {
      await authApi.login(account.username, account.password)
      queryClient.clear()
      router.push(account.redirectTo)
    } catch {
      setServerError(`Demo account unavailable. Run "python manage.py seed" first.`)
    } finally {
      setDemoLoading(null)
    }
  }

  return (
    <Card className="w-full max-w-sm">
      <CardHeader>
        <CardTitle>Sign in</CardTitle>
        <CardDescription>Enter your credentials to access your account</CardDescription>
      </CardHeader>
      <CardContent className="space-y-5">
        {/* Demo accounts */}
        <div className="space-y-2">
          <p className="text-xs font-medium text-muted-foreground uppercase tracking-wider">
            Try a demo account
          </p>
          <div className="grid grid-cols-2 gap-2">
            {DEMO_ACCOUNTS.map((account) => {
              const Icon = account.icon
              const isLoading = demoLoading === account.username
              return (
                <button
                  key={account.username}
                  type="button"
                  onClick={() => loginAsDemo(account)}
                  disabled={isLoading || demoLoading !== null}
                  className={[
                    'flex flex-col items-start gap-1.5 rounded-lg border p-3 text-left',
                    'transition-all duration-150 disabled:opacity-60 disabled:cursor-not-allowed',
                    account.bg,
                    account.border,
                    account.hover,
                  ].join(' ')}
                >
                  <div className={['flex items-center gap-1.5 font-medium text-sm', account.color].join(' ')}>
                    <Icon size={13} />
                    {isLoading ? 'Signing in…' : account.label}
                  </div>
                  <span className="text-xs text-muted-foreground leading-snug">
                    {account.description}
                  </span>
                </button>
              )
            })}
          </div>
        </div>

        <div className="flex items-center gap-3">
          <Separator className="flex-1" />
          <span className="text-xs text-muted-foreground">or sign in manually</span>
          <Separator className="flex-1" />
        </div>

        {/* Manual login form */}
        <form onSubmit={handleSubmit(onSubmit)} className="space-y-4">
          <div className="space-y-1.5">
            <Label htmlFor="username">Username</Label>
            <Input id="username" {...register('username')} autoComplete="username" />
            {errors.username && (
              <p className="text-sm text-destructive">{errors.username.message}</p>
            )}
          </div>

          <div className="space-y-1.5">
            <Label htmlFor="password">Password</Label>
            <Input
              id="password"
              type="password"
              {...register('password')}
              autoComplete="current-password"
            />
            {errors.password && (
              <p className="text-sm text-destructive">{errors.password.message}</p>
            )}
          </div>

          {serverError && <p className="text-sm text-destructive">{serverError}</p>}

          <Button type="submit" className="w-full" disabled={isSubmitting || demoLoading !== null}>
            {isSubmitting ? 'Signing in…' : 'Sign in'}
          </Button>
        </form>

        <p className="text-center text-sm text-muted-foreground">
          Don&apos;t have an account?{' '}
          <Link href="/register" className="underline underline-offset-4 hover:text-foreground">
            Register
          </Link>
        </p>
      </CardContent>
    </Card>
  )
}
