import { cn } from '@/lib/utils'
import { Mic, CheckCircle2, Sparkles } from 'lucide-react'

interface ChatBubbleProps {
  text: string
  type: 'user' | 'system' | 'transcription' | 'ticket'
  timestamp?: Date
  isProcessing?: boolean
}

export function ChatBubble({ text, type, timestamp, isProcessing }: ChatBubbleProps) {
  const formatTime = (date: Date) => {
    return new Intl.DateTimeFormat('fr-FR', {
      hour: '2-digit',
      minute: '2-digit'
    }).format(date)
  }

  if (type === 'user') {
    return (
      <div className="flex justify-end mb-4 animate-in slide-in-from-right">
        <div className="max-w-[80%]">
          <div className="bg-gradient-to-br from-indigo-500 to-purple-600 rounded-2xl rounded-br-md px-4 py-3 shadow-lg">
            <p className="text-sm text-white leading-relaxed">{text}</p>
          </div>
          {timestamp && (
            <p className="text-xs text-muted-foreground/60 mt-1 text-right">
              {formatTime(timestamp)}
            </p>
          )}
        </div>
      </div>
    )
  }

  if (type === 'system') {
    return (
      <div className="flex justify-center mb-4">
        <div className="flex items-center gap-2 px-3 py-1.5 rounded-full bg-muted/50 backdrop-blur-sm border border-border/50">
          {isProcessing ? (
            <Sparkles className="w-3.5 h-3.5 text-indigo-400 animate-pulse" />
          ) : (
            <CheckCircle2 className="w-3.5 h-3.5 text-green-400" />
          )}
          <p className="text-xs text-muted-foreground/80">{text}</p>
        </div>
      </div>
    )
  }

  if (type === 'transcription') {
    return (
      <div className="flex justify-start mb-4 animate-in slide-in-from-left">
        <div className="max-w-[80%]">
          <div className="bg-background/60 backdrop-blur-xl border border-border/50 rounded-2xl rounded-bl-md px-4 py-3 shadow-sm">
            <p className="text-sm text-foreground/90 leading-relaxed">{text}</p>
          </div>
          {timestamp && (
            <p className="text-xs text-muted-foreground/60 mt-1">
              {formatTime(timestamp)}
            </p>
          )}
        </div>
      </div>
    )
  }

  return null
}
