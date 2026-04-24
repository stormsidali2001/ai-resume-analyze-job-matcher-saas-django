import { cn } from '@/lib/utils'
import type { ChatMessage } from '@/types/api'
import { SourceCard } from './SourceCard'

interface MessageBubbleProps {
  message: ChatMessage
  isJobSource: boolean
  isLast: boolean
}

function StreamingCursor() {
  return (
    <span className="ml-0.5 inline-block w-0.5 h-4 bg-current align-middle animate-pulse" />
  )
}

export function MessageBubble({ message, isJobSource, isLast }: MessageBubbleProps) {
  const isUser = message.role === 'user'

  return (
    <div className={cn('flex flex-col gap-2', isUser ? 'items-end' : 'items-start')}>
      <div
        className={cn(
          'max-w-[75%] rounded-2xl px-4 py-2.5 text-sm leading-relaxed',
          isUser
            ? 'bg-primary text-primary-foreground rounded-br-sm'
            : message.isError
              ? 'bg-destructive/10 text-destructive border border-destructive/20 rounded-bl-sm'
              : 'bg-muted text-foreground rounded-bl-sm',
        )}
      >
        {message.content
          ? message.content.split('\n').map((line, i) => (
              <span key={i}>
                {line}
                {i < message.content.split('\n').length - 1 && <br />}
              </span>
            ))
          : !message.isStreaming && <span className="text-muted-foreground italic">…</span>}
        {message.isStreaming && isLast && <StreamingCursor />}
      </div>

      {/* Source cards shown after streaming completes */}
      {!isUser && !message.isStreaming && message.sources && message.sources.length > 0 && (
        <div className="max-w-[85%] w-full space-y-1.5">
          <p className="text-xs text-muted-foreground px-1">Sources</p>
          <div className="grid grid-cols-1 gap-1.5 sm:grid-cols-2">
            {message.sources.map((source, i) => (
              <SourceCard key={source.id || i} source={source} index={i} isJobSource={isJobSource} />
            ))}
          </div>
        </div>
      )}
    </div>
  )
}
