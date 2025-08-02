import {
  SidebarMenu,
  SidebarMenuButton,
  SidebarMenuItem,
} from "@/components/ui/sidebar"
import { SIDEBAR_STYLES } from "@/lib/user-utils"
import type { NavigationSectionProps } from "@/types/navigation"

export function NavigationSection({ 
  items, 
  currentView, 
  onViewChange, 
  readyCount, 
  readyItemId,
  isCollapsed 
}: NavigationSectionProps & { isCollapsed?: boolean }) {
  return (
    <SidebarMenu className="space-y-1">
      {items.map((item) => {
        const Icon = item.icon
        const isActive = currentView === item.id
        const showBadge = item.id === readyItemId && typeof readyCount === 'number' && readyCount > 0

        return (
          <SidebarMenuItem key={item.id}>
            <SidebarMenuButton
              isActive={isActive}
              onClick={() => onViewChange(item.id)}
              tooltip={isCollapsed ? item.title : item.description}
              className={`${SIDEBAR_STYLES.MENU_BUTTON} ${isCollapsed ? 'justify-center px-2' : ''}`}
            >
              <Icon className={`h-5 w-5 ${isActive ? SIDEBAR_STYLES.ACTIVE_ICON : SIDEBAR_STYLES.INACTIVE_ICON} flex-shrink-0`} />
              {!isCollapsed && (
                <>
                  <span className="flex-1 text-left">{item.title}</span>
                  {showBadge && (
                    <span className="ml-auto bg-primary text-white text-xs font-bold rounded-full px-2 py-0.5 min-w-[1.5rem] text-center">
                      {readyCount}
                    </span>
                  )}
                </>
              )}
            </SidebarMenuButton>
          </SidebarMenuItem>
        )
      })}
    </SidebarMenu>
  )
}