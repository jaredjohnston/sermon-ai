import { Card, CardContent, CardDescription, CardFooter, CardHeader, CardTitle } from '@/components/ui/card'
import { Button } from '@/components/ui/button'
import { Alert, AlertDescription } from '@/components/ui/alert'
import { AlertTriangle } from 'lucide-react'
import Link from 'next/link'

export default function AuthCodeErrorPage() {
  return (
    <div className="min-h-screen flex items-center justify-center bg-warm-white px-4 sm:px-6 lg:px-8">
      <Card className="w-full max-w-md">
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <AlertTriangle className="h-5 w-5 text-red-500" />
            Confirmation Failed
          </CardTitle>
          <CardDescription>
            There was an error confirming your email address
          </CardDescription>
        </CardHeader>
        
        <CardContent>
          <Alert variant="destructive">
            <AlertDescription>
              The confirmation link is invalid or has expired. Please try signing up again or contact support if the problem persists.
            </AlertDescription>
          </Alert>
        </CardContent>
        
        <CardFooter className="flex flex-col space-y-2">
          <Button asChild className="w-full">
            <Link href="/signup">Try Again</Link>
          </Button>
          <Button variant="outline" asChild className="w-full">
            <Link href="/login">Back to Login</Link>
          </Button>
        </CardFooter>
      </Card>
    </div>
  )
}