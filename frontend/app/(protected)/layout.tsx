import { createClient } from '@/lib/supabase/server'
import { redirect } from 'next/navigation'

export default async function ProtectedLayout({
  children,
}: {
  children: React.ReactNode
}) {
  const supabase = await createClient()
  
  // SECURITY: Always use getUser() to validate authentication
  // getSession() can be spoofed, getUser() validates with Auth server
  const { data: { user } } = await supabase.auth.getUser()

  if (!user?.email_confirmed_at) {
    redirect('/login')
  }

  return <>{children}</>
}