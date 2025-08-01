import { Button } from "@/components/ui/button"
import { 
  DropdownMenu, 
  DropdownMenuContent, 
  DropdownMenuItem, 
  DropdownMenuTrigger 
} from "@/components/ui/dropdown-menu"
import { Avatar, AvatarFallback } from "@/components/ui/avatar"
import { Settings, User, LogOut, UserPlus, CreditCard, TrendingUp, MessageSquare } from "lucide-react"
import { getAvatarFallback } from "@/lib/user-utils"

interface UserDropdownProps {
  user?: { email?: string } | null
  onSignOut: () => void
}

export function UserDropdown({ user, onSignOut }: UserDropdownProps) {
  return (
    <DropdownMenu>
      <DropdownMenuTrigger asChild>
        <Button variant="ghost" className="w-full justify-start h-9 px-3 rounded-xl hover:bg-stone-200">
          <Avatar className="h-6 w-6 mr-3">
            <AvatarFallback className="text-xs">
              {getAvatarFallback(user?.email, 2)}
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
              {getAvatarFallback(user?.email, 1)}
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
  )
}