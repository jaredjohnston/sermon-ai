import type { Metadata } from 'next'
import { Inter } from 'next/font/google'
import { AuthHeader } from './auth-header'

const inter = Inter({ 
  subsets: ['latin'],
  display: 'swap'
})

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
    <div 
      className={`${inter.className} min-h-screen flex items-center justify-center px-4 py-8 sm:px-6 lg:px-8 bg-cover bg-center bg-no-repeat`}
      style={{ backgroundImage: 'url("/church-on-the-prairie.jpg")' }}
    >
      <div className="max-w-md w-full">
        {children}
      </div>
    </div>
  )
}