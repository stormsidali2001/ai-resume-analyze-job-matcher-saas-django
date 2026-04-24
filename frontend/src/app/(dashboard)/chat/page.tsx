'use client'

import { useEffect, useRef } from 'react'
import { MessageSquare } from 'lucide-react'
import { useCurrentUser } from '@/lib/hooks/useCurrentUser'
import { useChatSocket } from '@/lib/hooks/useChatSocket'
import { MessageBubble } from '@/components/chat/MessageBubble'
import { ChatInput } from '@/components/chat/ChatInput'

const CANDIDATE_PROMPTS = [
  'What Python engineering roles are available?',
  'Are there any remote full-stack positions?',
  'Which companies are hiring for data roles?',
]

const RECRUITER_PROMPTS = [
  'Find candidates with React and 3+ years of experience',
  'Who has PostgreSQL and cloud experience?',
  'Show me full-stack developers based in Europe',
]

export default function ChatPage() {
  const { data: user } = useCurrentUser()
  const { messages, isStreaming, isConnected, connect, sendMessage } = useChatSocket()
  const bottomRef = useRef<HTMLDivElement>(null)

  const isCandidate = user?.role !== 'recruiter'
  const title = isCandidate ? 'Job Search Assistant' : 'Talent Discovery'
  const subtitle = isCandidate
    ? 'Ask me about available job opportunities'
    : 'Ask me about candidate profiles'
  const suggestedPrompts = isCandidate ? CANDIDATE_PROMPTS : RECRUITER_PROMPTS

  useEffect(() => {
    connect()
  }, [connect])

  // Auto-scroll to bottom whenever messages change
  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: 'smooth' })
  }, [messages])

  const isEmpty = messages.length === 0

  return (
    <div className="flex h-full flex-col overflow-hidden">
      {/* Header */}
      <div className="shrink-0 border-b border-border px-4 py-3">
        <div className="flex items-center gap-2">
          <div className="flex size-8 items-center justify-center rounded-lg bg-primary/10">
            <MessageSquare size={16} className="text-primary" />
          </div>
          <div>
            <h1 className="text-sm font-semibold text-foreground">{title}</h1>
            <p className="text-xs text-muted-foreground">{subtitle}</p>
          </div>
          <div className="ml-auto flex items-center gap-1.5">
            <div
              className={`size-2 rounded-full ${isConnected ? 'bg-green-500' : 'bg-muted-foreground'}`}
            />
            <span className="text-xs text-muted-foreground">
              {isConnected ? 'Connected' : 'Connecting…'}
            </span>
          </div>
        </div>
      </div>

      {/* Messages */}
      <div className="flex-1 overflow-y-auto px-4 py-4">
        {isEmpty ? (
          <div className="flex h-full flex-col items-center justify-center gap-6 text-center">
            <div className="space-y-1">
              <h2 className="text-base font-medium text-foreground">How can I help you today?</h2>
              <p className="text-sm text-muted-foreground max-w-xs">{subtitle}</p>
            </div>
            <div className="flex flex-col gap-2 w-full max-w-sm">
              {suggestedPrompts.map((prompt) => (
                <button
                  key={prompt}
                  onClick={() => sendMessage(prompt)}
                  disabled={!isConnected || isStreaming}
                  className="rounded-xl border border-border bg-card px-4 py-2.5 text-left text-sm text-foreground hover:bg-muted transition-colors disabled:opacity-50"
                >
                  {prompt}
                </button>
              ))}
            </div>
          </div>
        ) : (
          <div className="space-y-4 max-w-2xl mx-auto">
            {messages.map((message, i) => (
              <MessageBubble
                key={message.id}
                message={message}
                isJobSource={isCandidate}
                isLast={i === messages.length - 1}
              />
            ))}
            <div ref={bottomRef} />
          </div>
        )}
      </div>

      {/* Input */}
      <div className="shrink-0 px-4 pb-4 pt-2 max-w-2xl mx-auto w-full">
        <ChatInput onSend={sendMessage} disabled={!isConnected || isStreaming} />
      </div>
    </div>
  )
}
