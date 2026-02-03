import { cn } from "@/lib/utils"

interface AudioVisualizerProps {
  audioData: number[]
  isActive: boolean
  className?: string
}

export function AudioVisualizer({ audioData, isActive, className }: AudioVisualizerProps) {
  if (!isActive || audioData.length === 0) {
    return null
  }

  const maxHeight = 80
  const minHeight = 4

  return (
    <div className={cn("flex items-end justify-center gap-0.5 h-24", className)}>
      {audioData.map((value, i) => {
        const normalizedValue = Math.min(value / 255, 1)
        const height = minHeight + (normalizedValue * (maxHeight - minHeight))
        
        return (
          <div
            key={i}
            className="w-1.5 rounded-full bg-gradient-to-t from-cyan-400 via-blue-500 to-cyan-400"
            style={{
              height: `${height}px`,
              transition: 'height 0.1s ease-out',
            }}
          />
        )
      })}
    </div>
  )
}
