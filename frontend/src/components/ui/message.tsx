"use client"

import * as React from "react"
import { Mic, Bot, CheckCircle2, AlertCircle, Clock, Zap, AlertTriangle, Info } from "lucide-react"
import { cn } from "@/lib/utils"
import { Badge } from "@/components/ui/badge"
import { TypingTranscription, SimpleTyping } from "@/components/ui/typing-transcription"

export type MessageType = "user" | "system" | "notification" | "ticket"

interface Word {
  word: string
  confidence: number
  boosted: boolean
}

interface BaseMessageProps {
  timestamp?: Date
  className?: string
}

interface UserMessageProps extends BaseMessageProps {
  type: "user"
  content: string
  words?: Word[]
  isTyping?: boolean
}

interface SystemMessageProps extends BaseMessageProps {
  type: "system"
  content: string
  status?: "processing" | "success" | "error"
}

interface NotificationMessageProps extends BaseMessageProps {
  type: "notification"
  title: string
  description?: string
  variant?: "default" | "success" | "error"
}

interface TicketMessageProps extends BaseMessageProps {
  type: "ticket"
  ticketId: string
  objet: string
  reference: string
  gravite: number
  action: string
  photo?: string
}

export type MessageProps =
  | UserMessageProps
  | SystemMessageProps
  | NotificationMessageProps
  | TicketMessageProps

function formatTime(date: Date) {
  return new Intl.DateTimeFormat("fr-FR", {
    hour: "2-digit",
    minute: "2-digit",
  }).format(date)
}

function getGraviteConfig(gravite: number) {
  if (gravite >= 5) return { label: "Urgente", icon: Zap, color: "text-white" }
  if (gravite >= 4) return { label: "Critique", icon: AlertTriangle, color: "text-neutral-300" }
  if (gravite >= 3) return { label: "Élevée", icon: AlertCircle, color: "text-neutral-400" }
  return { label: gravite >= 2 ? "Modérée" : "Faible", icon: Info, color: "text-neutral-500" }
}

export function Message(props: MessageProps) {
  const { type, timestamp, className } = props

  if (type === "user") {
    const { content, words, isTyping } = props as UserMessageProps
    return (
      <div className={cn("flex items-start gap-3", className)}>
        <div className="flex h-8 w-8 flex-shrink-0 items-center justify-center rounded-full bg-white">
          <Mic className="h-4 w-4 text-black" />
        </div>
        <div className="flex-1 min-w-0">
          <div className="rounded-lg bg-neutral-800 px-4 py-3">
            {words && words.length > 0 && isTyping ? (
              <TypingTranscription words={words} typingSpeed={60} />
            ) : words && words.length > 0 ? (
              <p className="text-sm leading-relaxed whitespace-pre-wrap break-words">
                {words.map((word, index) => (
                  <span key={`${word.word}-${index}`}>
                    <span
                      className={cn(
                        word.boosted 
                          ? "text-green-400 bg-green-400/10 px-0.5 rounded" 
                          : "text-white"
                      )}
                    >
                      {word.word.trim()}
                    </span>
                    {index < words.length - 1 && " "}
                  </span>
                ))}
              </p>
            ) : isTyping ? (
              <SimpleTyping text={content} typingSpeed={25} />
            ) : (
              <p className="text-sm text-white leading-relaxed">{content}</p>
            )}
          </div>
          {/* Légende Word Boost */}
          {words && words.length > 0 && words.some(w => w.boosted) && (
            <div className="mt-1 flex items-center gap-2 text-xs">
              <span className="flex items-center gap-1">
                <span className="w-2 h-2 rounded-full bg-green-400" />
                <span className="text-neutral-500">Context Bias</span>
              </span>
            </div>
          )}
          {timestamp && (
            <p className="mt-1 text-xs text-neutral-600">{formatTime(timestamp)}</p>
          )}
        </div>
      </div>
    )
  }

  if (type === "system") {
    const { content, status } = props as SystemMessageProps
    return (
      <div className={cn("flex items-start gap-3", className)}>
        <div className={cn(
          "flex h-8 w-8 flex-shrink-0 items-center justify-center rounded-full",
          status === "processing" && "bg-neutral-700",
          status === "success" && "bg-green-500/20",
          status === "error" && "bg-red-500/20",
          !status && "bg-neutral-800"
        )}>
          {status === "processing" && <Clock className="h-4 w-4 text-neutral-400 animate-pulse" />}
          {status === "success" && <CheckCircle2 className="h-4 w-4 text-green-400" />}
          {status === "error" && <AlertCircle className="h-4 w-4 text-red-400" />}
          {!status && <Bot className="h-4 w-4 text-neutral-400" />}
        </div>
        <div className="flex-1 min-w-0">
          <div className="rounded-lg bg-neutral-900 border border-neutral-800 px-4 py-3">
            <p className={cn(
              "text-sm leading-relaxed",
              status === "processing" && "text-neutral-400",
              status === "success" && "text-green-400",
              status === "error" && "text-red-400",
              !status && "text-neutral-300"
            )}>
              {content}
            </p>
          </div>
          {timestamp && (
            <p className="mt-1 text-xs text-neutral-600">{formatTime(timestamp)}</p>
          )}
        </div>
      </div>
    )
  }

  if (type === "notification") {
    const { title, description, variant = "default" } = props as NotificationMessageProps
    return (
      <div className={cn("flex justify-center", className)}>
        <div className={cn(
          "inline-flex items-center gap-2 rounded-full px-4 py-2 text-xs",
          variant === "default" && "bg-neutral-800 text-neutral-400",
          variant === "success" && "bg-green-500/10 text-green-400 border border-green-500/20",
          variant === "error" && "bg-red-500/10 text-red-400 border border-red-500/20"
        )}>
          {variant === "success" && <CheckCircle2 className="h-3.5 w-3.5" />}
          {variant === "error" && <AlertCircle className="h-3.5 w-3.5" />}
          <span className="font-medium">{title}</span>
          {description && <span className="text-neutral-500">— {description}</span>}
        </div>
      </div>
    )
  }

  if (type === "ticket") {
    const { ticketId, objet, reference, gravite, action, photo } = props as TicketMessageProps
    const config = getGraviteConfig(gravite)
    const Icon = config.icon

    const getPriorityBg = (g: number) => {
      if (g >= 5) return "from-red-500/20 to-red-500/5 border-red-500/30"
      if (g >= 4) return "from-orange-500/20 to-orange-500/5 border-orange-500/30"
      if (g >= 3) return "from-yellow-500/20 to-yellow-500/5 border-yellow-500/30"
      return "from-green-500/20 to-green-500/5 border-green-500/30"
    }

    const getPriorityText = (g: number) => {
      if (g >= 5) return "text-red-400"
      if (g >= 4) return "text-orange-400"
      if (g >= 3) return "text-yellow-400"
      return "text-green-400"
    }

    return (
      <div className={cn("py-2", className)}>
        {/* Ticket Card */}
        <div className={cn(
          "rounded-xl border bg-gradient-to-b overflow-hidden",
          getPriorityBg(gravite)
        )}>
          {/* Header */}
          <div className="px-4 py-3 flex items-center justify-between">
            <div className="flex items-center gap-3">
              <div className={cn(
                "w-10 h-10 rounded-lg flex items-center justify-center",
                gravite >= 4 ? "bg-white/10" : "bg-white/5"
              )}>
                <Icon className={cn("w-5 h-5", getPriorityText(gravite))} />
              </div>
              <div>
                <p className="font-semibold text-white">{objet}</p>
                <p className="text-xs text-neutral-400 font-mono">{ticketId}</p>
              </div>
            </div>
            <div className={cn(
              "px-2.5 py-1 rounded-full text-xs font-medium border",
              getPriorityText(gravite),
              gravite >= 4 ? "bg-white/10 border-white/20" : "bg-white/5 border-white/10"
            )}>
              {config.label}
            </div>
          </div>
          
          {/* Divider */}
          <div className="h-px bg-white/10 mx-4" />
          
          {/* Body */}
          <div className="px-4 py-4 space-y-3">
            {/* Photo */}
            {photo && (
              <div className="rounded-lg overflow-hidden border border-white/10">
                <img src={photo} alt="Photo équipement" className="w-full max-h-40 object-cover" />
              </div>
            )}
            {/* Reference */}
            {reference && (
              <div className="flex items-center gap-2 text-sm">
                <span className="text-neutral-500">Réf:</span>
                <span className="font-mono text-white bg-white/5 px-2 py-0.5 rounded">{reference}</span>
              </div>
            )}
            
            {/* Action */}
            <div>
              <p className="text-xs text-neutral-500 uppercase tracking-wider mb-1.5">Action requise</p>
              <p className="text-sm text-neutral-200 leading-relaxed">{action}</p>
            </div>
            
            {/* Meta row */}
            <div className="flex items-center justify-between pt-2">
              <div className="flex items-center gap-4 text-xs text-neutral-500">
                {timestamp && (
                  <span className="flex items-center gap-1.5">
                    <Clock className="w-3.5 h-3.5" />
                    {new Intl.DateTimeFormat("fr-FR", {
                      hour: "2-digit",
                      minute: "2-digit"
                    }).format(timestamp)}
                  </span>
                )}
                <span className="flex items-center gap-1.5">
                  <span className={cn("w-1.5 h-1.5 rounded-full", 
                    gravite >= 5 ? "bg-red-500" :
                    gravite >= 4 ? "bg-orange-500" :
                    gravite >= 3 ? "bg-yellow-500" : "bg-green-500"
                  )} />
                  Priorité {gravite}/5
                </span>
              </div>
              <span className="text-xs px-2 py-0.5 rounded bg-green-500/20 text-green-400 font-medium">
                Nouveau
              </span>
            </div>
          </div>
          
          {/* Footer - Export Button */}
          <div className="px-4 py-3 bg-black/20">
            <button className="w-full bg-white hover:bg-neutral-100 text-black py-2.5 px-4 rounded-lg text-sm font-semibold transition-all flex items-center justify-center gap-2 shadow-lg">
              <svg className="w-4 h-4" viewBox="0 0 24 24" fill="none">
                <path d="M12 4L12 14M12 14L8 10M12 14L16 10" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"/>
                <path d="M4 17L4 18C4 19.1046 4.89543 20 6 20L18 20C19.1046 20 20 19.1046 20 18L20 17" stroke="currentColor" strokeWidth="2" strokeLinecap="round"/>
              </svg>
              Exporter dans SAP
            </button>
          </div>
        </div>
      </div>
    )
  }

  return null
}
