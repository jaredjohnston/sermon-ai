import type { Metadata } from 'next'
import { AuthHeader } from './auth-header'

export const metadata: Metadata = {
  title: 'Authentication - Churchable',
  description: 'Sign in or create your account to access Churchable',
}

export default function AuthLayout({
  children,
}: {
  children: React.ReactNode
}) {
  return (
    <div className="min-h-screen flex items-center justify-center bg-warm-white px-4 py-8 sm:px-6 lg:px-8">
      <div className="max-w-md w-full space-y-8">
        <AuthHeader />
        {children}
      </div>
    </div>
  )
}