"use client"
import {
  Sidebar,
  SidebarContent,
  SidebarFooter,
  SidebarGroup,
  SidebarGroupContent,
  SidebarHeader,
  SidebarRail,
  SidebarSeparator,
} from "@/components/ui/sidebar"
import { Zap, Video, Sparkles, BookOpen, Settings, HelpCircle } from "lucide-react"
import type { ContentSource } from "@/types/api"
import type { NavigationItem } from "@/types/navigation"
import { useViewedItems } from "@/hooks/use-viewed-items"
import { NavigationSection } from "@/components/sidebar/NavigationSection"
import { UserDropdown } from "@/components/sidebar/UserDropdown"

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

const mainNavigation: NavigationItem[] = [
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

const comingSoonNavigation: NavigationItem[] = [
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

const bottomNavigation: NavigationItem[] = [
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


export function AppSidebar({ contents, currentView, onViewChange, onContentSelect, user, onSignOut }: AppSidebarProps) {
  const viewedItems = useViewedItems()

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
            <NavigationSection
              items={mainNavigation}
              currentView={currentView}
              onViewChange={onViewChange}
              readyCount={readyCount}
              readyItemId="library"
            />
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
            <NavigationSection
              items={comingSoonNavigation}
              currentView={currentView}
              onViewChange={onViewChange}
            />
          </SidebarGroupContent>
        </SidebarGroup>

      </SidebarContent>

      {/* Divider above footer */}
      <SidebarSeparator className="bg-warm-gray-200" />

      <SidebarFooter className="p-4 space-y-2">
        <NavigationSection
          items={bottomNavigation}
          currentView={currentView}
          onViewChange={onViewChange}
        />

        <UserDropdown user={user} onSignOut={onSignOut} />
      </SidebarFooter>

      <SidebarRail />
    </Sidebar>
  )
}
