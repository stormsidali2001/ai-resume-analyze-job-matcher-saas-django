import { cookies } from 'next/headers'
import { NextResponse } from 'next/server'

const DJANGO = 'http://localhost:8000'

export async function GET() {
  const cookieStore = await cookies()
  const token = cookieStore.get('access_token')?.value

  if (!token) {
    return NextResponse.json({ detail: 'Not authenticated.' }, { status: 401 })
  }

  const upstream = await fetch(`${DJANGO}/api/auth/profile/`, {
    headers: { Authorization: `Bearer ${token}` },
  })

  const data = await upstream.json()
  return NextResponse.json(data, { status: upstream.status })
}
