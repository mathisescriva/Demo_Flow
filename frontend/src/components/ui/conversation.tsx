"use client"

import * as React from "react"
import { StickToBottom, useStickToBottomContext } from "use-stick-to-bottom"
import { ArrowDown, MessageSquare } from "lucide-react"
import { cn } from "@/lib/utils"
import { Button } from "@/components/ui/button"

interface ConversationProps extends React.ComponentProps<typeof StickToBottom> {
  className?: string
}

export function Conversation({ className, children, ...props }: ConversationProps) {
  return (
    <StickToBottom
      className={cn("relative flex flex-col", className)}
      resize="smooth"
      initial="smooth"
      {...props}
    >
      {children}
    </StickToBottom>
  )
}

interface ConversationContentProps
  extends React.ComponentProps<typeof StickToBottom.Content> {
  className?: string
}

export function ConversationContent({
  className,
  children,
  ...props
}: ConversationContentProps) {
  return (
    <StickToBottom.Content
      className={cn("flex flex-col gap-4 p-4", className)}
      {...props}
    >
      {children}
    </StickToBottom.Content>
  )
}

interface ConversationEmptyStateProps
  extends React.HTMLAttributes<HTMLDivElement> {
  title?: string
  description?: string
  icon?: React.ReactNode
}

export function ConversationEmptyState({
  title = "Aucun message",
  description,
  icon,
  className,
  children,
  ...props
}: ConversationEmptyStateProps) {
  if (children) {
    return (
      <div
        className={cn(
          "flex flex-1 flex-col items-center justify-center p-8",
          className
        )}
        {...props}
      >
        {children}
      </div>
    )
  }

  return (
    <div
      className={cn(
        "flex flex-1 flex-col items-center justify-center p-8 text-center",
        className
      )}
      {...props}
    >
      <div className="mb-4 flex h-12 w-12 items-center justify-center rounded-full bg-neutral-800">
        {icon || <MessageSquare className="h-6 w-6 text-neutral-400" />}
      </div>
      <h3 className="text-sm font-medium text-neutral-300">{title}</h3>
      {description && (
        <p className="mt-1 text-xs text-neutral-500">{description}</p>
      )}
    </div>
  )
}

interface ConversationScrollButtonProps
  extends React.ComponentProps<typeof Button> {
  className?: string
}

export function ConversationScrollButton({
  className,
  ...props
}: ConversationScrollButtonProps) {
  const { isAtBottom, scrollToBottom } = useStickToBottomContext()

  if (isAtBottom) return null

  return (
    <Button
      variant="outline"
      size="icon"
      className={cn(
        "absolute bottom-4 left-1/2 -translate-x-1/2 rounded-full bg-neutral-900 border-neutral-700 hover:bg-neutral-800 shadow-lg",
        className
      )}
      onClick={() => scrollToBottom()}
      {...props}
    >
      <ArrowDown className="h-4 w-4" />
    </Button>
  )
}
