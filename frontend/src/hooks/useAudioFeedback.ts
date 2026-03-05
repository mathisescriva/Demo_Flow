// Audio feedback hooks - subtle, modern sound design
export function useAudioFeedback() {
  const audioContextRef = { current: null as AudioContext | null }
  
  const getAudioContext = () => {
    if (typeof window === 'undefined') return null
    if (!audioContextRef.current) {
      audioContextRef.current = new (window.AudioContext || (window as any).webkitAudioContext)()
    }
    // Resume if suspended (browser autoplay policy)
    if (audioContextRef.current.state === 'suspended') {
      audioContextRef.current.resume()
    }
    return audioContextRef.current
  }

  // Enhanced tone with ADSR envelope and optional harmonics
  const playTone = (
    frequency: number, 
    duration: number, 
    type: OscillatorType = 'sine', 
    volume: number = 0.1,
    options: {
      attack?: number,
      decay?: number,
      sustain?: number,
      release?: number,
      detune?: number,
      harmonics?: number[]
    } = {}
  ) => {
    const audioContext = getAudioContext()
    if (!audioContext) return
    
    const { 
      attack = 0.01, 
      decay = 0.1, 
      sustain = 0.5, 
      release = duration * 0.5,
      detune = 0,
      harmonics = []
    } = options
    
    const now = audioContext.currentTime
    
    // Main oscillator
    const oscillator = audioContext.createOscillator()
    const gainNode = audioContext.createGain()
    
    oscillator.connect(gainNode)
    gainNode.connect(audioContext.destination)
    
    oscillator.frequency.value = frequency
    oscillator.type = type
    oscillator.detune.value = detune
    
    // ADSR envelope
    gainNode.gain.setValueAtTime(0, now)
    gainNode.gain.linearRampToValueAtTime(volume, now + attack) // Attack
    gainNode.gain.linearRampToValueAtTime(volume * sustain, now + attack + decay) // Decay
    gainNode.gain.setValueAtTime(volume * sustain, now + duration - release) // Sustain
    gainNode.gain.exponentialRampToValueAtTime(0.001, now + duration) // Release
    
    oscillator.start(now)
    oscillator.stop(now + duration)
    
    // Add harmonics for richer sound
    harmonics.forEach((harmonic, i) => {
      const harmOsc = audioContext.createOscillator()
      const harmGain = audioContext.createGain()
      
      harmOsc.connect(harmGain)
      harmGain.connect(audioContext.destination)
      
      harmOsc.frequency.value = frequency * harmonic
      harmOsc.type = type
      
      const harmVolume = volume * (0.3 / (i + 2)) // Decreasing volume for each harmonic
      harmGain.gain.setValueAtTime(0, now)
      harmGain.gain.linearRampToValueAtTime(harmVolume, now + attack)
      harmGain.gain.exponentialRampToValueAtTime(0.001, now + duration * 0.8)
      
      harmOsc.start(now)
      harmOsc.stop(now + duration)
    })
  }

  // Subtle click/tap sound
  const playClick = (volume: number = 0.03) => {
    const audioContext = getAudioContext()
    if (!audioContext) return
    
    const now = audioContext.currentTime
    const osc = audioContext.createOscillator()
    const gain = audioContext.createGain()
    const filter = audioContext.createBiquadFilter()
    
    osc.connect(filter)
    filter.connect(gain)
    gain.connect(audioContext.destination)
    
    osc.type = 'sine'
    osc.frequency.setValueAtTime(1200, now)
    osc.frequency.exponentialRampToValueAtTime(400, now + 0.03)
    
    filter.type = 'lowpass'
    filter.frequency.value = 2000
    
    gain.gain.setValueAtTime(volume, now)
    gain.gain.exponentialRampToValueAtTime(0.001, now + 0.05)
    
    osc.start(now)
    osc.stop(now + 0.05)
  }

  // Soft whoosh/sweep sound
  const playSweep = (direction: 'up' | 'down' = 'up', volume: number = 0.04) => {
    const audioContext = getAudioContext()
    if (!audioContext) return
    
    const now = audioContext.currentTime
    const osc = audioContext.createOscillator()
    const gain = audioContext.createGain()
    const filter = audioContext.createBiquadFilter()
    
    osc.connect(filter)
    filter.connect(gain)
    gain.connect(audioContext.destination)
    
    osc.type = 'sine'
    if (direction === 'up') {
      osc.frequency.setValueAtTime(300, now)
      osc.frequency.exponentialRampToValueAtTime(800, now + 0.15)
    } else {
      osc.frequency.setValueAtTime(800, now)
      osc.frequency.exponentialRampToValueAtTime(300, now + 0.15)
    }
    
    filter.type = 'lowpass'
    filter.frequency.setValueAtTime(1500, now)
    filter.frequency.linearRampToValueAtTime(500, now + 0.15)
    
    gain.gain.setValueAtTime(0, now)
    gain.gain.linearRampToValueAtTime(volume, now + 0.02)
    gain.gain.exponentialRampToValueAtTime(0.001, now + 0.15)
    
    osc.start(now)
    osc.stop(now + 0.15)
  }

  // Start recording - soft "on" sound, airy and warm
  const playStartRecording = () => {
    playClick(0.04)
    setTimeout(() => {
      playSweep('up', 0.03)
    }, 30)
    // Soft high ping
    setTimeout(() => {
      playTone(987, 0.15, 'sine', 0.05, { 
        attack: 0.02, 
        decay: 0.05, 
        sustain: 0.3,
        harmonics: [2, 3] 
      })
    }, 50)
  }

  // Stop recording - gentle "off" confirmation
  const playStopRecording = () => {
    playClick(0.03)
    // Two soft descending notes
    playTone(660, 0.1, 'sine', 0.04, { attack: 0.01, decay: 0.03, sustain: 0.4 })
    setTimeout(() => {
      playTone(523, 0.12, 'sine', 0.05, { attack: 0.01, decay: 0.04, sustain: 0.5 })
    }, 70)
  }

  // Processing/thinking sound - subtle pulse
  const playProcessing = () => {
    playTone(440, 0.08, 'sine', 0.025, { attack: 0.02, decay: 0.02 })
  }

  // Transcription started - soft blip
  const playTranscribing = () => {
    playSweep('up', 0.025)
    setTimeout(() => {
      playTone(698, 0.1, 'sine', 0.03, { attack: 0.01, decay: 0.03, harmonics: [2] })
    }, 80)
  }

  // Analyzing started - slightly different blip
  const playAnalyzing = () => {
    playTone(587, 0.08, 'sine', 0.025, { attack: 0.01, decay: 0.02 })
    setTimeout(() => {
      playTone(740, 0.1, 'sine', 0.03, { attack: 0.01, decay: 0.03 })
    }, 60)
  }

  // Success - pleasant, satisfying chime (major chord arpeggio)
  const playSuccess = () => {
    const baseVolume = 0.045
    // C major arpeggio with soft attack
    playTone(523, 0.18, 'sine', baseVolume, { attack: 0.02, decay: 0.06, sustain: 0.4, harmonics: [2] }) // C5
    setTimeout(() => {
      playTone(659, 0.16, 'sine', baseVolume, { attack: 0.015, decay: 0.05, sustain: 0.4, harmonics: [2] }) // E5
    }, 80)
    setTimeout(() => {
      playTone(784, 0.16, 'sine', baseVolume, { attack: 0.015, decay: 0.05, sustain: 0.4, harmonics: [2] }) // G5
    }, 160)
    setTimeout(() => {
      playTone(1047, 0.25, 'sine', baseVolume * 1.2, { attack: 0.02, decay: 0.08, sustain: 0.5, harmonics: [2, 3] }) // C6
    }, 250)
  }

  // Error - soft but noticeable warning
  const playError = () => {
    playTone(220, 0.15, 'triangle', 0.05, { attack: 0.01, decay: 0.05, sustain: 0.6 })
    setTimeout(() => {
      playTone(185, 0.2, 'triangle', 0.04, { attack: 0.01, decay: 0.08, sustain: 0.5 })
    }, 100)
  }

  // Notification - gentle ping
  const playNotification = () => {
    playTone(880, 0.12, 'sine', 0.035, { attack: 0.01, decay: 0.04, sustain: 0.3, harmonics: [2] })
    setTimeout(() => {
      playTone(1108, 0.1, 'sine', 0.025, { attack: 0.01, decay: 0.03, sustain: 0.25 })
    }, 100)
  }

  // Tick sound for progress updates
  const playTick = () => {
    playClick(0.02)
  }

  // Message received/sent sound
  const playMessage = () => {
    playTone(740, 0.06, 'sine', 0.025, { attack: 0.005, decay: 0.02 })
  }

  return { 
    playStartRecording, 
    playStopRecording, 
    playSuccess, 
    playError,
    playProcessing,
    playTranscribing,
    playAnalyzing,
    playNotification,
    playTick,
    playMessage,
    playClick,
    playSweep
  }
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
