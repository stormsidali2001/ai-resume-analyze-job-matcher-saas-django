import { cookies } from 'next/headers'
import { NextRequest, NextResponse } from 'next/server'

const DJANGO = 'http://localhost:8000'

export async function POST(req: NextRequest) {
  const body = await req.json()

  const upstream = await fetch(`${DJANGO}/api/auth/register/`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(body),
  })

  if (!upstream.ok) {
    const err = await upstream.json()
    return NextResponse.json(err, { status: upstream.status })
  }

  const data = await upstream.json()
  const cookieStore = await cookies()
  const isProd = process.env.NODE_ENV === 'production'
  const base = { httpOnly: true, sameSite: 'lax' as const, secure: isProd, path: '/' }

  cookieStore.set('access_token', data.access, { ...base, maxAge: 60 * 60 })
  cookieStore.set('refresh_token', data.refresh, { ...base, maxAge: 60 * 60 * 24 * 7 })

  return NextResponse.json({ user: data.user })
}
