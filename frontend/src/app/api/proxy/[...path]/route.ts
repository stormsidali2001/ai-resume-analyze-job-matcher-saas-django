import { cookies } from 'next/headers'
import { NextRequest, NextResponse } from 'next/server'

const DJANGO_V1 = 'http://localhost:8000/api/v1'

async function forward(req: NextRequest, method: string) {
  const cookieStore = await cookies()
  const token = cookieStore.get('access_token')?.value

  if (!token) {
    return NextResponse.json({ detail: 'Not authenticated.' }, { status: 401 })
  }

  const url = new URL(req.url)
  // Strip the /api/proxy prefix to get the Django path
  const proxiedPath = url.pathname.replace(/^\/api\/proxy/, '')
  const proxiedPathWithSlash = proxiedPath.endsWith('/') ? proxiedPath : `${proxiedPath}/`
  const target = `${DJANGO_V1}${proxiedPathWithSlash}${url.search}`

  const headers: HeadersInit = {
    Authorization: `Bearer ${token}`,
    'Content-Type': 'application/json',
  }

  const body = ['GET', 'HEAD'].includes(method) ? undefined : await req.text()

  const upstream = await fetch(target, { method, headers, body, redirect: 'follow' })

  const text = await upstream.text()
  const contentType = upstream.headers.get('content-type') ?? 'application/json'

  return new NextResponse(text || null, {
    status: upstream.status,
    headers: { 'Content-Type': contentType },
  })
}


export const GET = (req: NextRequest) => forward(req, 'GET')
export const POST = (req: NextRequest) => forward(req, 'POST')
export const PATCH = (req: NextRequest) => forward(req, 'PATCH')
