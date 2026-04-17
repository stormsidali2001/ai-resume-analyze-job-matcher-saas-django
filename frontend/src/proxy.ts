import { NextResponse } from 'next/server'
import type { NextRequest } from 'next/server'

const PUBLIC_PATHS = ['/login', '/register']

export function proxy(request: NextRequest) {
  const { pathname } = request.nextUrl
  const token = request.cookies.get('access_token')?.value

  const isPublic = PUBLIC_PATHS.some((p) => pathname === p || pathname.startsWith(p + '/'))

  // No token → send to login
  if (!token && !isPublic) {
    const url = request.nextUrl.clone()
    url.pathname = '/login'
    return NextResponse.redirect(url)
  }

  // Already authenticated → don't show login/register
  if (token && isPublic) {
    const url = request.nextUrl.clone()
    url.pathname = '/resumes'
    return NextResponse.redirect(url)
  }

  return NextResponse.next()
}

export const config = {
  matcher: [
    '/((?!api|_next/static|_next/image|favicon.ico|sitemap.xml|robots.txt).*)',
  ],
}
