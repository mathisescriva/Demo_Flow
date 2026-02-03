import * as React from "react"
import { cn } from "@/lib/utils"
import { CheckCircle2, X } from "lucide-react"

export interface ToastProps {
  title?: string
  description?: string
  open?: boolean
  onOpenChange?: (open: boolean) => void
}

export function Toast({ title, description, open, onOpenChange }: ToastProps) {
  if (!open) return null

  return (
    <div className="fixed top-4 right-4 z-50 animate-in slide-in-from-top-5">
      <div className="rounded-lg border bg-background p-4 shadow-lg">
        <div className="flex items-start gap-3">
          <CheckCircle2 className="h-5 w-5 text-green-500 flex-shrink-0 mt-0.5" />
          <div className="flex-1">
            {title && <p className="font-semibold text-sm">{title}</p>}
            {description && <p className="text-sm text-muted-foreground mt-1">{description}</p>}
          </div>
          {onOpenChange && (
            <button
              onClick={() => onOpenChange(false)}
              className="text-muted-foreground hover:text-foreground"
            >
              <X className="h-4 w-4" />
            </button>
          )}
        </div>
      </div>
    </div>
  )
}
