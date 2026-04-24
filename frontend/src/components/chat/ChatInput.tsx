'use client'

import { useRef, useState } from 'react'
import { Send } from 'lucide-react'
import { cn } from '@/lib/utils'

interface ChatInputProps {
  onSend: (message: string) => void
  disabled?: boolean
}

export function ChatInput({ onSend, disabled }: ChatInputProps) {
  const [value, setValue] = useState('')
  const textareaRef = useRef<HTMLTextAreaElement>(null)

  const submit = () => {
    const text = value.trim()
    if (!text || disabled) return
    onSend(text)
    setValue('')
    // Reset height
    if (textareaRef.current) {
      textareaRef.current.style.height = 'auto'
    }
  }

  return (
    <div className="flex items-end gap-2 rounded-2xl border border-border bg-background px-4 py-3 shadow-sm">
      <textarea
        ref={textareaRef}
        value={value}
        onChange={(e) => {
          setValue(e.target.value)
          // Auto-grow up to ~5 lines
          e.target.style.height = 'auto'
          e.target.style.height = `${Math.min(e.target.scrollHeight, 120)}px`
        }}
        onKeyDown={(e) => {
          if (e.key === 'Enter' && !e.shiftKey) {
            e.preventDefault()
            submit()
          }
        }}
        placeholder="Ask a question…"
        rows={1}
        disabled={disabled}
        className={cn(
          'flex-1 resize-none bg-transparent text-sm text-foreground placeholder:text-muted-foreground outline-none leading-relaxed',
          disabled && 'opacity-50 cursor-not-allowed',
        )}
      />
      <button
        onClick={submit}
        disabled={disabled || !value.trim()}
        className={cn(
          'flex size-8 shrink-0 items-center justify-center rounded-full bg-primary text-primary-foreground transition-opacity',
          (disabled || !value.trim()) && 'opacity-40 cursor-not-allowed',
        )}
      >
        <Send size={14} />
      </button>
    </div>
  )
}
