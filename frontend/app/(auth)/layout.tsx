import type { Metadata } from 'next'
import { Roboto } from 'next/font/google'
import { AuthHeader } from './auth-header'

const roboto = Roboto({ 
  weight: ['300', '400', '500', '700'],
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
      className={`${roboto.className} min-h-screen flex items-center justify-center px-4 py-8 sm:px-6 lg:px-8 bg-cover bg-center bg-no-repeat`}
      style={{ backgroundImage: 'url("/church-on-the-prairie.jpg")' }}
    >
      <div className="max-w-md w-full">
        {children}
      </div>
    </div>
  )
}