import { useEffect, useRef, useState } from 'react'

export function useAudioVisualizer(stream: MediaStream | null) {
  const [audioData, setAudioData] = useState<number[]>([])
  const animationFrameRef = useRef<number>()
  const analyserRef = useRef<AnalyserNode | null>(null)
  const audioContextRef = useRef<AudioContext | null>(null)
  const smoothedDataRef = useRef<number[]>([])

  useEffect(() => {
    if (!stream) {
      setAudioData([])
      smoothedDataRef.current = []
      return
    }

    const audioContext = new AudioContext()
    const analyser = audioContext.createAnalyser()
    const microphone = audioContext.createMediaStreamSource(stream)
    
    analyser.fftSize = 512
    analyser.smoothingTimeConstant = 0.85
    analyser.minDecibels = -90
    analyser.maxDecibels = -10
    microphone.connect(analyser)
    
    analyserRef.current = analyser
    audioContextRef.current = audioContext

    const dataArray = new Uint8Array(analyser.frequencyBinCount)
    const barCount = 40
    smoothedDataRef.current = new Array(barCount).fill(0)

    const updateAudioData = () => {
      if (analyserRef.current) {
        analyserRef.current.getByteFrequencyData(dataArray)
        
        // Prendre les barCount premières fréquences et lisser
        const newData: number[] = []
        for (let i = 0; i < barCount; i++) {
          const index = Math.floor((i / barCount) * dataArray.length)
          const value = dataArray[index] || 0
          
          // Lissage exponentiel pour fluidité
          const smoothed = smoothedDataRef.current[i] || 0
          const newValue = smoothed * 0.7 + value * 0.3
          smoothedDataRef.current[i] = newValue
          newData.push(newValue)
        }
        
        setAudioData(newData)
        animationFrameRef.current = requestAnimationFrame(updateAudioData)
      }
    }

    updateAudioData()

    return () => {
      if (animationFrameRef.current) {
        cancelAnimationFrame(animationFrameRef.current)
      }
      if (audioContextRef.current) {
        audioContextRef.current.close()
      }
      smoothedDataRef.current = []
    }
  }, [stream])

  return audioData
}
