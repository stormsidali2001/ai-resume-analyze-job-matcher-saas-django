'use client'

import { useEffect } from 'react'
import { useQueryClient } from '@tanstack/react-query'
import { resumeKeys } from './useResumes'
import type { ResumeDTO } from '@/types/api'

const WS_BASE = process.env.NEXT_PUBLIC_DJANGO_WS_URL ?? 'ws://localhost:8000'

/**
 * Fetch the JWT access token from the server-side API route.
 *
 * The access_token cookie is HttpOnly — document.cookie cannot read it.
 * /api/auth/ws-token reads it server-side and returns it as JSON so the
 * client can attach it to the WebSocket URL as a query parameter.
 */
async function fetchAccessToken(): Promise<string | null> {
  try {
    const res = await fetch('/api/auth/ws-token')
    if (!res.ok) return null
    const { token } = await res.json() as { token: string | null }
    return token ?? null
  } catch {
    return null
  }
}

/**
 * Opens a WebSocket to Django Channels for the given resume and keeps the
 * React Query cache in sync with analysis_status transitions pushed by the
 * Celery worker.
 *
 * @param resumeId - UUID of the resume to watch
 * @param enabled  - Only connect while analysis is actually in flight.
 *                   Pass `false` when the resume is already done/idle so we
 *                   don't hold an unnecessary connection open.
 *
 * Lifecycle:
 *   connect → receive "processing" → patch cache optimistically
 *          → receive "done"|"failed" → invalidate full detail + list → close WS
 */
export function useResumeStatusSocket(resumeId: string, enabled: boolean) {
  const qc = useQueryClient()

  useEffect(() => {
    if (!enabled || !resumeId) return

    let ws: WebSocket | null = null
    let cancelled = false

    fetchAccessToken().then((token) => {
      if (!token || cancelled) return

      ws = new WebSocket(`${WS_BASE}/ws/resume/${resumeId}/?token=${token}`)

      ws.onopen = () => {
        // Guard against race condition: if the Celery task completed before
        // the WebSocket connected, we missed the broadcast. Refetch once on
        // open so we catch an already-terminal status.
        qc.invalidateQueries({ queryKey: resumeKeys.detail(resumeId) })
      }

      ws.onmessage = (event: MessageEvent) => {
        let data: { type: string; analysis_status: string; resume_id: string }
        try {
          data = JSON.parse(event.data as string)
        } catch {
          return
        }

        if (data.type !== 'status_update') return

        const { analysis_status } = data

        // Optimistically patch the cached status so the banner updates immediately
        // without waiting for a full refetch round-trip.
        qc.setQueryData<ResumeDTO>(resumeKeys.detail(resumeId), (old) =>
          old ? { ...old, analysis_status: analysis_status as ResumeDTO['analysis_status'] } : old
        )

        if (analysis_status === 'done' || analysis_status === 'failed') {
          // Refetch the full resume — skills/experiences/education are now populated
          qc.invalidateQueries({ queryKey: resumeKeys.detail(resumeId) })
          // Refresh the list so the card's "Analyzing…" pill disappears
          qc.invalidateQueries({ queryKey: resumeKeys.all })
          ws?.close()
        }
      }

      ws.onerror = () => ws?.close()
    })

    return () => {
      cancelled = true
      if (ws && (ws.readyState === WebSocket.OPEN || ws.readyState === WebSocket.CONNECTING)) {
        ws.close()
      }
    }
  }, [resumeId, enabled, qc])
}
