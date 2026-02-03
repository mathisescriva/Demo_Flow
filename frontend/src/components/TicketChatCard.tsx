import { Card } from '@/components/ui/card'
import { Badge } from '@/components/ui/badge'
import { Zap, AlertTriangle, Info, ArrowRight } from 'lucide-react'
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

interface TicketChatCardProps {
  ticket: Ticket
  index: number
}

export function TicketChatCard({ ticket, index }: TicketChatCardProps) {
  const getGraviteConfig = (gravite: number) => {
    if (gravite >= 5) {
      return {
        label: 'Urgente',
        icon: Zap,
        color: 'text-red-400',
        bg: 'bg-red-500/10',
        border: 'border-red-500/30',
        glow: 'shadow-red-500/20'
      }
    }
    if (gravite >= 4) {
      return {
        label: 'Critique',
        icon: AlertTriangle,
        color: 'text-orange-400',
        bg: 'bg-orange-500/10',
        border: 'border-orange-500/30',
        glow: 'shadow-orange-500/20'
      }
    }
    if (gravite >= 3) {
      return {
        label: 'Élevée',
        icon: Info,
        color: 'text-yellow-400',
        bg: 'bg-yellow-500/10',
        border: 'border-yellow-500/30',
        glow: 'shadow-yellow-500/20'
      }
    }
    return {
      label: gravite >= 2 ? 'Modérée' : 'Faible',
      icon: Info,
      color: 'text-blue-400',
      bg: 'bg-blue-500/10',
      border: 'border-blue-500/30',
      glow: 'shadow-blue-500/20'
    }
  }

  const config = getGraviteConfig(ticket.gravite)
  const Icon = config.icon

  return (
    <div className="flex justify-start mb-4 animate-in slide-in-from-left">
      <div className="max-w-[85%] w-full">
        <Card
          className={cn(
            "group relative overflow-hidden border backdrop-blur-xl bg-background/60 transition-all duration-300 hover:scale-[1.02] hover:shadow-lg",
            config.border,
            config.glow
          )}
          style={{
            animationDelay: `${index * 100}ms`
          }}
        >
          <div className={cn("absolute inset-0 opacity-0 group-hover:opacity-100 transition-opacity", config.bg)} />
          
          <div className="relative p-4 space-y-3">
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
                <h3 className="text-sm font-semibold leading-tight mb-1">
                  {ticket.objet}
                </h3>
                {ticket.reference_piece && (
                  <p className="text-xs text-muted-foreground/70 mb-1">
                    Réf: <span className="font-mono">{ticket.reference_piece}</span>
                  </p>
                )}
                <p className="text-xs text-muted-foreground/80 leading-relaxed">
                  {ticket.action_requise}
                </p>
              </div>
              <ArrowRight className="w-4 h-4 text-muted-foreground/40 group-hover:text-foreground transition-colors flex-shrink-0" />
            </div>
          </div>
        </Card>
      </div>
    </div>
  )
}
