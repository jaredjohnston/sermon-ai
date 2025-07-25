'use client'

import { useState } from 'react'
import { useAuth } from '@/components/providers/AuthProvider'
import { Button } from '@/components/ui/button'
import { Input } from '@/components/ui/input'
import { Label } from '@/components/ui/label'
import { Card, CardContent, CardDescription, CardFooter, CardHeader, CardTitle } from '@/components/ui/card'
import { Alert, AlertDescription } from '@/components/ui/alert'
import Link from 'next/link'
import Image from 'next/image'
import { Loader2 } from 'lucide-react'

export default function LoginPage() {
  const [email, setEmail] = useState('')
  const [password, setPassword] = useState('')
  const [error, setError] = useState('')
  const [isLoading, setIsLoading] = useState(false)
  const { signIn } = useAuth()

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault()
    setError('')
    setIsLoading(true)

    const result = await signIn(email, password)
    
    if (result.error) {
      setError(result.error)
    }
    
    setIsLoading(false)
  }

  return (
    <Card className="w-full bg-white/20 backdrop-blur-md shadow-2xl border-white/30 rounded-2xl">
      <CardHeader className="text-center space-y-4 pb-8">
        <div className="flex justify-center">
          <Image 
            src="/churchable.png" 
            alt="Churchable Logo" 
            width={120} 
            height={120}
            className="object-contain"
          />
        </div>
        <div className="space-y-1">
          <h1 className="text-4xl font-bold text-white">Churchable</h1>
          <p className="text-white/90">Welcome, please sign in below.</p>
        </div>
      </CardHeader>
      
      <form onSubmit={handleSubmit}>
        <CardContent className="space-y-4">
          {error && (
            <Alert variant="destructive">
              <AlertDescription>{error}</AlertDescription>
            </Alert>
          )}
          
          <div className="space-y-2">
            <Label htmlFor="email" className="text-white">Email</Label>
            <Input
              id="email"
              type="email"
              value={email}
              onChange={(e) => setEmail(e.target.value)}
              required
              disabled={isLoading}
            />
          </div>
          
          <div className="space-y-2">
            <Label htmlFor="password" className="text-white">Password</Label>
            <Input
              id="password"
              type="password"
              value={password}
              onChange={(e) => setPassword(e.target.value)}
              required
              disabled={isLoading}
            />
          </div>
        </CardContent>
        
        <CardFooter className="flex flex-col">
          <Button type="submit" className="mx-auto px-8 rounded-full hover:scale-[1.02] hover:brightness-110 transition-all duration-200" disabled={isLoading}>
            {isLoading && <Loader2 className="mr-2 h-4 w-4 animate-spin" />}
            Sign In
          </Button>
          
          <div className="w-full border-t border-white/20 mt-8 mb-4"></div>
          
          <p className="text-sm text-center text-white/80">
            Don't have an account?{' '}
            <Link href="/signup" className="font-medium text-white underline hover:text-white/90">
              Sign up
            </Link>
          </p>
        </CardFooter>
      </form>
    </Card>
  )
}