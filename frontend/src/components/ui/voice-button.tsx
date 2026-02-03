"use client"

import * as React from "react"
import { Mic, Loader2, Check, X } from "lucide-react"
import { cn } from "@/lib/utils"
import { LiveWaveform } from "./live-waveform"

export type VoiceButtonState =
  | "idle"
  | "recording"
  | "processing"
  | "success"
  | "error"

export interface VoiceButtonProps
  extends Omit<React.ButtonHTMLAttributes<HTMLButtonElement>, "children"> {
  state?: VoiceButtonState
  onPressStart?: () => void
  onPressEnd?: () => void
  onPress?: () => void
  label?: React.ReactNode
  trailing?: React.ReactNode
  icon?: React.ReactNode
  variant?: "default" | "destructive" | "outline" | "secondary" | "ghost" | "link"
  size?: "default" | "sm" | "lg" | "icon"
  waveformClassName?: string
  feedbackDuration?: number
  pushToTalk?: boolean
}

export function VoiceButton({
  state = "idle",
  onPressStart,
  onPressEnd,
  onPress,
  label,
  trailing,
  icon,
  variant = "outline",
  size = "default",
  className,
  waveformClassName,
  feedbackDuration = 1500,
  disabled,
  pushToTalk = false,
  ...props
}: VoiceButtonProps) {
  const isIconOnly = size === "icon"
  const showWaveform = state === "recording"
  const isProcessing = state === "processing"
  const isSuccess = state === "success"
  const isError = state === "error"
  const isIdle = state === "idle"
  const isRecording = state === "recording"

  const getIcon = () => {
    if (isSuccess) return <Check className="h-5 w-5" />
    if (isError) return <X className="h-5 w-5" />
    if (isProcessing) return <Loader2 className="h-5 w-5 animate-spin" />
    if (icon) return icon
    return <Mic className="h-5 w-5" />
  }

  const getLabel = () => {
    if (isSuccess) return "Terminé"
    if (isError) return "Erreur"
    if (isProcessing) return "Traitement..."
    if (isRecording) return "Relâchez pour envoyer"
    return label || "Maintenez pour parler"
  }

  const sizeClasses = {
    default: "h-12 px-4 py-2",
    sm: "h-9 px-3 py-1.5",
    lg: "h-14 px-6 py-3",
    icon: "h-12 w-12",
  }

  const variantClasses = {
    default: "bg-white text-black hover:bg-neutral-200",
    destructive: "bg-red-500 text-white hover:bg-red-600",
    outline: "border border-neutral-700 bg-transparent hover:bg-neutral-800 hover:border-neutral-600",
    secondary: "bg-neutral-800 text-white hover:bg-neutral-700",
    ghost: "hover:bg-neutral-800",
    link: "text-white underline-offset-4 hover:underline",
  }

  const handleMouseDown = () => {
    if (pushToTalk && onPressStart && isIdle) {
      onPressStart()
    }
  }

  const handleMouseUp = () => {
    if (pushToTalk && onPressEnd && isRecording) {
      onPressEnd()
    }
  }

  const handleClick = () => {
    if (!pushToTalk && onPress) {
      onPress()
    }
  }

  return (
    <button
      type="button"
      onClick={handleClick}
      onMouseDown={handleMouseDown}
      onMouseUp={handleMouseUp}
      onMouseLeave={handleMouseUp}
      onTouchStart={handleMouseDown}
      onTouchEnd={handleMouseUp}
      disabled={disabled || isProcessing}
      className={cn(
        "relative inline-flex items-center justify-center gap-3 rounded-lg font-medium transition-all focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-white focus-visible:ring-offset-2 focus-visible:ring-offset-black disabled:pointer-events-none disabled:opacity-50 select-none",
        sizeClasses[size],
        variantClasses[variant],
        isRecording && "border-white bg-white/10 scale-[1.02]",
        isSuccess && "border-green-500/50 bg-green-500/10",
        isError && "border-red-500/50 bg-red-500/10",
        className
      )}
      {...props}
    >
      {isIconOnly ? (
        <div
          className={cn(
            "flex h-10 w-10 items-center justify-center rounded-full transition-all",
            isIdle && "bg-neutral-800",
            isRecording && "bg-white text-black",
            isProcessing && "bg-neutral-700",
            isSuccess && "bg-green-500/20 text-green-500",
            isError && "bg-red-500/20 text-red-500"
          )}
        >
          {getIcon()}
        </div>
      ) : (
        <>
          {/* Icon container */}
          <div
            className={cn(
              "flex h-10 w-10 flex-shrink-0 items-center justify-center rounded-full transition-all",
              isIdle && "bg-neutral-800",
              isRecording && "bg-white text-black",
              isProcessing && "bg-neutral-700",
              isSuccess && "bg-green-500/20 text-green-500",
              isError && "bg-red-500/20 text-red-500"
            )}
          >
            {getIcon()}
          </div>

          {/* Content area */}
          <div className="flex flex-1 items-center justify-between gap-2 min-w-0">
            {/* Label or Waveform */}
            <div className="flex-1 text-left min-w-0">
              {showWaveform ? (
                <LiveWaveform
                  isActive={isRecording}
                  barCount={24}
                  barWidth={2}
                  barGap={2}
                  minHeight={4}
                  maxHeight={20}
                  className={cn("h-6", waveformClassName)}
                />
              ) : (
                <span className={cn(
                  "block truncate text-sm",
                  isIdle && "text-neutral-300",
                  isRecording && "text-white",
                  isProcessing && "text-neutral-400",
                  isSuccess && "text-green-400",
                  isError && "text-red-400"
                )}>
                  {getLabel()}
                </span>
              )}
            </div>

            {/* Trailing content */}
            {trailing && !showWaveform && (
              <span className="flex-shrink-0 text-xs text-neutral-500 font-mono">
                {trailing}
              </span>
            )}
          </div>
        </>
      )}
    </button>
  )
}
