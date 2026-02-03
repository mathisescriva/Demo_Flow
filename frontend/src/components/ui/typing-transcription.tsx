"use client"

import * as React from "react"
import { cn } from "@/lib/utils"

interface Word {
  word: string
  confidence: number
  boosted: boolean
  start?: number
  end?: number
}

interface TypingTranscriptionProps {
  words: Word[]
  onComplete?: () => void
  typingSpeed?: number // ms per word
  className?: string
}

export function TypingTranscription({
  words,
  onComplete,
  typingSpeed = 80,
  className,
}: TypingTranscriptionProps) {
  const [visibleCount, setVisibleCount] = React.useState(0)
  const [isComplete, setIsComplete] = React.useState(false)

  React.useEffect(() => {
    if (visibleCount < words.length) {
      const timer = setTimeout(() => {
        setVisibleCount((prev) => prev + 1)
      }, typingSpeed)
      return () => clearTimeout(timer)
    } else if (!isComplete && words.length > 0) {
      setIsComplete(true)
      onComplete?.()
    }
  }, [visibleCount, words.length, typingSpeed, onComplete, isComplete])

  // Reset when words change
  React.useEffect(() => {
    setVisibleCount(0)
    setIsComplete(false)
  }, [words])

  const getWordColor = (word: Word) => {
    // Only highlight boosted words (Word Boost vocabulary)
    if (word.boosted) {
      return "text-green-400 bg-green-400/10 px-0.5 rounded"
    }
    // Normal words - white text
    return "text-white"
  }

  const visibleWords = words.slice(0, visibleCount)

  return (
    <p className={cn("text-sm leading-relaxed whitespace-pre-wrap break-words", className)}>
      {visibleWords.map((word, index) => (
        <span key={`${word.word}-${index}`}>
          <span
            className={cn(
              "transition-all duration-200",
              getWordColor(word),
              index === visibleCount - 1 && "animate-pulse"
            )}
          >
            {word.word.trim()}
          </span>
          {index < visibleCount - 1 && " "}
        </span>
      ))}
      {visibleCount < words.length && (
        <span className="inline-block w-0.5 h-4 bg-white animate-pulse ml-0.5 align-middle" />
      )}
    </p>
  )
}

// Simple text typing (for when we don't have word-level data)
interface SimpleTypingProps {
  text: string
  onComplete?: () => void
  typingSpeed?: number
  className?: string
}

export function SimpleTyping({
  text,
  onComplete,
  typingSpeed = 30,
  className,
}: SimpleTypingProps) {
  const [visibleLength, setVisibleLength] = React.useState(0)
  const [isComplete, setIsComplete] = React.useState(false)

  React.useEffect(() => {
    if (visibleLength < text.length) {
      const timer = setTimeout(() => {
        setVisibleLength((prev) => prev + 1)
      }, typingSpeed)
      return () => clearTimeout(timer)
    } else if (!isComplete && text.length > 0) {
      setIsComplete(true)
      onComplete?.()
    }
  }, [visibleLength, text.length, typingSpeed, onComplete, isComplete])

  React.useEffect(() => {
    setVisibleLength(0)
    setIsComplete(false)
  }, [text])

  return (
    <p className={cn("text-sm leading-relaxed text-white", className)}>
      {text.slice(0, visibleLength)}
      {visibleLength < text.length && (
        <span className="inline-block w-0.5 h-4 bg-white animate-pulse ml-0.5" />
      )}
    </p>
  )
}
