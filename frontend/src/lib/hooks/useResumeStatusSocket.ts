'use client'

import { useEffect } from 'react'
import { useQueryClient } from '@tanstack/react-query'
import { resumeKeys } from './useResumes'
import type { ResumeDTO } from '@/types/api'

const WS_BASE = process.env.NEXT_PUBLIC_DJANGO_WS_URL ?? 'ws://localhost:8000'

/** Read the JWT access token from the browser cookie set at login. */
function getAccessToken(): string | null {
  if (typeof document === 'undefined') return null
  const match = document.cookie.match(/(?:^|; )access_token=([^;]*)/)
  return match ? decodeURIComponent(match[1]) : null
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

    const token = getAccessToken()
    if (!token) return

    const ws = new WebSocket(`${WS_BASE}/ws/resume/${resumeId}/?token=${token}`)

    ws.onopen = () => {
      // Connection established — nothing to send, server-push only
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
        ws.close()
      }
    }

    ws.onerror = () => ws.close()

    return () => {
      if (ws.readyState === WebSocket.OPEN || ws.readyState === WebSocket.CONNECTING) {
        ws.close()
      }
    }
  }, [resumeId, enabled, qc])
}
