import { useState } from 'react'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
import { Button } from '@/components/ui/button'
import { Badge } from '@/components/ui/badge'
import { Play, CheckCircle2 } from 'lucide-react'

interface ScenarioStep {
  id: number
  text: string
  completed: boolean
}

interface ScenarioDemoProps {
  onScenarioSelect: (text: string) => void
  currentStep: number | null
}

const scenarios: ScenarioStep[] = [
  {
    id: 1,
    text: "Hugo ici, j'ai une fuite sur la vanne V12, commande un kit de joint et mets l'alerte au max",
    completed: false
  },
  {
    id: 2,
    text: "La pompe P5 fait un bruit anormal, vérifie le roulement et prévois une maintenance préventive niveau 3",
    completed: false
  },
  {
    id: 3,
    text: "Problème sur le compresseur C8, température trop élevée, arrêt d'urgence nécessaire, gravité maximale",
    completed: false
  },
  {
    id: 4,
    text: "Le capteur de pression S3 envoie des valeurs erronées, remplacement requis, priorité normale",
    completed: false
  }
]

export function ScenarioDemo({ onScenarioSelect, currentStep }: ScenarioDemoProps) {
  const [completedSteps, setCompletedSteps] = useState<number[]>([])

  const handleScenarioClick = (step: ScenarioStep) => {
    onScenarioSelect(step.text)
    if (!completedSteps.includes(step.id)) {
      setCompletedSteps([...completedSteps, step.id])
    }
  }

  return (
    <Card>
      <CardHeader>
        <CardTitle>Scénario de Démonstration</CardTitle>
        <CardDescription>
          Sélectionnez une requête pour voir le CRM se remplir en temps réel
        </CardDescription>
      </CardHeader>
      <CardContent>
        <div className="space-y-3">
          {scenarios.map((step) => {
            const isCompleted = completedSteps.includes(step.id)
            const isActive = currentStep === step.id
            
            return (
              <Button
                key={step.id}
                variant={isActive ? "default" : "outline"}
                className="w-full justify-start h-auto py-3 px-4 text-left"
                onClick={() => handleScenarioClick(step)}
              >
                <div className="flex items-start gap-3 w-full">
                  <div className={isCompleted ? "text-green-500" : "text-muted-foreground"}>
                    {isCompleted ? (
                      <CheckCircle2 className="w-5 h-5" />
                    ) : (
                      <Play className="w-5 h-5" />
                    )}
                  </div>
                  <div className="flex-1">
                    <div className="flex items-center gap-2 mb-1">
                      <span className="font-semibold">Requête {step.id}</span>
                      {isCompleted && (
                        <Badge variant="outline" className="text-xs">✓ Traitée</Badge>
                      )}
                      {isActive && (
                        <Badge variant="default" className="text-xs">En cours...</Badge>
                      )}
                    </div>
                    <p className="text-sm text-muted-foreground">{step.text}</p>
                  </div>
                </div>
              </Button>
            )
          })}
        </div>
      </CardContent>
    </Card>
  )
}
