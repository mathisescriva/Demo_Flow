// Audio feedback hooks - subtle sounds
export function useAudioFeedback() {
  const audioContext = typeof window !== 'undefined' ? new (window.AudioContext || (window as any).webkitAudioContext)() : null

  const playTone = (frequency: number, duration: number, type: OscillatorType = 'sine', volume: number = 0.1) => {
    if (!audioContext) return
    
    const oscillator = audioContext.createOscillator()
    const gainNode = audioContext.createGain()
    
    oscillator.connect(gainNode)
    gainNode.connect(audioContext.destination)
    
    oscillator.frequency.value = frequency
    oscillator.type = type
    gainNode.gain.value = volume
    
    // Fade out
    gainNode.gain.exponentialRampToValueAtTime(0.001, audioContext.currentTime + duration)
    
    oscillator.start(audioContext.currentTime)
    oscillator.stop(audioContext.currentTime + duration)
  }

  const playStartRecording = () => {
    // Subtle high ping
    playTone(880, 0.1, 'sine', 0.08)
  }

  const playStopRecording = () => {
    // Double low ping
    playTone(440, 0.08, 'sine', 0.06)
    setTimeout(() => playTone(660, 0.1, 'sine', 0.06), 80)
  }

  const playSuccess = () => {
    // Pleasant success chime - more elaborate
    playTone(523, 0.12, 'sine', 0.1) // C5
    setTimeout(() => playTone(659, 0.12, 'sine', 0.1), 80) // E5
    setTimeout(() => playTone(784, 0.12, 'sine', 0.1), 160) // G5
    setTimeout(() => playTone(1047, 0.2, 'sine', 0.12), 240) // C6 - final note longer
  }

  const playError = () => {
    // Low buzz
    playTone(200, 0.2, 'triangle', 0.1)
  }

  return { playStartRecording, playStopRecording, playSuccess, playError }
}

// Local TTS - disabled (robotic voice)
// Just use sound feedback instead
export function useTTS() {
  // No TTS - just return empty functions
  // The audio feedback (playSuccess) is sufficient for the demo
  const speakTicketCreated = (_objet: string, _gravite: number) => {
    // Disabled - sounds are handled by useAudioFeedback
  }

  return { speak: () => {}, speakTicketCreated }
}
