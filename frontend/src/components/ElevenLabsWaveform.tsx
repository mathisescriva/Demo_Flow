import { useEffect, useRef } from 'react'
import { cn } from '@/lib/utils'

interface ElevenLabsWaveformProps {
  audioData: number[]
  isActive: boolean
  className?: string
}

export function ElevenLabsWaveform({ audioData, isActive, className }: ElevenLabsWaveformProps) {
  const canvasRef = useRef<HTMLCanvasElement>(null)

  useEffect(() => {
    if (!canvasRef.current || !isActive) return

    const canvas = canvasRef.current
    const ctx = canvas.getContext('2d')
    if (!ctx) return

    const width = canvas.width
    const height = canvas.height
    const centerY = height / 2
    const barCount = audioData.length || 60
    const barWidth = width / barCount
    const maxAmplitude = height * 0.4

    // Clear canvas
    ctx.clearRect(0, 0, width, height)

    // Draw waveform
    audioData.forEach((value, i) => {
      const normalizedValue = value / 255
      const amplitude = normalizedValue * maxAmplitude
      const x = i * barWidth + barWidth / 2

      // Gradient colors
      const gradient = ctx.createLinearGradient(0, centerY - amplitude, 0, centerY + amplitude)
      gradient.addColorStop(0, 'rgba(99, 102, 241, 0.8)')
      gradient.addColorStop(0.5, 'rgba(139, 92, 246, 0.6)')
      gradient.addColorStop(1, 'rgba(99, 102, 241, 0.8)')

      ctx.fillStyle = gradient
      ctx.beginPath()
      const rectX = x - barWidth / 2 + 1
      const rectY = centerY - amplitude
      const rectW = barWidth - 2
      const rectH = amplitude * 2
      const radius = 2
      ctx.moveTo(rectX + radius, rectY)
      ctx.lineTo(rectX + rectW - radius, rectY)
      ctx.quadraticCurveTo(rectX + rectW, rectY, rectX + rectW, rectY + radius)
      ctx.lineTo(rectX + rectW, rectY + rectH - radius)
      ctx.quadraticCurveTo(rectX + rectW, rectY + rectH, rectX + rectW - radius, rectY + rectH)
      ctx.lineTo(rectX + radius, rectY + rectH)
      ctx.quadraticCurveTo(rectX, rectY + rectH, rectX, rectY + rectH - radius)
      ctx.lineTo(rectX, rectY + radius)
      ctx.quadraticCurveTo(rectX, rectY, rectX + radius, rectY)
      ctx.closePath()
      ctx.fill()
    })
  }, [audioData, isActive])

  if (!isActive) {
    return (
      <div className={cn("flex items-center justify-center h-20", className)}>
        <div className="flex items-center gap-1">
          {Array.from({ length: 20 }).map((_, i) => (
            <div
              key={i}
              className="w-1 bg-muted rounded-full"
              style={{
                height: '4px',
                animationDelay: `${i * 50}ms`,
              }}
            />
          ))}
        </div>
      </div>
    )
  }

  return (
    <div className={cn("relative h-20 overflow-hidden", className)}>
      <canvas
        ref={canvasRef}
        width={300}
        height={80}
        className="w-full h-full"
      />
    </div>
  )
}
