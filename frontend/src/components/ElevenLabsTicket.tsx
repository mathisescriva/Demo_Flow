import { Card } from '@/components/ui/card'
import { Badge } from '@/components/ui/badge'
import { Zap, AlertTriangle, Info, Clock, ArrowRight } from 'lucide-react'
import { cn } from '@/lib/utils'

interface Ticket {
  id: string
  objet: string
  reference_piece: string
  gravite: number
  action_requise: string
  createdAt: Date
  status: 'new' | 'processing' | 'completed'
}

interface ElevenLabsTicketProps {
  ticket: Ticket
  index: number
}

export function ElevenLabsTicket({ ticket, index }: ElevenLabsTicketProps) {
  const getGraviteConfig = (gravite: number) => {
    if (gravite >= 5) {
      return {
        label: 'Urgente',
        icon: Zap,
        color: 'text-red-400',
        bg: 'bg-red-500/10',
        border: 'border-red-500/20',
        glow: 'shadow-red-500/20'
      }
    }
    if (gravite >= 4) {
      return {
        label: 'Critique',
        icon: AlertTriangle,
        color: 'text-orange-400',
        bg: 'bg-orange-500/10',
        border: 'border-orange-500/20',
        glow: 'shadow-orange-500/20'
      }
    }
    if (gravite >= 3) {
      return {
        label: 'Élevée',
        icon: Info,
        color: 'text-yellow-400',
        bg: 'bg-yellow-500/10',
        border: 'border-yellow-500/20',
        glow: 'shadow-yellow-500/20'
      }
    }
    return {
      label: gravite >= 2 ? 'Modérée' : 'Faible',
      icon: Info,
      color: 'text-blue-400',
      bg: 'bg-blue-500/10',
      border: 'border-blue-500/20',
      glow: 'shadow-blue-500/20'
    }
  }

  const config = getGraviteConfig(ticket.gravite)
  const Icon = config.icon

  const formatTime = (date: Date) => {
    return new Intl.DateTimeFormat('fr-FR', {
      hour: '2-digit',
      minute: '2-digit'
    }).format(date)
  }

  return (
    <Card
      className={cn(
        "group relative overflow-hidden border backdrop-blur-xl bg-background/80 transition-all duration-500 hover:scale-[1.02] hover:shadow-xl",
        config.border,
        config.glow,
        "animate-in slide-in-from-right"
      )}
      style={{
        animationDelay: `${index * 100}ms`
      }}
    >
      <div className={cn("absolute inset-0 opacity-0 group-hover:opacity-100 transition-opacity", config.bg)} />
      
      <div className="relative p-5 space-y-4">
        {/* Header */}
        <div className="flex items-start justify-between gap-3">
          <div className="flex-1 min-w-0">
            <div className="flex items-center gap-2 mb-2 flex-wrap">
              <span className="text-xs font-mono text-muted-foreground/60">
                {ticket.id}
              </span>
              <Badge
                variant="outline"
                className={cn("text-xs font-medium border", config.color, config.bg, config.border)}
              >
                <Icon className="w-3 h-3 mr-1" />
                {config.label}
              </Badge>
            </div>
            <h3 className="text-base font-semibold leading-tight mb-1">
              {ticket.objet}
            </h3>
          </div>
          <ArrowRight className="w-4 h-4 text-muted-foreground/40 group-hover:text-foreground transition-colors" />
        </div>

        {/* Content */}
        {ticket.reference_piece && (
          <div className="flex items-center gap-2 text-xs">
            <span className="text-muted-foreground/60">Réf:</span>
            <span className="font-mono text-foreground/80">
              {ticket.reference_piece}
            </span>
          </div>
        )}

        <p className="text-sm text-muted-foreground leading-relaxed line-clamp-2">
          {ticket.action_requise}
        </p>

        {/* Footer */}
        <div className="flex items-center justify-between pt-3 border-t border-border/30">
          <span className="text-xs text-muted-foreground/60 flex items-center gap-1.5">
            <Clock className="w-3 h-3" />
            {formatTime(ticket.createdAt)}
          </span>
          <div className={cn(
            "w-1.5 h-1.5 rounded-full",
            config.color,
            "bg-current animate-pulse"
          )} />
        </div>
      </div>
    </Card>
  )
}
