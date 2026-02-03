"use client"

import * as React from "react"
import { cn } from "@/lib/utils"

export interface LiveWaveformProps extends React.HTMLAttributes<HTMLDivElement> {
  isActive?: boolean
  barCount?: number
  barWidth?: number
  barGap?: number
  minHeight?: number
  maxHeight?: number
}

export function LiveWaveform({
  isActive = false,
  barCount = 32,
  barWidth = 2,
  barGap = 2,
  minHeight = 4,
  maxHeight = 24,
  className,
  ...props
}: LiveWaveformProps) {
  const [heights, setHeights] = React.useState<number[]>(
    Array(barCount).fill(minHeight)
  )
  const animationRef = React.useRef<number>()
  const analyserRef = React.useRef<AnalyserNode | null>(null)
  const streamRef = React.useRef<MediaStream | null>(null)

  React.useEffect(() => {
    if (!isActive) {
      setHeights(Array(barCount).fill(minHeight))
      if (streamRef.current) {
        streamRef.current.getTracks().forEach(track => track.stop())
        streamRef.current = null
      }
      if (animationRef.current) {
        cancelAnimationFrame(animationRef.current)
      }
      return
    }

    const setupAudio = async () => {
      try {
        const stream = await navigator.mediaDevices.getUserMedia({ audio: true })
        streamRef.current = stream
        
        const audioContext = new AudioContext()
        const analyser = audioContext.createAnalyser()
        const source = audioContext.createMediaStreamSource(stream)
        
        analyser.fftSize = 64
        analyser.smoothingTimeConstant = 0.8
        source.connect(analyser)
        analyserRef.current = analyser

        const dataArray = new Uint8Array(analyser.frequencyBinCount)

        const animate = () => {
          if (!analyserRef.current) return
          
          analyserRef.current.getByteFrequencyData(dataArray)
          
          const newHeights = Array(barCount).fill(0).map((_, i) => {
            const index = Math.floor((i / barCount) * dataArray.length)
            const value = dataArray[index] || 0
            const normalized = value / 255
            return minHeight + normalized * (maxHeight - minHeight)
          })
          
          setHeights(newHeights)
          animationRef.current = requestAnimationFrame(animate)
        }

        animate()
      } catch (error) {
        console.error("Error accessing microphone:", error)
      }
    }

    setupAudio()

    return () => {
      if (animationRef.current) {
        cancelAnimationFrame(animationRef.current)
      }
      if (streamRef.current) {
        streamRef.current.getTracks().forEach(track => track.stop())
      }
    }
  }, [isActive, barCount, minHeight, maxHeight])

  return (
    <div
      className={cn(
        "flex items-center justify-center",
        className
      )}
      style={{ gap: `${barGap}px` }}
      {...props}
    >
      {heights.map((height, index) => (
        <div
          key={index}
          className={cn(
            "rounded-full transition-all duration-75",
            isActive ? "bg-white" : "bg-neutral-600"
          )}
          style={{
            width: `${barWidth}px`,
            height: `${height}px`,
          }}
        />
      ))}
    </div>
  )
}
