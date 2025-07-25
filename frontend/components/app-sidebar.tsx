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
import { Settings, HelpCircle, User, LogOut, Clock, Zap, Video, Mic } from "lucide-react"
import Image from "next/image"
import type { SermonData } from "@/types/api"

interface AppSidebarProps {
  sermons: SermonData[]
  currentView: string
  onViewChange: (view: string) => void
  onSermonSelect: (sermon: SermonData) => void
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
    title: "Create Content",
    icon: FileUploadIcon,
    id: "dashboard",
    description: "Upload & create content",
  },
  {
    title: "Recently Created",
    icon: Clock,
    id: "library",
    description: "Your content library",
  },
  {
    title: "AI Assistant",
    icon: Zap,
    id: "assistant",
    description: "Sermon assistant",
  },
  {
    title: "Create Social Clips",
    icon: Video,
    id: "video-clips",
    description: "Social media content",
  },
]

const userNavigation = [
  {
    title: "Voice & Style",
    icon: Mic,
    id: "voice-style",
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
    <Sidebar collapsible="icon" className="border-r-2 border-warm-gray-800 bg-warm-gray-50">
      <SidebarHeader className="border-b-2 border-warm-gray-800 bg-card">
        <div className="flex items-center px-4 py-4">
          <span className="font-black text-lg zorp-text-blue">CHURCHABLE</span>
        </div>
      </SidebarHeader>

      <SidebarContent className="bg-warm-gray-50">
        {/* Main Content Creation Section */}
        <SidebarGroup>
          <SidebarGroupContent>
            <SidebarMenu>
              {mainNavigation.map((item) => {
                const Icon = item.icon
                const isActive = currentView === item.id

                return (
                  <SidebarMenuItem key={item.id}>
                    <SidebarMenuButton
                      isActive={isActive}
                      onClick={() => onViewChange(item.id)}
                      tooltip={item.description}
                      className={`
                        font-bold transition-colors hover:bg-card
                        ${isActive ? "bg-card border-l-4 text-white" : "text-warm-gray-700"}
                      `}
                      style={isActive ? { borderLeftColor: "#0000ee", color: "#0000ee" } : {}}
                    >
                      <Icon className="h-4 w-4" style={{ color: "#0000ee" }} />
                      <span>{item.title.toUpperCase()}</span>
                    </SidebarMenuButton>
                  </SidebarMenuItem>
                )
              })}
            </SidebarMenu>
          </SidebarGroupContent>
        </SidebarGroup>

        {/* Visual Divider */}
        <SidebarSeparator className="my-2" />

        {/* User Preferences Section */}
        <SidebarGroup>
          <SidebarGroupContent>
            <SidebarMenu>
              {userNavigation.map((item) => {
                const Icon = item.icon
                const isActive = currentView === item.id
                return (
                  <SidebarMenuItem key={item.id}>
                    <SidebarMenuButton
                      isActive={isActive}
                      onClick={() => onViewChange(item.id)}
                      className={`
                        font-bold transition-colors hover:bg-card
                        ${isActive ? "bg-card border-l-4 text-white" : "text-warm-gray-700"}
                      `}
                      style={isActive ? { borderLeftColor: "#0000ee", color: "#0000ee" } : {}}
                    >
                      <Icon className="h-4 w-4" style={{ color: "#0000ee" }} />
                      <span>{item.title.toUpperCase()}</span>
                    </SidebarMenuButton>
                  </SidebarMenuItem>
                )
              })}
            </SidebarMenu>
          </SidebarGroupContent>
        </SidebarGroup>

      </SidebarContent>

      <SidebarFooter className="border-t-2 border-warm-gray-800 bg-card">
        <SidebarMenu>
          {bottomNavigation.map((item) => {
            const Icon = item.icon
            const isActive = currentView === item.id
            return (
              <SidebarMenuItem key={item.id}>
                <SidebarMenuButton
                  isActive={isActive}
                  onClick={() => onViewChange(item.id)}
                  className={`
                    font-bold transition-colors hover:bg-warm-gray-100
                    ${isActive ? "bg-warm-gray-100 border-l-4" : "text-warm-gray-700"}
                  `}
                  style={isActive ? { borderLeftColor: "#0000ee", color: "#0000ee" } : {}}
                >
                  <Icon className="h-4 w-4 text-warm-gray-700" />
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
