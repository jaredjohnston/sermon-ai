"use client"
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
import { Settings, HelpCircle, User, LogOut, Clock, Zap, Video, Mic, Sparkles, BookOpen } from "lucide-react"
import Image from "next/image"
import type { ContentSource } from "@/types/api"

interface AppSidebarProps {
  sermons: ContentSource[]
  currentView: string
  onViewChange: (view: string) => void
  onSermonSelect: (sermon: ContentSource) => void
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


export function AppSidebar({ sermons, currentView, onViewChange, onSermonSelect }: AppSidebarProps) {
  return (
    <Sidebar collapsible="icon" className="border-r border-warm-gray-200 bg-warm-gray-50">
      <SidebarHeader className="border-b border-warm-gray-200 bg-white">
        <div className="flex items-center px-6 py-6">
          <div className="flex items-center gap-2">
            <div className="w-8 h-8 bg-primary rounded-lg flex items-center justify-center">
              <span className="text-white font-black text-sm">C</span>
            </div>
            <span className="font-black text-2xl text-warm-gray-900">CHURCHABLE</span>
          </div>
        </div>
      </SidebarHeader>

      <SidebarContent className="p-4">
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
                      className={`font-semibold text-sm h-10 px-3 rounded-lg transition-all duration-200 hover:bg-white hover:shadow-sm ${
                        isActive ? 'bg-white shadow-sm' : ''
                      }`}
                    >
                      <Icon className={`h-4 w-4 ${isActive ? 'text-primary' : ''}`} />
                      <span>{item.title.toUpperCase()}</span>
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
                      className={`font-semibold text-sm h-10 px-3 rounded-lg transition-all duration-200 hover:bg-white hover:shadow-sm ${
                        isActive ? 'bg-white shadow-sm' : ''
                      }`}
                    >
                      <Icon className={`h-4 w-4 ${isActive ? 'text-primary' : ''}`} />
                      <span>{item.title.toUpperCase()}</span>
                    </SidebarMenuButton>
                  </SidebarMenuItem>
                )
              })}
            </SidebarMenu>
          </SidebarGroupContent>
        </SidebarGroup>

      </SidebarContent>

      <SidebarFooter className="border-t border-warm-gray-200 bg-white p-4">
        <SidebarMenu className="space-y-1">
          {bottomNavigation.map((item) => {
            const Icon = item.icon
            const isActive = currentView === item.id
            return (
              <SidebarMenuItem key={item.id}>
                <SidebarMenuButton
                  isActive={isActive}
                  onClick={() => onViewChange(item.id)}
                  className={`font-semibold text-sm h-10 px-3 rounded-lg transition-all duration-200 hover:bg-warm-gray-50 ${
                    isActive ? 'bg-warm-gray-50' : ''
                  }`}
                >
                  <Icon className={`h-4 w-4 ${isActive ? 'text-primary' : ''}`} />
                  <span>{item.title.toUpperCase()}</span>
                </SidebarMenuButton>
              </SidebarMenuItem>
            )
          })}
        </SidebarMenu>
      </SidebarFooter>

      <SidebarRail />
    </Sidebar>
  )
}
