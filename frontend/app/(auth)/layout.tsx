import type { Metadata } from 'next'

export const metadata: Metadata = {
  title: 'Authentication - Sermon AI',
  description: 'Sign in or create your account to access Sermon AI',
}

export default function AuthLayout({
  children,
}: {
  children: React.ReactNode
}) {
  return (
    <div className="min-h-screen flex items-center justify-center bg-warm-white px-4 sm:px-6 lg:px-8">
      <div className="max-w-md w-full space-y-8">
        <div className="text-center">
          <h1 className="text-3xl font-bold text-warm-gray-900">Sermon AI</h1>
          <p className="mt-2 text-warm-gray-600">Transform your sermons with AI</p>
        </div>
        {children}
      </div>
    </div>
  )
}