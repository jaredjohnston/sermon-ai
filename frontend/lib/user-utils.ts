/**
 * Generates consistent avatar fallback text from user email
 */
export function getAvatarFallback(email?: string | null, length: number = 2): string {
  if (!email) return 'U'
  
  const cleanEmail = email.trim().toUpperCase()
  if (cleanEmail.length === 0) return 'U'
  
  return cleanEmail.substring(0, Math.max(1, length))
}

/**
 * UI styling constants for consistency
 */
export const SIDEBAR_STYLES = {
  MENU_BUTTON: "text-sm h-9 px-3 rounded-xl transition-all duration-200 hover:bg-stone-200",
  ACTIVE_ICON: "text-brand-blue",
  INACTIVE_ICON: "text-gray-500"
} as const