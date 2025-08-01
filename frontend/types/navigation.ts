import { LucideIcon } from "lucide-react"

export interface NavigationItem {
  title: string
  icon: LucideIcon
  id: string
  description?: string
}

export interface NavigationSectionProps {
  items: NavigationItem[]
  currentView: string
  onViewChange: (view: string) => void
  readyCount?: number
  readyItemId?: string
}