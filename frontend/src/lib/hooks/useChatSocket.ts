'use client'

import { useCallback, useRef, useState } from 'react'
import type { ChatMessage, ChatSource } from '@/types/api'

const WS_BASE = process.env.NEXT_PUBLIC_DJANGO_WS_URL ?? 'ws://localhost:8000'

async function fetchAccessToken(): Promise<string | null> {
  try {
    const res = await fetch('/api/auth/ws-token')
    if (!res.ok) return null
    const { token } = (await res.json()) as { token: string | null }
    return token ?? null
  } catch {
    return null
  }
}

function makeId() {
  return Math.random().toString(36).slice(2)
}

export interface UseChatSocketReturn {
  messages: ChatMessage[]
  isStreaming: boolean
  isConnected: boolean
  connect: () => Promise<void>
  disconnect: () => void
  sendMessage: (text: string) => void
}

export function useChatSocket(): UseChatSocketReturn {
  const [messages, setMessages] = useState<ChatMessage[]>([])
  const [isStreaming, setIsStreaming] = useState(false)
  const [isConnected, setIsConnected] = useState(false)
  const wsRef = useRef<WebSocket | null>(null)
  // Track the ID of the assistant message currently being streamed
  const streamingIdRef = useRef<string | null>(null)

  const disconnect = useCallback(() => {
    const ws = wsRef.current
    if (ws && (ws.readyState === WebSocket.OPEN || ws.readyState === WebSocket.CONNECTING)) {
      ws.close()
    }
    wsRef.current = null
    setIsConnected(false)
  }, [])

  const connect = useCallback(async () => {
    if (wsRef.current?.readyState === WebSocket.OPEN) return

    const token = await fetchAccessToken()
    if (!token) return

    const ws = new WebSocket(`${WS_BASE}/ws/chat/?token=${token}`)
    wsRef.current = ws

    ws.onopen = () => setIsConnected(true)

    ws.onmessage = (event: MessageEvent) => {
      let data: { type: string; content?: string; sources?: ChatSource[]; message?: string }
      try {
        data = JSON.parse(event.data as string)
      } catch {
        return
      }

      if (data.type === 'chunk' && data.content) {
        setMessages((prev) => {
          const streamId = streamingIdRef.current
          if (!streamId) return prev
          return prev.map((m) =>
            m.id === streamId
              ? { ...m, content: m.content + data.content!, isStreaming: true }
              : m
          )
        })
      } else if (data.type === 'done') {
        setMessages((prev) => {
          const streamId = streamingIdRef.current
          if (!streamId) return prev
          return prev.map((m) =>
            m.id === streamId
              ? { ...m, sources: data.sources ?? [], isStreaming: false }
              : m
          )
        })
        streamingIdRef.current = null
        setIsStreaming(false)
      } else if (data.type === 'error') {
        const errorText = data.message ?? 'An error occurred. Please try again.'
        setMessages((prev) => {
          const streamId = streamingIdRef.current
          if (streamId) {
            // Update the in-flight assistant bubble
            return prev.map((m) =>
              m.id === streamId
                ? { ...m, content: errorText, isStreaming: false, isError: true }
                : m
            )
          }
          // No streaming message — append a standalone error bubble
          return [
            ...prev,
            { id: makeId(), role: 'assistant' as const, content: errorText, isError: true },
          ]
        })
        streamingIdRef.current = null
        setIsStreaming(false)
      }
    }

    ws.onerror = () => ws.close()
    ws.onclose = () => {
      setIsConnected(false)
      wsRef.current = null
      // If the connection closed while a response was streaming, mark it as an error
      // so the cursor doesn't spin forever.
      const streamId = streamingIdRef.current
      if (streamId) {
        setMessages((prev) =>
          prev.map((m) =>
            m.id === streamId
              ? { ...m, content: m.content || 'Connection closed unexpectedly.', isStreaming: false, isError: !m.content }
              : m
          )
        )
        streamingIdRef.current = null
        setIsStreaming(false)
      }
    }
  }, [])

  const sendMessage = useCallback(
    (text: string) => {
      const ws = wsRef.current
      if (!ws || ws.readyState !== WebSocket.OPEN || isStreaming) return

      // Add user message
      const userMsg: ChatMessage = { id: makeId(), role: 'user', content: text }
      // Add empty assistant message as streaming placeholder
      const assistantId = makeId()
      const assistantMsg: ChatMessage = {
        id: assistantId,
        role: 'assistant',
        content: '',
        isStreaming: true,
      }
      streamingIdRef.current = assistantId
      setIsStreaming(true)
      setMessages((prev) => [...prev, userMsg, assistantMsg])

      ws.send(JSON.stringify({ message: text }))
    },
    [isStreaming]
  )

  return { messages, isStreaming, isConnected, connect, disconnect, sendMessage }
}
