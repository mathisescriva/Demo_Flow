import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'
import { Badge } from '@/components/ui/badge'
import { Separator } from '@/components/ui/separator'
import { Clock, CheckCircle2, AlertTriangle, Info, Zap } from 'lucide-react'
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

interface TicketListProps {
  tickets: Ticket[]
}

export function TicketList({ tickets }: TicketListProps) {
  const getGraviteConfig = (gravite: number) => {
    if (gravite >= 5) {
      return {
        color: 'destructive',
        label: 'Urgente',
        icon: Zap,
        bgColor: 'bg-red-500/10',
        borderColor: 'border-red-500/50',
        textColor: 'text-red-500'
      }
    }
    if (gravite >= 4) {
      return {
        color: 'destructive',
        label: 'Critique',
        icon: AlertTriangle,
        bgColor: 'bg-orange-500/10',
        borderColor: 'border-orange-500/50',
        textColor: 'text-orange-500'
      }
    }
    if (gravite >= 3) {
      return {
        color: 'secondary',
        label: 'Élevée',
        icon: Info,
        bgColor: 'bg-yellow-500/10',
        borderColor: 'border-yellow-500/50',
        textColor: 'text-yellow-500'
      }
    }
    return {
      color: 'outline',
      label: gravite >= 2 ? 'Modérée' : 'Faible',
      icon: Info,
      bgColor: 'bg-blue-500/10',
      borderColor: 'border-blue-500/50',
      textColor: 'text-blue-500'
    }
  }

  const formatDate = (date: Date) => {
    return new Intl.DateTimeFormat('fr-FR', {
      hour: '2-digit',
      minute: '2-digit',
      second: '2-digit'
    }).format(date)
  }

  if (tickets.length === 0) {
    return (
      <Card className="border-dashed">
        <CardHeader>
          <CardTitle className="text-lg">Tickets CRM</CardTitle>
        </CardHeader>
        <CardContent>
          <div className="flex flex-col items-center justify-center py-12">
            <div className="w-16 h-16 rounded-full bg-muted flex items-center justify-center mb-4">
              <Clock className="w-8 h-8 text-muted-foreground" />
            </div>
            <p className="text-sm text-muted-foreground text-center">
              Aucun ticket créé
            </p>
            <p className="text-xs text-muted-foreground text-center mt-1">
              Parlez pour créer un ticket
            </p>
          </div>
        </CardContent>
      </Card>
    )
  }

  return (
    <Card>
      <CardHeader>
        <div className="flex items-center justify-between">
          <CardTitle className="text-lg">Tickets CRM</CardTitle>
          <Badge variant="secondary" className="text-xs">
            {tickets.length} {tickets.length > 1 ? 'tickets' : 'ticket'}
          </Badge>
        </div>
      </CardHeader>
      <CardContent>
        <div className="space-y-3">
          {tickets.map((ticket, index) => {
            const graviteConfig = getGraviteConfig(ticket.gravite)
            const Icon = graviteConfig.icon

            return (
              <div
                key={ticket.id}
                className={cn(
                  "group relative rounded-lg border p-4 transition-all duration-300 hover:shadow-lg",
                  graviteConfig.bgColor,
                  graviteConfig.borderColor,
                  "border"
                )}
              >
                <div className="space-y-3">
                  {/* Header */}
                  <div className="flex items-start justify-between gap-3">
                    <div className="flex-1 min-w-0">
                      <div className="flex items-center gap-2 mb-2 flex-wrap">
                        <span className="text-xs font-mono text-muted-foreground bg-background/50 px-2 py-0.5 rounded">
                          {ticket.id}
                        </span>
                        <Badge 
                          variant={graviteConfig.color as any}
                          className={cn("text-xs font-semibold", graviteConfig.textColor)}
                        >
                          <Icon className="w-3 h-3 mr-1" />
                          {graviteConfig.label}
                        </Badge>
                        {ticket.status === 'new' && (
                          <Badge variant="outline" className="text-xs bg-green-500/10 border-green-500/50 text-green-500">
                            <CheckCircle2 className="w-3 h-3 mr-1" />
                            Nouveau
                          </Badge>
                        )}
                      </div>
                      <h3 className="text-sm font-semibold leading-tight mb-1">
                        {ticket.objet}
                      </h3>
                    </div>
                  </div>

                  {/* Content */}
                  <div className="space-y-2">
                    {ticket.reference_piece && (
                      <div className="flex items-center gap-2 text-xs">
                        <span className="text-muted-foreground">Réf:</span>
                        <span className="font-mono bg-background/50 px-2 py-0.5 rounded">
                          {ticket.reference_piece}
                        </span>
                      </div>
                    )}
                    <p className="text-xs text-muted-foreground leading-relaxed">
                      {ticket.action_requise}
                    </p>
                  </div>

                  {/* Footer */}
                  <div className="flex items-center justify-between pt-2 border-t border-border/50">
                    <span className="text-xs text-muted-foreground">
                      {formatDate(ticket.createdAt)}
                    </span>
                    <div className="flex items-center gap-1">
                      <div className={cn(
                        "w-2 h-2 rounded-full",
                        graviteConfig.textColor,
                        "bg-current animate-pulse"
                      )} />
                      <span className="text-xs text-muted-foreground">Actif</span>
                    </div>
                  </div>
                </div>
              </div>
            )
          })}
        </div>
      </CardContent>
    </Card>
  )
}
