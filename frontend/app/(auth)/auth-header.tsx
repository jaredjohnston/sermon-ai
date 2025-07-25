'use client'

import { usePathname } from 'next/navigation'

export function AuthHeader() {
  const pathname = usePathname()
  const isLoginPage = pathname === '/login'
  
  return (
    <div className="text-center">
      <h1 className="text-5xl font-bold text-white">Churchable</h1>
      <p className="mt-2 text-white">
        {isLoginPage ? 'Welcome, please sign in below.' : 'Create your free account. No credit card required.'}
      </p>
    </div>
  )
}