import { useEffect, useState, useRef } from 'react'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'
import { Input } from '@/components/ui/input'
import { Badge } from '@/components/ui/badge'
import { Separator } from '@/components/ui/separator'
import { CheckCircle2, Clock, Sparkles } from 'lucide-react'
import { cn } from '@/lib/utils'

interface CRMField {
  id: string
  label: string
  value: string
  status: 'empty' | 'filling' | 'filled'
}

interface CRMFormProps {
  data: {
    objet?: string
    reference_piece?: string
    gravite?: number
    action_requise?: string
  } | null
  isProcessing: boolean
  onComplete?: (ticketData: any) => void
}

export function CRMForm({ data, isProcessing, onComplete }: CRMFormProps) {
  const [fields, setFields] = useState<CRMField[]>([
    { id: 'ticket_id', label: 'Ticket ID', value: '', status: 'empty' },
    { id: 'objet', label: 'Objet', value: '', status: 'empty' },
    { id: 'reference_piece', label: 'Référence', value: '', status: 'empty' },
    { id: 'gravite', label: 'Gravité', value: '', status: 'empty' },
    { id: 'action_requise', label: 'Action', value: '', status: 'empty' },
    { id: 'statut', label: 'Statut', value: '', status: 'empty' },
  ])
  const ticketIdRef = useRef<string | null>(null)
  const completedRef = useRef<boolean>(false)
  const processingRef = useRef<string | null>(null) // Track which data we're processing

  useEffect(() => {
    console.log('🔄 CRMForm useEffect - data:', data, 'isProcessing:', isProcessing)
    
    if (!data) {
      setFields(prev => prev.map(f => ({ ...f, value: '', status: 'empty' as const })))
      ticketIdRef.current = null
      completedRef.current = false
      processingRef.current = null
      return
    }
    
    // Créer une clé unique pour ces données
    const dataKey = `${data.objet}-${data.reference_piece}-${data.gravite}`
    
    // Vérifier si on est déjà en train de traiter ces mêmes données
    if (processingRef.current === dataKey) {
      console.log('⚠️ Ces données sont déjà en cours de traitement, ignoré')
      return
    }
    
    // Vérifier si on a déjà complété un ticket
    if (completedRef.current) {
      console.log('⚠️ Un ticket a déjà été complété pour cette session, ignoré')
      return
    }
    
    console.log('🚀 Démarrage du remplissage du formulaire CRM')
    processingRef.current = dataKey

    const updateField = (fieldId: string, value: string, delay: number) => {
      setTimeout(() => {
        setFields(prev => prev.map(field => {
          if (field.id === fieldId) {
            return { ...field, value, status: 'filling' as const }
          }
          return field
        }))

        setTimeout(() => {
          setFields(prev => prev.map(field => {
            if (field.id === fieldId) {
              return { ...field, status: 'filled' as const }
            }
            return field
          }))
        }, 800)
      }, delay)
    }

    const ticketId = `TKT-${Date.now().toString().slice(-6)}`
    ticketIdRef.current = ticketId
    updateField('ticket_id', ticketId, 100)

    if (data.objet) {
      updateField('objet', data.objet, 300)
    }
    if (data.reference_piece) {
      updateField('reference_piece', data.reference_piece, 500)
    }
    if (data.gravite) {
      const graviteText = `${data.gravite}/5`
      updateField('gravite', graviteText, 700)
    }
    if (data.action_requise) {
      updateField('action_requise', data.action_requise, 900)
    }

    updateField('statut', 'Créé', 1100)

    // Notifier la completion après que tous les champs soient remplis
    const completionTimeout = setTimeout(() => {
      if (onComplete && data && !completedRef.current && ticketIdRef.current) {
        completedRef.current = true
        const ticketData = {
          id: ticketIdRef.current,
          objet: data.objet || '',
          reference_piece: data.reference_piece || '',
          gravite: data.gravite || 1,
          action_requise: data.action_requise || '',
          createdAt: new Date(),
          status: 'new' as const
        }
        console.log('📤 Envoi du ticket complet:', ticketData)
        onComplete(ticketData)
      }
    }, 2000)
    
    return () => {
      clearTimeout(completionTimeout)
    }
  }, [data, isProcessing, onComplete])

  const hasData = fields.some(f => f.status !== 'empty')

  return (
    <Card className={cn(
      "transition-all duration-500",
      hasData && "ring-2 ring-blue-500/50 shadow-lg"
    )}>
      <CardHeader>
        <div className="flex items-center justify-between">
          <CardTitle className="text-lg flex items-center gap-2">
            {hasData && <Sparkles className="w-4 h-4 text-blue-500 animate-pulse" />}
            Nouveau Ticket
          </CardTitle>
          {hasData && (
            <Badge variant="default" className="text-xs animate-pulse">
              En création...
            </Badge>
          )}
        </div>
      </CardHeader>
      <CardContent>
        <div className="space-y-4">
          {fields.map((field, index) => (
            <div key={field.id} className="space-y-2">
              <div className="flex items-center justify-between">
                <label className="text-xs font-medium text-muted-foreground flex items-center gap-2">
                  {field.status === 'filling' && (
                    <Clock className="w-3.5 h-3.5 text-blue-500 animate-spin" />
                  )}
                  {field.status === 'filled' && (
                    <CheckCircle2 className="w-3.5 h-3.5 text-green-500" />
                  )}
                  {field.status === 'empty' && (
                    <div className="w-3.5 h-3.5 rounded-full border border-muted-foreground/30" />
                  )}
                  {field.label}
                </label>
                {field.status === 'filled' && (
                  <Badge variant="outline" className="text-xs bg-green-500/10 border-green-500/50 text-green-500">
                    ✓
                  </Badge>
                )}
              </div>
              <Input
                value={field.value}
                readOnly
                className={cn(
                  "h-10 text-sm transition-all duration-500 font-medium",
                  field.status === 'filling' && "ring-2 ring-blue-500 bg-blue-500/10 border-blue-500 animate-pulse",
                  field.status === 'filled' && "ring-2 ring-green-500 bg-green-500/10 border-green-500",
                  field.status === 'empty' && "bg-muted/50"
                )}
                placeholder={field.status === 'empty' ? 'En attente...' : ''}
              />
              {index < fields.length - 1 && <Separator className="mt-4" />}
            </div>
          ))}
        </div>
      </CardContent>
    </Card>
  )
}
