import { Card } from '@/components/ui/card'
import { Badge } from '@/components/ui/badge'
import { Zap, AlertTriangle, Info, Clock } from 'lucide-react'
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

interface TicketCardProps {
  ticket: Ticket
  index: number
}

export function TicketCard({ ticket, index }: TicketCardProps) {
  const getGraviteConfig = (gravite: number) => {
    if (gravite >= 5) {
      return {
        color: 'destructive',
        label: 'Urgente',
        icon: Zap,
        bgGradient: 'from-red-500/20 to-orange-500/20',
        borderColor: 'border-red-500/50',
        textColor: 'text-red-500'
      }
    }
    if (gravite >= 4) {
      return {
        color: 'destructive',
        label: 'Critique',
        icon: AlertTriangle,
        bgGradient: 'from-orange-500/20 to-yellow-500/20',
        borderColor: 'border-orange-500/50',
        textColor: 'text-orange-500'
      }
    }
    if (gravite >= 3) {
      return {
        color: 'secondary',
        label: 'Élevée',
        icon: Info,
        bgGradient: 'from-yellow-500/20 to-blue-500/20',
        borderColor: 'border-yellow-500/50',
        textColor: 'text-yellow-500'
      }
    }
    return {
      color: 'outline',
      label: gravite >= 2 ? 'Modérée' : 'Faible',
      icon: Info,
      bgGradient: 'from-blue-500/20 to-cyan-500/20',
      borderColor: 'border-blue-500/50',
      textColor: 'text-blue-500'
    }
  }

  const graviteConfig = getGraviteConfig(ticket.gravite)
  const Icon = graviteConfig.icon

  const formatTime = (date: Date) => {
    return new Intl.DateTimeFormat('fr-FR', {
      hour: '2-digit',
      minute: '2-digit'
    }).format(date)
  }

  return (
    <Card
      className={cn(
        "border-2 p-4 transition-all duration-500 animate-in slide-in-from-right",
        graviteConfig.borderColor,
        `bg-gradient-to-br ${graviteConfig.bgGradient}`
      )}
      style={{
        animationDelay: `${index * 100}ms`
      }}
    >
      <div className="space-y-3">
        <div className="flex items-start justify-between gap-2">
          <div className="flex-1 min-w-0">
            <div className="flex items-center gap-2 mb-2 flex-wrap">
              <span className="text-xs font-mono text-muted-foreground bg-background/80 px-2 py-0.5 rounded">
                {ticket.id}
              </span>
              <Badge
                variant={graviteConfig.color as any}
                className={cn("text-xs font-semibold", graviteConfig.textColor)}
              >
                <Icon className="w-3 h-3 mr-1" />
                {graviteConfig.label}
              </Badge>
            </div>
            <h3 className="text-base font-semibold leading-tight mb-1">
              {ticket.objet}
            </h3>
          </div>
        </div>

        {ticket.reference_piece && (
          <div className="flex items-center gap-2 text-xs">
            <span className="text-muted-foreground">Réf:</span>
            <span className="font-mono bg-background/80 px-2 py-0.5 rounded">
              {ticket.reference_piece}
            </span>
          </div>
        )}

        <p className="text-xs text-muted-foreground leading-relaxed line-clamp-2">
          {ticket.action_requise}
        </p>

        <div className="flex items-center justify-between pt-2 border-t border-border/50">
          <span className="text-xs text-muted-foreground flex items-center gap-1">
            <Clock className="w-3 h-3" />
            {formatTime(ticket.createdAt)}
          </span>
          <div className={cn(
            "w-2 h-2 rounded-full",
            graviteConfig.textColor,
            "bg-current animate-pulse"
          )} />
        </div>
      </div>
    </Card>
  )
}
