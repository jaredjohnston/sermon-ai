"use client"
import { useState, useEffect } from "react"
import {
  Sidebar,
  SidebarContent,
  SidebarFooter,
  SidebarGroup,
  SidebarGroupContent,
  SidebarHeader,
  SidebarMenu,
  SidebarMenuButton,
  SidebarMenuItem,
  SidebarRail,
  SidebarSeparator,
} from "@/components/ui/sidebar"
import { Settings, HelpCircle, User, LogOut, Clock, Zap, Video, Mic, Sparkles, BookOpen, CreditCard, UserPlus, MessageSquare, TrendingUp } from "lucide-react"
import Image from "next/image"
import { Button } from "@/components/ui/button"
import { 
  DropdownMenu, 
  DropdownMenuContent, 
  DropdownMenuItem, 
  DropdownMenuTrigger 
} from "@/components/ui/dropdown-menu"
import { Avatar, AvatarFallback } from "@/components/ui/avatar"
import type { ContentSource } from "@/types/api"

interface AppSidebarProps {
  contents: ContentSource[]
  currentView: string
  onViewChange: (view: string) => void
  onContentSelect: (content: ContentSource) => void
  user?: { email?: string } | null
  onSignOut: () => void
}

// Traditional Upload Icon - Simple upward arrow with base line
function FileUploadIcon({ className }: { className?: string }) {
  return (
    <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="none" className={className}>
      {/* Upload arrow shaft */}
      <path d="M12 15V3" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" />

      {/* Arrow head */}
      <path d="M7 8l5-5 5 5" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" />

      {/* Base platform/ground line */}
      <path
        d="M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4"
        stroke="currentColor"
        strokeWidth="2"
        strokeLinecap="round"
        strokeLinejoin="round"
      />
    </svg>
  )
}

const mainNavigation = [
  {
    title: "Upload Sermon",
    icon: FileUploadIcon,
    id: "dashboard",
    description: "Upload sermon files",
  },
  {
    title: "Create Content",
    icon: Sparkles,
    id: "library",
    description: "Your content library",
  },
  {
    title: "Templates",
    icon: BookOpen,
    id: "voice-style",
    description: "Content templates",
  },
]

const comingSoonNavigation = [
  {
    title: "AI Research",
    icon: Zap,
    id: "assistant",
    description: "AI research assistant",
  },
  {
    title: "Create Social Clips",
    icon: Video,
    id: "video-clips",
    description: "Social media content",
  },
]

const bottomNavigation = [
  {
    title: "Settings",
    icon: Settings,
    id: "settings",
  },
  {
    title: "Help",
    icon: HelpCircle,
    id: "help",
  },
]


// Utility functions for localStorage operations
const VIEWED_ITEMS_KEY = 'churchable-viewed-items'

const loadViewedItems = (): Set<string> => {
  if (typeof window === 'undefined') return new Set()
  try {
    const stored = localStorage.getItem(VIEWED_ITEMS_KEY)
    return stored ? new Set(JSON.parse(stored)) : new Set()
  } catch {
    return new Set()
  }
}

export function AppSidebar({ contents, currentView, onViewChange, onContentSelect, user, onSignOut }: AppSidebarProps) {
  const [viewedItems, setViewedItems] = useState<Set<string>>(new Set())

  // Load viewed items on mount and listen for localStorage changes
  useEffect(() => {
    setViewedItems(loadViewedItems())

    // Listen for storage changes (when content-library updates viewed items)
    const handleStorageChange = (e: StorageEvent) => {
      if (e.key === VIEWED_ITEMS_KEY) {
        setViewedItems(loadViewedItems())
      }
    }

    // Listen for custom events from same tab (localStorage events only fire for other tabs)
    const handleViewedItemsUpdate = () => {
      setViewedItems(loadViewedItems())
    }

    window.addEventListener('storage', handleStorageChange)
    window.addEventListener('viewed-items-updated', handleViewedItemsUpdate)

    return () => {
      window.removeEventListener('storage', handleStorageChange)
      window.removeEventListener('viewed-items-updated', handleViewedItemsUpdate)
    }
  }, [])

  // Count ready transcripts that haven't been viewed
  const readyCount = contents.filter(c => 
    c.status === 'completed' && 
    (!c.content || c.content.length === 0) &&
    !viewedItems.has(c.id)
  ).length
  return (
    <Sidebar collapsible="icon" className="bg-warm-white">
      <SidebarHeader className="">
        <div className="flex items-center px-6 py-4">
          <div className="flex items-center gap-2">
            <div className="w-6 h-6 bg-primary rounded-md flex items-center justify-center">
              <span className="text-white font-black text-xs">C</span>
            </div>
            <span className="font-black text-lg text-warm-gray-900">CHURCHABLE</span>
          </div>
        </div>
      </SidebarHeader>

      <SidebarContent className="px-4 pt-2 pb-4">
        {/* Main Content Creation Section */}
        <SidebarGroup>
          <div className="px-2 py-2 mb-2">
            <h4 className="text-xs font-black text-warm-gray-600 uppercase tracking-wider">CONTENT</h4>
          </div>
          <SidebarGroupContent>
            <SidebarMenu className="space-y-1">
              {mainNavigation.map((item) => {
                const Icon = item.icon
                const isActive = currentView === item.id

                return (
                  <SidebarMenuItem key={item.id}>
                    <SidebarMenuButton
                      isActive={isActive}
                      onClick={() => onViewChange(item.id)}
                      tooltip={item.description}
                      className="text-sm h-9 px-3 rounded-xl transition-all duration-200 hover:bg-stone-200"
                    >
                      <Icon className={`h-4 w-4 ${isActive ? 'text-brand-blue' : 'text-gray-500'}`} />
                      <span className="flex-1 text-left">{item.title}</span>
                      {item.id === 'library' && readyCount > 0 && (
                        <span className="ml-auto bg-primary text-white text-xs font-bold rounded-full px-2 py-0.5 min-w-[1.5rem] text-center">
                          {readyCount}
                        </span>
                      )}
                    </SidebarMenuButton>
                  </SidebarMenuItem>
                )
              })}
            </SidebarMenu>
          </SidebarGroupContent>
        </SidebarGroup>

        {/* Visual Divider */}
        <SidebarSeparator className="my-6 bg-warm-gray-200" />

        {/* Coming Soon Section */}
        <SidebarGroup>
          <div className="px-2 py-2 mb-2">
            <h4 className="text-xs font-black text-warm-gray-600 uppercase tracking-wider">COMING SOON</h4>
          </div>
          <SidebarGroupContent>
            <SidebarMenu className="space-y-1">
              {comingSoonNavigation.map((item) => {
                const Icon = item.icon
                const isActive = currentView === item.id
                return (
                  <SidebarMenuItem key={item.id}>
                    <SidebarMenuButton
                      isActive={isActive}
                      onClick={() => onViewChange(item.id)}
                      className="text-sm h-9 px-3 rounded-xl transition-all duration-200 hover:bg-stone-200"
                    >
                      <Icon className={`h-4 w-4 ${isActive ? 'text-brand-blue' : 'text-gray-500'}`} />
                      <span>{item.title}</span>
                    </SidebarMenuButton>
                  </SidebarMenuItem>
                )
              })}
            </SidebarMenu>
          </SidebarGroupContent>
        </SidebarGroup>

      </SidebarContent>

      {/* Divider above footer */}
      <SidebarSeparator className="bg-warm-gray-200" />

      <SidebarFooter className="p-4 space-y-2">
        <SidebarMenu className="space-y-1">
          {bottomNavigation.map((item) => {
            const Icon = item.icon
            const isActive = currentView === item.id
            return (
              <SidebarMenuItem key={item.id}>
                <SidebarMenuButton
                  isActive={isActive}
                  onClick={() => onViewChange(item.id)}
                  className="text-sm h-9 px-3 rounded-xl transition-all duration-200 hover:bg-stone-200"
                >
                  <Icon className={`h-4 w-4 ${isActive ? 'text-brand-blue' : 'text-gray-500'}`} />
                  <span>{item.title}</span>
                </SidebarMenuButton>
              </SidebarMenuItem>
            )
          })}
        </SidebarMenu>

        {/* User dropdown */}
        <div>
          <DropdownMenu>
            <DropdownMenuTrigger asChild>
              <Button variant="ghost" className="w-full justify-start h-9 px-3 rounded-xl hover:bg-stone-200">
                <Avatar className="h-6 w-6 mr-3">
                  <AvatarFallback className="text-xs">
                    {user?.email?.substring(0, 2).toUpperCase() || 'U'}
                  </AvatarFallback>
                </Avatar>
                <span className="text-sm text-gray-700 truncate">{user?.email || 'User'}</span>
              </Button>
            </DropdownMenuTrigger>
            <DropdownMenuContent className="w-64" align="start" side="right">
              {/* Header with user info */}
              <div className="flex items-center gap-3 p-3 border-b">
                <Avatar className="h-8 w-8">
                  <AvatarFallback className="text-sm">
                    {user?.email?.substring(0, 1).toUpperCase() || 'C'}
                  </AvatarFallback>
                </Avatar>
                <span className="font-medium text-gray-900">Churchable</span>
              </div>

              {/* Settings section */}
              <div className="py-1">
                <DropdownMenuItem>
                  <User className="mr-3 h-4 w-4" />
                  <span>My settings</span>
                </DropdownMenuItem>
                <DropdownMenuItem>
                  <Settings className="mr-3 h-4 w-4" />
                  <span>Team settings</span>
                </DropdownMenuItem>
                <DropdownMenuItem>
                  <UserPlus className="mr-3 h-4 w-4" />
                  <span>Invite members</span>
                </DropdownMenuItem>
                <DropdownMenuItem>
                  <CreditCard className="mr-3 h-4 w-4" />
                  <span>Plan & Billing</span>
                </DropdownMenuItem>
              </div>

              {/* Divider */}
              <div className="border-b my-1"></div>

              {/* Additional options */}
              <div className="py-1">
                <DropdownMenuItem>
                  <TrendingUp className="mr-3 h-4 w-4" />
                  <span>Upgrade plan</span>
                </DropdownMenuItem>
                <DropdownMenuItem>
                  <MessageSquare className="mr-3 h-4 w-4" />
                  <span>Feedback</span>
                </DropdownMenuItem>
              </div>

              {/* Divider */}
              <div className="border-b my-1"></div>

              {/* Sign out */}
              <div className="py-1">
                <DropdownMenuItem onClick={onSignOut}>
                  <LogOut className="mr-3 h-4 w-4" />
                  <span>Sign out</span>
                </DropdownMenuItem>
              </div>
            </DropdownMenuContent>
          </DropdownMenu>
        </div>
      </SidebarFooter>

      <SidebarRail />
    </Sidebar>
  )
}
