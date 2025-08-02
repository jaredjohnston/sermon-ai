"use client"
import {
  Sidebar,
  SidebarContent,
  SidebarFooter,
  SidebarHeader,
  SidebarRail,
  SidebarSeparator,
  useSidebar,
} from "@/components/ui/sidebar"
import { 
  ArrowUpOnSquareIcon, 
  SparklesIcon, 
  DocumentTextIcon, 
  BoltIcon, 
  VideoCameraIcon,
  Cog6ToothIcon,
  ChatBubbleOvalLeftEllipsisIcon 
} from "@heroicons/react/24/solid"
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


const mainNavigation: NavigationItem[] = [
  {
    title: "Upload Sermon",
    icon: ArrowUpOnSquareIcon,
    id: "dashboard",
    description: "Upload sermon files",
  },
  {
    title: "Create Content",
    icon: SparklesIcon,
    id: "library",
    description: "Your content library",
  },
  {
    title: "Templates",
    icon: DocumentTextIcon,
    id: "voice-style",
    description: "Content templates",
  },
]

const comingSoonNavigation: NavigationItem[] = [
  {
    title: "AI Research",
    icon: BoltIcon,
    id: "assistant",
    description: "AI research assistant",
  },
  {
    title: "Create Social Clips",
    icon: VideoCameraIcon,
    id: "video-clips",
    description: "Social media content",
  },
]

const bottomNavigation: NavigationItem[] = [
  {
    title: "Settings",
    icon: Cog6ToothIcon,
    id: "settings",
  },
  {
    title: "Help",
    icon: ChatBubbleOvalLeftEllipsisIcon,
    id: "help",
  },
]


export function AppSidebar({ contents, currentView, onViewChange, onContentSelect, user, onSignOut }: AppSidebarProps) {
  const viewedItems = useViewedItems()
  const { state } = useSidebar()
  const isCollapsed = state === "collapsed"

  // Count ready transcripts that haven't been viewed
  const readyCount = contents.filter(c => 
    c.status === 'completed' && 
    (!c.content || c.content.length === 0) &&
    !viewedItems.has(c.id)
  ).length
  return (
    <Sidebar collapsible="icon" className="bg-warm-white">
      <SidebarHeader className="">
        <div className={`flex items-center ${isCollapsed ? 'justify-center px-2' : 'px-6'} py-4`}>
          <div className="flex items-center gap-2">
            <div className="w-6 h-6 bg-primary rounded-md flex items-center justify-center flex-shrink-0">
              <span className="text-white font-black text-xs">C</span>
            </div>
            {!isCollapsed && (
              <span className="font-black text-lg text-warm-gray-900">CHURCHABLE</span>
            )}
          </div>
        </div>
      </SidebarHeader>

      <SidebarContent className={`${isCollapsed ? 'px-2' : 'px-4'} pt-2 pb-4`}>
        {/* Main Content Creation Section */}
        {!isCollapsed && (
          <div className="py-2 mb-2">
            <h4 className="text-xs font-black text-warm-gray-600 uppercase tracking-wider">CONTENT</h4>
          </div>
        )}
        <NavigationSection
          items={mainNavigation}
          currentView={currentView}
          onViewChange={onViewChange}
          readyCount={readyCount}
          readyItemId="library"
          isCollapsed={isCollapsed}
        />

        {/* Visual Divider */}
        {!isCollapsed && (
          <SidebarSeparator className="my-6 bg-warm-gray-200" />
        )}

        {/* Coming Soon Section */}
        {!isCollapsed && (
          <div className="py-2 mb-2">
            <h4 className="text-xs font-black text-warm-gray-600 uppercase tracking-wider">COMING SOON</h4>
          </div>
        )}
        <NavigationSection
          items={comingSoonNavigation}
          currentView={currentView}
          onViewChange={onViewChange}
          isCollapsed={isCollapsed}
        />

      </SidebarContent>

      {/* Divider above footer */}
      {!isCollapsed && (
        <SidebarSeparator className="bg-warm-gray-200" />
      )}

      <SidebarFooter className={`${isCollapsed ? 'p-2' : 'p-4'} space-y-2`}>
        <NavigationSection
          items={bottomNavigation}
          currentView={currentView}
          onViewChange={onViewChange}
          isCollapsed={isCollapsed}
        />

        <UserDropdown user={user} onSignOut={onSignOut} isCollapsed={isCollapsed} />
      </SidebarFooter>

      <SidebarRail />
    </Sidebar>
  )
}
