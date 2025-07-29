import { TestApiClient } from '@/components/test-api-client'
import { createClient } from '@/lib/supabase/server'
import { redirect } from 'next/navigation'

export default async function TestPage() {
  const supabase = await createClient()
  const { data: { user } } = await supabase.auth.getUser()

  if (!user) {
    redirect('/login')
  }

  return (
    <div className="container mx-auto py-8">
      <h1 className="text-3xl font-bold mb-8">Test Page</h1>
      <div className="mb-8 p-4 bg-muted rounded-lg">
        <p className="text-sm text-muted-foreground">Logged in as:</p>
        <p className="font-mono">{user.email}</p>
        <p className="text-xs text-muted-foreground mt-2">
          To restrict access to this page, add your email to the allowedTestEmails array in middleware.ts
        </p>
      </div>
      
      <TestApiClient />
    </div>
  )
}