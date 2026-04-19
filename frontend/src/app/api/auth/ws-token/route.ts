import { cookies } from 'next/headers'
import { NextResponse } from 'next/server'

/**
 * GET /api/auth/ws-token
 *
 * Returns the JWT access token so the client can attach it to a WebSocket
 * URL as a query parameter.  The access_token cookie is HttpOnly and cannot
 * be read by browser JS directly — this route bridges that gap.
 *
 * The token is only returned when it already exists (i.e. the user is
 * logged in).  It is never written or modified here.
 */
export async function GET() {
  const cookieStore = await cookies()
  const token = cookieStore.get('access_token')?.value

  if (!token) {
    return NextResponse.json({ token: null }, { status: 401 })
  }

  return NextResponse.json({ token })
}
