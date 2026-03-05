import { useState, useRef, useEffect } from 'react'
import { Mic, Settings, PanelRightOpen, PanelRightClose, Camera, X, MessageSquare, Send } from 'lucide-react'
import { Progress } from '@/components/ui/progress'
import { Badge } from '@/components/ui/badge'
import { Button } from '@/components/ui/button'
import { VoiceButton, type VoiceButtonState } from '@/components/ui/voice-button'
import {
  Conversation,
  ConversationContent,
  ConversationEmptyState,
  ConversationScrollButton,
} from '@/components/ui/conversation'
import { Message, type MessageProps } from '@/components/ui/message'
import { SettingsPanel } from '@/components/ui/settings-panel'
import { NotificationsPanel, SAPPanel } from '@/components/ui/notifications-panel'
import { useAudioFeedback, useTTS } from '@/hooks/useAudioFeedback'

const API_URL = 'http://localhost:8000'

interface ERPData {
  objet: string
  reference_piece: string
  gravite: number
  action_requise: string
}

interface SAPTicket {
  id: string
  objet: string
  reference: string
  gravite: number
  action: string
  photo?: string
  timestamp: Date
}

interface Notification {
  id: string
  type: 'slack' | 'sap'
  title: string
  description: string
  timestamp: Date
}

function App() {
  const [voiceState, setVoiceState] = useState<VoiceButtonState>('idle')
  const [isProcessing, setIsProcessing] = useState(false)
  const [souverainete, setSouverainete] = useState(0)
  const [status, setStatus] = useState<'idle' | 'listening' | 'transcribing' | 'analyzing' | 'complete'>('idle')
  const [messages, setMessages] = useState<(MessageProps & { id: string })[]>([])
  const [settingsOpen, setSettingsOpen] = useState(false)
  
  // New features
  const [sapPanelOpen, setSapPanelOpen] = useState(false)
  const [sapTickets, setSapTickets] = useState<SAPTicket[]>([])
  const [notifications, setNotifications] = useState<Notification[]>([])

  const [pendingPhoto, setPendingPhoto] = useState<string | null>(null)
  const [textInputOpen, setTextInputOpen] = useState(false)
  const [textInputValue, setTextInputValue] = useState('')

  const mediaRecorderRef = useRef<MediaRecorder | null>(null)
  const audioChunksRef = useRef<Blob[]>([])
  const fileInputRef = useRef<HTMLInputElement | null>(null)
  
  // Audio & TTS hooks
  const { 
    playStartRecording, 
    playStopRecording, 
    playSuccess, 
    playError,
    playTranscribing,
    playAnalyzing,
    playNotification,
    playMessage
  } = useAudioFeedback()
  const { speakTicketCreated } = useTTS()

  useEffect(() => {
    if (isProcessing) {
      const interval = setInterval(() => {
        setSouverainete((prev) => {
          if (prev >= 100) return 100
          return prev + 10
        })
      }, 200)
      return () => clearInterval(interval)
    } else if (status === 'idle') {
      setSouverainete(0)
    }
  }, [isProcessing, status])

  const addMessage = (message: Omit<MessageProps & { id: string }, 'id'>) => {
    const id = `msg-${Date.now()}-${Math.random().toString(36).substr(2, 9)}`
    setMessages(prev => [...prev, { ...message, id } as MessageProps & { id: string }])
    return id
  }

  const updateMessage = (id: string, updates: Partial<MessageProps>) => {
    setMessages(prev => prev.map(msg => 
      msg.id === id ? { ...msg, ...updates } : msg
    ))
  }

  const streamRef = useRef<MediaStream | null>(null)

  const handlePressStart = async () => {
    if (voiceState !== 'idle') return
    
    playStartRecording() // Audio feedback
    
    try {
      const stream = await navigator.mediaDevices.getUserMedia({ audio: true })
      streamRef.current = stream
      
      const mediaRecorder = new MediaRecorder(stream, {
        mimeType: 'audio/webm;codecs=opus'
      })

      audioChunksRef.current = []

      mediaRecorder.ondataavailable = (event) => {
        if (event.data.size > 0) {
          audioChunksRef.current.push(event.data)
        }
      }

      mediaRecorder.onstop = async () => {
        const audioBlob = new Blob(audioChunksRef.current, { type: 'audio/webm' })
        if (streamRef.current) {
          streamRef.current.getTracks().forEach(track => track.stop())
          streamRef.current = null
        }
        setVoiceState('processing')
        setStatus('transcribing')
        await processAudio(audioBlob)
      }

      mediaRecorderRef.current = mediaRecorder
      mediaRecorder.start()
      setVoiceState('recording')
      setStatus('listening')
      setSouverainete(0)
    } catch (error) {
      console.error('Erreur micro:', error)
      playError() // Error sound for microphone access
      setVoiceState('error')
      setTimeout(() => setVoiceState('idle'), 2000)
    }
  }

  const handlePressEnd = () => {
    if (voiceState !== 'recording') return
    
    playStopRecording() // Audio feedback
    
    if (mediaRecorderRef.current && mediaRecorderRef.current.state === 'recording') {
      mediaRecorderRef.current.stop()
    }
  }
  
  // Add notification
  const addNotification = (type: 'slack' | 'sap', title: string, description: string) => {
    const notif: Notification = {
      id: `notif-${Date.now()}`,
      type,
      title,
      description,
      timestamp: new Date()
    }
    setNotifications(prev => [notif, ...prev])
    
    // Auto-remove after 5s
    setTimeout(() => {
      setNotifications(prev => prev.filter(n => n.id !== notif.id))
    }, 5000)
  }

  const handlePhotoCapture = (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0]
    if (!file) return
    const reader = new FileReader()
    reader.onloadend = () => {
      setPendingPhoto(reader.result as string)
    }
    reader.readAsDataURL(file)
    e.target.value = ''
  }

  const handleTextSubmit = async () => {
    const text = textInputValue.trim()
    if (!text || isProcessing) return
    setTextInputOpen(false)
    setTextInputValue('')
    setIsProcessing(true)
    setSouverainete(50)
    setStatus('analyzing')

    playMessage()
    addMessage({ type: 'user', content: text, timestamp: new Date() })

    const analyzingMsgId = addMessage({
      type: 'system',
      content: 'Analyse par IA Mistral...',
      status: 'processing',
      timestamp: new Date()
    })

    try {
      playAnalyzing()
      const actionResponse = await fetch(`${API_URL}/action`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ text }),
      })
      if (!actionResponse.ok) throw new Error('Erreur analyse')
      const actionData = await actionResponse.json()
      setSouverainete(100)

      if (actionData.data) {
        const erpData: ERPData = actionData.data
        const ticketId = `TKT-${Date.now().toString().slice(-6)}`
        updateMessage(analyzingMsgId, { type: 'system', content: 'Ticket créé avec succès', status: 'success' })
        addMessage({ type: 'ticket', ticketId, objet: erpData.objet, reference: erpData.reference_piece, gravite: erpData.gravite, action: erpData.action_requise, photo: pendingPhoto || undefined, timestamp: new Date() })
        addMessage({ type: 'notification', title: 'Ticket enregistré', description: ticketId, variant: 'success', timestamp: new Date() })
        playSuccess()
        setTimeout(() => speakTicketCreated(erpData.objet, erpData.gravite), 500)
        setSapTickets(prev => [{ id: ticketId, objet: erpData.objet, reference: erpData.reference_piece, gravite: erpData.gravite, action: erpData.action_requise, photo: pendingPhoto || undefined, timestamp: new Date() }, ...prev])
        setPendingPhoto(null)
        setTimeout(() => { playNotification(); addNotification('slack', 'Nouveau ticket', `${ticketId} - ${erpData.objet}`) }, 1000)
        setTimeout(() => { playNotification(); addNotification('sap', 'Sync SAP', 'Notification créée dans SAP') }, 2000)
        setStatus('complete')
        setVoiceState('success')
        setTimeout(() => { setVoiceState('idle'); setStatus('idle') }, 1500)
      } else {
        playError()
        updateMessage(analyzingMsgId, { type: 'system', content: "Erreur lors de l'analyse", status: 'error' })
        setVoiceState('error')
        setTimeout(() => { setVoiceState('idle'); setStatus('idle') }, 2000)
      }
    } catch {
      playError()
      addMessage({ type: 'notification', title: 'Erreur de traitement', variant: 'error', timestamp: new Date() })
      setVoiceState('error')
      setTimeout(() => { setVoiceState('idle'); setStatus('idle') }, 2000)
    } finally {
      setIsProcessing(false)
    }
  }

  useEffect(() => {
    const handleKeyDown = (e: KeyboardEvent) => {
      if (textInputOpen) return
      if (e.code === 'Space' && !e.repeat && voiceState === 'idle') {
        e.preventDefault()
        handlePressStart()
      }
    }

    const handleKeyUp = (e: KeyboardEvent) => {
      if (textInputOpen) return
      if (e.code === 'Space' && voiceState === 'recording') {
        e.preventDefault()
        handlePressEnd()
      }
    }

    window.addEventListener('keydown', handleKeyDown)
    window.addEventListener('keyup', handleKeyUp)
    return () => {
      window.removeEventListener('keydown', handleKeyDown)
      window.removeEventListener('keyup', handleKeyUp)
    }
  }, [voiceState, textInputOpen])

  const processAudio = async (audioBlob: Blob) => {
    setIsProcessing(true)
    setSouverainete(10)

    // Add processing notification
    const processingMsgId = addMessage({
      type: 'system',
      content: 'Transcription en cours...',
      status: 'processing',
      timestamp: new Date()
    })

    try {
      setStatus('transcribing')
      playTranscribing() // Sound feedback for transcription start
      const formData = new FormData()
      formData.append('audio', audioBlob, 'recording.webm')

      const transcribeResponse = await fetch(`${API_URL}/transcribe`, {
        method: 'POST',
        body: formData,
      })

      if (!transcribeResponse.ok) {
        throw new Error('Erreur transcription')
      }

      const transcribeData = await transcribeResponse.json()
      setSouverainete(50)

      // Update processing message and add user message
      updateMessage(processingMsgId, {
        type: 'system',
        content: 'Transcription terminée',
        status: 'success'
      })

      // Add user message with word-level confidence
      playMessage() // Sound for user message
      const userMsgId = addMessage({
        type: 'user',
        content: transcribeData.text,
        words: transcribeData.words || [],
        isTyping: true,
        timestamp: new Date()
      })

      // After typing animation, remove isTyping flag
      setTimeout(() => {
        updateMessage(userMsgId, { isTyping: false })
      }, (transcribeData.words?.length || transcribeData.text.length / 2) * 60 + 500)

      // Add analyzing notification
      const analyzingMsgId = addMessage({
        type: 'system',
        content: 'Analyse par IA Mistral...',
        status: 'processing',
        timestamp: new Date()
      })

      setStatus('analyzing')
      playAnalyzing() // Sound for AI analysis start
      const actionResponse = await fetch(`${API_URL}/action`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ text: transcribeData.text }),
      })

      if (!actionResponse.ok) {
        throw new Error('Erreur analyse')
      }

      const actionData = await actionResponse.json()
      setSouverainete(100)
      
      if (actionData.data) {
        const erpData: ERPData = actionData.data
        const ticketId = `TKT-${Date.now().toString().slice(-6)}`
        
        const finalObjet = erpData.objet
        const finalReference = erpData.reference_piece

        // Update analyzing message
        updateMessage(analyzingMsgId, {
          type: 'system',
          content: 'Ticket créé avec succès',
          status: 'success'
        })

        // Add ticket message
        addMessage({
          type: 'ticket',
          ticketId,
          objet: finalObjet,
          reference: finalReference,
          gravite: erpData.gravite,
          action: erpData.action_requise,
          photo: pendingPhoto || undefined,
          timestamp: new Date()
        })

        // Add success notification
        addMessage({
          type: 'notification',
          title: 'Ticket enregistré',
          description: ticketId,
          variant: 'success',
          timestamp: new Date()
        })
        
        // 🔊 Audio feedback & TTS
        playSuccess()
        setTimeout(() => {
          speakTicketCreated(finalObjet, erpData.gravite)
        }, 500)
        
        // 📱 Add to SAP panel
        const sapTicket: SAPTicket = {
          id: ticketId,
          objet: finalObjet,
          reference: finalReference,
          gravite: erpData.gravite,
          action: erpData.action_requise,
          photo: pendingPhoto || undefined,
          timestamp: new Date()
        }
        setSapTickets(prev => [sapTicket, ...prev])
        setPendingPhoto(null)
        
        // 🔔 Send notifications with sounds
        setTimeout(() => {
          playNotification()
          addNotification('slack', 'Nouveau ticket', `${ticketId} - ${finalObjet}`)
        }, 1000)
        setTimeout(() => {
          playNotification()
          addNotification('sap', 'Sync SAP', `Notification créée dans SAP`)
        }, 2000)

        setStatus('complete')
        setVoiceState('success')
        setTimeout(() => {
          setVoiceState('idle')
          setStatus('idle')
        }, 1500)
      } else {
        playError() // Error sound
        updateMessage(analyzingMsgId, {
          type: 'system',
          content: 'Erreur lors de l\'analyse',
          status: 'error'
        })
        setVoiceState('error')
        setTimeout(() => {
          setVoiceState('idle')
          setStatus('idle')
        }, 2000)
      }
    } catch (error) {
      console.error('Erreur:', error)
      playError() // Error sound
      addMessage({
        type: 'notification',
        title: 'Erreur de traitement',
        variant: 'error',
        timestamp: new Date()
      })
      setVoiceState('error')
      setTimeout(() => {
        setVoiceState('idle')
        setStatus('idle')
      }, 2000)
    } finally {
      setIsProcessing(false)
    }
  }

  return (
    <div className="h-screen bg-black text-white flex flex-col overflow-hidden">
      {/* Panels & Overlays */}
      <SettingsPanel isOpen={settingsOpen} onClose={() => setSettingsOpen(false)} />
      <SAPPanel isOpen={sapPanelOpen} onClose={() => setSapPanelOpen(false)} tickets={sapTickets} />
      <NotificationsPanel notifications={notifications} />

      {/* Header - Fixed */}
      <header className="flex-shrink-0 border-b border-neutral-800 px-4 py-3 bg-black z-10">
        <div className="max-w-md mx-auto">
          {/* Top row */}
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-3">
              <img 
                src="/logo_lexia.webp" 
                alt="Lexia" 
                className="h-6 w-auto brightness-0 invert"
              />
            </div>
            <div className="flex items-center gap-1">
              {messages.filter(m => m.type === 'ticket').length > 0 && (
                <Badge variant="outline" className="text-xs border-neutral-700 text-neutral-400 mr-1">
                  {messages.filter(m => m.type === 'ticket').length}
                </Badge>
              )}
              <Button 
                variant="ghost" 
                size="icon" 
                onClick={() => setSapPanelOpen(!sapPanelOpen)}
                className="h-8 w-8 text-neutral-400 hover:text-white"
                title="Panel SAP"
              >
                {sapPanelOpen ? <PanelRightClose className="h-4 w-4" /> : <PanelRightOpen className="h-4 w-4" />}
              </Button>
              <Button 
                variant="ghost" 
                size="icon" 
                onClick={() => setSettingsOpen(true)}
                className="h-8 w-8 text-neutral-400 hover:text-white"
              >
                <Settings className="h-4 w-4" />
              </Button>
            </div>
          </div>
          
          {/* Offline indicator */}
          <div className="flex items-center justify-center gap-2 mt-2 pt-2 border-t border-neutral-800/50">
            <div className="flex items-center gap-1.5 bg-green-500/10 px-2 py-1 rounded-full">
              <div className="w-1.5 h-1.5 rounded-full bg-green-500" />
              <span className="text-[10px] text-green-500 font-medium">100% Local</span>
            </div>
            <div className="flex items-center gap-1.5 bg-neutral-800 px-2 py-1 rounded-full">
              <svg className="w-3 h-3 text-neutral-500" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12l2 2 4-4m5.618-4.016A11.955 11.955 0 0112 2.944a11.955 11.955 0 01-8.618 3.04A12.02 12.02 0 003 9c0 5.591 3.824 10.29 9 11.622 5.176-1.332 9-6.03 9-11.622 0-1.042-.133-2.052-.382-3.016z" />
              </svg>
              <span className="text-[10px] text-neutral-400 font-medium">Souverain</span>
            </div>
            <div className="flex items-center gap-1.5 bg-neutral-800 px-2 py-1 rounded-full">
              <span className="text-[10px] text-neutral-400 font-medium">SAP · Sage · Salesforce</span>
            </div>
          </div>
        </div>
      </header>

      {/* Conversation - Scrollable middle section */}
      <main className="flex-1 overflow-y-auto">
        <div className="max-w-md mx-auto w-full h-full">
          <Conversation className="h-full">
            <ConversationContent className="min-h-full">
              {messages.length === 0 ? (
                <ConversationEmptyState
                  title="Commencez une conversation"
                  description="Maintenez le bouton pour dicter un message vocal"
                  icon={<Mic className="h-6 w-6 text-neutral-400" />}
                />
              ) : (
                messages.map((message) => (
                  <Message key={message.id} {...message} />
                ))
              )}
            </ConversationContent>
            <ConversationScrollButton />
          </Conversation>
        </div>
      </main>

      {/* Footer - Fixed */}
      <footer className="flex-shrink-0 border-t border-neutral-800 px-4 py-4 bg-black z-10">
        <div className="max-w-md mx-auto space-y-3">
          {/* Progress bar */}
          {isProcessing && (
            <div className="space-y-2">
              <div className="flex items-center justify-between text-xs">
                <div className="flex items-center gap-2">
                  <div className="w-1.5 h-1.5 rounded-full bg-green-500 animate-pulse" />
                  <span className="text-neutral-400">
                    {status === 'transcribing' && 'Transcription...'}
                    {status === 'analyzing' && 'Analyse IA...'}
                    {status === 'complete' && 'Terminé'}
                  </span>
                </div>
                <span className="text-green-500 font-mono text-xs">{souverainete}%</span>
              </div>
              <Progress value={souverainete} className="h-1.5 bg-neutral-800" />
            </div>
          )}

          {/* Photo preview */}
          {pendingPhoto && (
            <div className="flex items-center gap-2 p-2 rounded-lg bg-neutral-900 border border-neutral-800">
              <img src={pendingPhoto} alt="Photo jointe" className="h-12 w-12 rounded-md object-cover" />
              <span className="text-xs text-neutral-400 flex-1">Photo jointe au prochain ticket</span>
              <button onClick={() => setPendingPhoto(null)} className="p-1 rounded hover:bg-neutral-800 text-neutral-500 hover:text-white transition-colors">
                <X className="h-4 w-4" />
              </button>
            </div>
          )}

          {/* Text input */}
          {textInputOpen && (
            <div className="flex items-center gap-2">
              <input
                type="text"
                value={textInputValue}
                onChange={(e) => setTextInputValue(e.target.value)}
                onKeyDown={(e) => { if (e.key === 'Enter') handleTextSubmit() }}
                placeholder="Décrivez le problème..."
                autoFocus
                className="flex-1 h-10 rounded-lg bg-neutral-900 border border-neutral-700 px-3 text-sm text-white placeholder:text-neutral-500 focus:outline-none focus:border-neutral-500"
              />
              <Button
                variant="outline"
                size="icon"
                onClick={handleTextSubmit}
                disabled={!textInputValue.trim()}
                className="h-10 w-10 flex-shrink-0 border-neutral-700 text-neutral-400 hover:text-white hover:border-neutral-500 disabled:opacity-30"
              >
                <Send className="h-4 w-4" />
              </Button>
              <Button
                variant="outline"
                size="icon"
                onClick={() => { setTextInputOpen(false); setTextInputValue('') }}
                className="h-10 w-10 flex-shrink-0 border-neutral-700 text-neutral-500 hover:text-white hover:border-neutral-500"
              >
                <X className="h-4 w-4" />
              </Button>
            </div>
          )}

          {/* Voice Button + Camera + Text */}
          <input
            ref={fileInputRef}
            type="file"
            accept="image/*"
            capture="environment"
            onChange={handlePhotoCapture}
            className="hidden"
          />
          {!textInputOpen && (
            <div className="flex items-center gap-2">
              <Button
                variant="outline"
                size="icon"
                onClick={() => fileInputRef.current?.click()}
                className="h-12 w-12 flex-shrink-0 border-neutral-700 text-neutral-400 hover:text-white hover:border-neutral-500"
                title="Ajouter une photo"
              >
                <Camera className="h-5 w-5" />
              </Button>
              <VoiceButton
                label="Maintenez pour parler"
                trailing="Space"
                state={voiceState}
                onPressStart={handlePressStart}
                onPressEnd={handlePressEnd}
                pushToTalk={true}
                variant="outline"
                size="lg"
                className="flex-1"
              />
              <Button
                variant="outline"
                size="icon"
                onClick={() => setTextInputOpen(true)}
                className="h-12 w-12 flex-shrink-0 border-neutral-700 text-neutral-400 hover:text-white hover:border-neutral-500"
                title="Saisie texte"
              >
                <MessageSquare className="h-5 w-5" />
              </Button>
            </div>
          )}
        </div>
      </footer>
    </div>
  )
}

export default App
