"use client"

import * as React from "react"
import { Check, X } from "lucide-react"
import { cn } from "@/lib/utils"

interface Notification {
  id: string
  type: 'slack' | 'sap'
  title: string
  description: string
  timestamp: Date
}

interface NotificationsPanelProps {
  notifications: Notification[]
}

export function NotificationsPanel({ notifications }: NotificationsPanelProps) {
  if (notifications.length === 0) return null

  return (
    <div className="fixed top-20 right-4 z-40 space-y-2 w-72">
      {notifications.map((notif, index) => (
        <div
          key={notif.id}
          className={cn(
            "bg-neutral-900 border border-neutral-800 rounded-lg p-3 shadow-xl",
            "animate-in slide-in-from-right duration-300"
          )}
          style={{ animationDelay: `${index * 100}ms` }}
        >
          <div className="flex items-start gap-3">
            {/* Icon */}
            <div className={cn(
              "w-8 h-8 rounded-lg flex items-center justify-center flex-shrink-0",
              notif.type === 'slack' ? "bg-[#4A154B]" : "bg-[#0070D1]"
            )}>
              {notif.type === 'slack' ? (
                <svg viewBox="0 0 24 24" className="w-4 h-4 text-white" fill="currentColor">
                  <path d="M5.042 15.165a2.528 2.528 0 0 1-2.52 2.523A2.528 2.528 0 0 1 0 15.165a2.527 2.527 0 0 1 2.522-2.52h2.52v2.52zM6.313 15.165a2.527 2.527 0 0 1 2.521-2.52 2.527 2.527 0 0 1 2.521 2.52v6.313A2.528 2.528 0 0 1 8.834 24a2.528 2.528 0 0 1-2.521-2.522v-6.313zM8.834 5.042a2.528 2.528 0 0 1-2.521-2.52A2.528 2.528 0 0 1 8.834 0a2.528 2.528 0 0 1 2.521 2.522v2.52H8.834zM8.834 6.313a2.528 2.528 0 0 1 2.521 2.521 2.528 2.528 0 0 1-2.521 2.521H2.522A2.528 2.528 0 0 1 0 8.834a2.528 2.528 0 0 1 2.522-2.521h6.312zM18.956 8.834a2.528 2.528 0 0 1 2.522-2.521A2.528 2.528 0 0 1 24 8.834a2.528 2.528 0 0 1-2.522 2.521h-2.522V8.834zM17.688 8.834a2.528 2.528 0 0 1-2.523 2.521 2.527 2.527 0 0 1-2.52-2.521V2.522A2.527 2.527 0 0 1 15.165 0a2.528 2.528 0 0 1 2.523 2.522v6.312zM15.165 18.956a2.528 2.528 0 0 1 2.523 2.522A2.528 2.528 0 0 1 15.165 24a2.527 2.527 0 0 1-2.52-2.522v-2.522h2.52zM15.165 17.688a2.527 2.527 0 0 1-2.52-2.523 2.526 2.526 0 0 1 2.52-2.52h6.313A2.527 2.527 0 0 1 24 15.165a2.528 2.528 0 0 1-2.522 2.523h-6.313z"/>
                </svg>
              ) : (
                <span className="text-white text-xs font-bold">SAP</span>
              )}
            </div>
            
            {/* Content */}
            <div className="flex-1 min-w-0">
              <p className="text-sm font-medium text-white">{notif.title}</p>
              <p className="text-xs text-neutral-400 mt-0.5">{notif.description}</p>
            </div>
            
            {/* Check */}
            <div className="w-5 h-5 rounded-full bg-green-500/20 flex items-center justify-center">
              <Check className="w-3 h-3 text-green-400" />
            </div>
          </div>
        </div>
      ))}
    </div>
  )
}

// SAP Fiori Panel - Realistic simulation
interface SAPPanelProps {
  isOpen: boolean
  onClose: () => void
  tickets: Array<{
    id: string
    objet: string
    reference: string
    gravite: number
    action: string
    timestamp: Date
  }>
}

export function SAPPanel({ isOpen, onClose, tickets }: SAPPanelProps) {
  if (!isOpen) return null

  const getPriorityLabel = (g: number) => {
    if (g >= 5) return { label: "1 - Très élevée", color: "bg-[#bb0000] text-white" }
    if (g >= 4) return { label: "2 - Élevée", color: "bg-[#e78c07] text-white" }
    if (g >= 3) return { label: "3 - Moyenne", color: "bg-[#2b7d2b] text-white" }
    return { label: "4 - Basse", color: "bg-[#5e696e] text-white" }
  }

  return (
    <div className="fixed right-0 top-0 bottom-0 w-96 bg-[#f7f7f7] text-[#32363a] shadow-2xl z-30 flex flex-col font-['72',Arial,sans-serif]">
      {/* SAP Shell Bar */}
      <div className="bg-[#354a5f] h-11 flex items-center px-3 gap-3">
        {/* Close button */}
        <button 
          onClick={onClose}
          className="w-8 h-8 flex items-center justify-center text-white/70 hover:text-white hover:bg-white/10 rounded transition-colors"
        >
          <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
          </svg>
        </button>
        <div className="h-6 w-px bg-white/30" />
        {/* SAP Logo - Text version */}
        <div className="flex items-center gap-2">
          <span className="text-white font-bold text-lg tracking-tight">SAP</span>
        </div>
        <div className="h-6 w-px bg-white/30" />
        <span className="text-white text-sm font-light">S/4HANA</span>
        <div className="flex-1" />
        <div className="flex items-center gap-2">
          <div className="w-8 h-8 rounded-full bg-[#6a6d70] flex items-center justify-center text-white text-xs font-medium">
            PM
          </div>
        </div>
      </div>
      
      {/* Page Header */}
      <div className="bg-white border-b border-[#e5e5e5] px-4 py-3">
        <div className="flex items-center gap-2 text-xs text-[#0854a0] mb-2">
          <span className="hover:underline cursor-pointer">Accueil</span>
          <span className="text-[#6a6d70]">/</span>
          <span className="hover:underline cursor-pointer">Plant Maintenance</span>
          <span className="text-[#6a6d70]">/</span>
          <span className="text-[#32363a]">Notifications</span>
        </div>
        <h1 className="text-xl font-normal text-[#32363a]">Notifications de maintenance</h1>
        <p className="text-xs text-[#6a6d70] mt-1">{tickets.length} élément(s)</p>
      </div>
      
      {/* Toolbar */}
      <div className="bg-white border-b border-[#e5e5e5] px-4 py-2 flex items-center gap-2">
        <button className="px-3 py-1.5 text-xs border border-[#0854a0] text-[#0854a0] rounded hover:bg-[#0854a0]/5">
          + Créer
        </button>
        <button className="px-3 py-1.5 text-xs border border-[#bcc3ca] text-[#32363a] rounded hover:bg-[#e5e5e5]">
          Filtrer
        </button>
        <button className="px-3 py-1.5 text-xs border border-[#bcc3ca] text-[#32363a] rounded hover:bg-[#e5e5e5]">
          Trier
        </button>
        <div className="flex-1" />
        <button className="px-3 py-1.5 text-xs border border-[#bcc3ca] text-[#32363a] rounded hover:bg-[#e5e5e5]">
          ↻ Actualiser
        </button>
      </div>
      
      {/* Table */}
      <div className="flex-1 overflow-y-auto bg-white">
        {/* Table Header */}
        <div className="grid grid-cols-12 gap-2 px-4 py-2 bg-[#f7f7f7] border-b border-[#e5e5e5] text-xs font-semibold text-[#32363a] sticky top-0">
          <div className="col-span-3">Notification</div>
          <div className="col-span-3">Équipement</div>
          <div className="col-span-3">Description</div>
          <div className="col-span-2">Priorité</div>
          <div className="col-span-1">Statut</div>
        </div>
        
        {/* Table Body */}
        {tickets.length === 0 ? (
          <div className="p-8 text-center">
            <div className="w-16 h-16 mx-auto mb-4 bg-[#f7f7f7] rounded-full flex items-center justify-center">
              <svg className="w-8 h-8 text-[#6a6d70]" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5} d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" />
              </svg>
            </div>
            <p className="text-sm text-[#6a6d70]">Aucune notification</p>
            <p className="text-xs text-[#6a6d70] mt-1">Les nouvelles notifications apparaîtront ici</p>
          </div>
        ) : (
          tickets.map((ticket, index) => {
            const priority = getPriorityLabel(ticket.gravite)
            return (
              <div 
                key={ticket.id}
                className={cn(
                  "grid grid-cols-12 gap-2 px-4 py-3 border-b border-[#e5e5e5] text-xs hover:bg-[#e8f4ff] cursor-pointer transition-colors",
                  index === 0 && "bg-[#fff3b8]"
                )}
              >
                <div className="col-span-3">
                  <p className="text-[#0854a0] font-medium hover:underline">{ticket.id}</p>
                  <p className="text-[#6a6d70] text-[10px] mt-0.5">
                    {new Intl.DateTimeFormat("fr-FR", {
                      day: "2-digit",
                      month: "2-digit",
                      year: "numeric"
                    }).format(ticket.timestamp)}
                  </p>
                </div>
                <div className="col-span-3">
                  <p className="font-medium">{ticket.objet}</p>
                  <p className="text-[#6a6d70] text-[10px] mt-0.5">{ticket.reference}</p>
                </div>
                <div className="col-span-3">
                  <p className="text-[#32363a] line-clamp-2">{ticket.action}</p>
                </div>
                <div className="col-span-2">
                  <span className={cn("inline-block px-2 py-0.5 rounded text-[10px] font-medium", priority.color)}>
                    {priority.label}
                  </span>
                </div>
                <div className="col-span-1">
                  <span className="inline-block px-2 py-0.5 rounded text-[10px] bg-[#0854a0] text-white">
                    CRTD
                  </span>
                </div>
              </div>
            )
          })
        )}
      </div>
      
      {/* Footer */}
      <div className="bg-[#f7f7f7] border-t border-[#e5e5e5] px-4 py-2 flex items-center justify-between text-[10px] text-[#6a6d70]">
        <span>Affichage 1-{tickets.length} sur {tickets.length}</span>
        <span>Dernière sync: {new Date().toLocaleTimeString('fr-FR')}</span>
      </div>
    </div>
  )
}
