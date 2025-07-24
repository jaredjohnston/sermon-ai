import { type NextRequest } from 'next/server'
import { createClient } from '@/lib/supabase/middleware'

export async function middleware(request: NextRequest) {
  const { supabase, response } = createClient(request)

  // SECURITY: Always use getUser() instead of getSession() 
  // getSession() can be spoofed, getUser() validates with Auth server
  const { data: { user } } = await supabase.auth.getUser()

  const url = request.nextUrl.clone()
  const pathname = url.pathname

  // Public routes that don't require authentication
  const publicRoutes = ['/login', '/signup', '/auth']
  const isPublicRoute = publicRoutes.some(route => pathname.startsWith(route))

  // Root path handling
  if (pathname === '/') {
    if (user?.email_confirmed_at) {
      // Authenticated user - redirect to dashboard
      url.pathname = '/dashboard'
      return Response.redirect(url)
    } else {
      // Unauthenticated user - redirect to login
      url.pathname = '/login'
      return Response.redirect(url)
    }
  }

  // Protected routes (dashboard and other app routes)
  const isProtectedRoute = pathname.startsWith('/dashboard') || (!isPublicRoute && pathname !== '/auth/confirm')

  if (isProtectedRoute) {
    if (!user?.email_confirmed_at) {
      // User is not authenticated or email not confirmed - redirect to login
      url.pathname = '/login'
      return Response.redirect(url)
    }
  }

  // If user is authenticated and tries to access auth pages, redirect to dashboard
  if (isPublicRoute && user?.email_confirmed_at && pathname !== '/auth/confirm') {
    url.pathname = '/dashboard'
    return Response.redirect(url)
  }

  return response
}

export const config = {
  matcher: [
    /*
     * Match all request paths except for the ones starting with:
     * - _next/static (static files)
     * - _next/image (image optimization files)
     * - favicon.ico (favicon file)
     * - public folder
     */
    '/((?!_next/static|_next/image|favicon.ico|.*\\.(?:svg|png|jpg|jpeg|gif|webp)$).*)',
  ],
}