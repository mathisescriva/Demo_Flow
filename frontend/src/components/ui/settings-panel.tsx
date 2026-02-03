"use client"

import * as React from "react"
import { Settings, X, Plus, Trash2, Sparkles } from "lucide-react"
import { cn } from "@/lib/utils"
import { Button } from "@/components/ui/button"
import { Badge } from "@/components/ui/badge"
import { Separator } from "@/components/ui/separator"

const API_URL = 'http://localhost:8000'

interface SettingsPanelProps {
  isOpen: boolean
  onClose: () => void
}

export function SettingsPanel({ isOpen, onClose }: SettingsPanelProps) {
  const [vocabulary, setVocabulary] = React.useState<{
    default: string[]
    custom: string[]
    total: number
  } | null>(null)
  const [newWord, setNewWord] = React.useState('')
  const [loading, setLoading] = React.useState(false)

  React.useEffect(() => {
    if (isOpen) {
      fetchVocabulary()
    }
  }, [isOpen])

  const fetchVocabulary = async () => {
    try {
      const response = await fetch(`${API_URL}/vocabulary`)
      const data = await response.json()
      setVocabulary(data)
    } catch (error) {
      console.error('Erreur chargement vocabulaire:', error)
    }
  }

  const addWord = async () => {
    if (!newWord.trim()) return
    setLoading(true)
    try {
      await fetch(`${API_URL}/vocabulary/add`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ word: newWord.trim() })
      })
      setNewWord('')
      await fetchVocabulary()
    } catch (error) {
      console.error('Erreur ajout mot:', error)
    }
    setLoading(false)
  }

  const removeWord = async (word: string) => {
    if (!vocabulary) return
    const newCustom = vocabulary.custom.filter(w => w !== word)
    try {
      await fetch(`${API_URL}/vocabulary`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ words: newCustom })
      })
      await fetchVocabulary()
    } catch (error) {
      console.error('Erreur suppression mot:', error)
    }
  }

  if (!isOpen) return null

  return (
    <div className="fixed inset-0 z-50 bg-black/80 backdrop-blur-sm">
      <div className="fixed inset-y-0 right-0 w-full max-w-sm bg-neutral-900 border-l border-neutral-800 shadow-xl">
        {/* Header */}
        <div className="flex items-center justify-between p-4 border-b border-neutral-800">
          <div className="flex items-center gap-2">
            <Settings className="h-5 w-5 text-neutral-400" />
            <h2 className="font-semibold">Paramètres</h2>
          </div>
          <Button variant="ghost" size="icon" onClick={onClose}>
            <X className="h-5 w-5" />
          </Button>
        </div>

        {/* Content */}
        <div className="p-4 space-y-6 overflow-y-auto h-[calc(100vh-73px)]">
          {/* Word Boost Section */}
          <div>
            <div className="flex items-center gap-2 mb-3">
              <Sparkles className="h-4 w-4 text-neutral-400" />
              <h3 className="text-sm font-medium">Word Boost</h3>
              {vocabulary && (
                <Badge variant="outline" className="text-xs border-neutral-700">
                  {vocabulary.total} mots
                </Badge>
              )}
            </div>
            <p className="text-xs text-neutral-500 mb-4">
              Ajoutez des mots-clés pour améliorer la reconnaissance vocale de termes spécifiques.
            </p>

            {/* Add word input */}
            <div className="flex gap-2 mb-4">
              <input
                type="text"
                value={newWord}
                onChange={(e) => setNewWord(e.target.value)}
                onKeyDown={(e) => e.key === 'Enter' && addWord()}
                placeholder="Nouveau mot..."
                className="flex-1 h-9 px-3 text-sm bg-neutral-800 border border-neutral-700 rounded-md focus:outline-none focus:border-neutral-600"
              />
              <Button 
                variant="outline" 
                size="sm" 
                onClick={addWord}
                disabled={loading || !newWord.trim()}
                className="border-neutral-700"
              >
                <Plus className="h-4 w-4" />
              </Button>
            </div>

            {/* Custom vocabulary */}
            {vocabulary && vocabulary.custom.length > 0 && (
              <div className="mb-4">
                <p className="text-xs text-neutral-500 mb-2">Mots personnalisés</p>
                <div className="flex flex-wrap gap-2">
                  {vocabulary.custom.map((word) => (
                    <Badge 
                      key={word} 
                      variant="secondary" 
                      className="bg-neutral-800 text-neutral-300 pr-1"
                    >
                      {word}
                      <button
                        onClick={() => removeWord(word)}
                        className="ml-1 p-0.5 hover:bg-neutral-700 rounded"
                      >
                        <X className="h-3 w-3" />
                      </button>
                    </Badge>
                  ))}
                </div>
              </div>
            )}

            <Separator className="bg-neutral-800 my-4" />

            {/* Default vocabulary */}
            {vocabulary && (
              <div>
                <p className="text-xs text-neutral-500 mb-2">Vocabulaire par défaut</p>
                <div className="flex flex-wrap gap-1.5">
                  {vocabulary.default.map((word) => (
                    <Badge 
                      key={word} 
                      variant="outline" 
                      className="text-xs border-neutral-800 text-neutral-500"
                    >
                      {word}
                    </Badge>
                  ))}
                </div>
              </div>
            )}
          </div>

          <Separator className="bg-neutral-800" />

          {/* Info Section */}
          <div>
            <h3 className="text-sm font-medium mb-2">À propos</h3>
            <div className="space-y-2 text-xs text-neutral-500">
              <p>• Transcription : Faster-Whisper (local)</p>
              <p>• Analyse : Ollama + Mistral (local)</p>
              <p>• Traitement 100% souverain</p>
            </div>
          </div>
        </div>
      </div>
    </div>
  )
}
