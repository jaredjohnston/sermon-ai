"use client"

import { Card, CardContent } from "@/components/ui/card"
import { Button } from "@/components/ui/button"
import { Video } from "lucide-react"

export function VideoClips() {
  return (
    <div className="space-y-8">
      {/* Header */}
      <div>
        <h1 className="text-3xl font-black text-warm-gray-900">CREATE SOCIAL CLIPS</h1>
        <p className="text-warm-gray-600 font-medium">Create engaging social media clips from your sermons</p>
      </div>

      {/* Coming Soon Card */}
      <Card className="bg-gradient-to-br from-blue-50 to-indigo-50 border-none">
        <CardContent className="p-8 text-center">
          <div className="rounded-full bg-blue-100 p-4 w-16 h-16 mx-auto mb-4">
            <Video className="h-8 w-8" style={{ color: "#0000ee" }} />
          </div>
          <h2 className="text-2xl font-black mb-2 text-warm-gray-900">SOCIAL CLIPS COMING SOON</h2>
          <p className="text-warm-gray-600 font-medium max-w-lg mx-auto mb-6">
            We're working on tools to help you create engaging social media clips from your sermons.
          </p>
          <Button disabled>
            <Video className="h-4 w-4 mr-2" />
            Coming Soon
          </Button>
        </CardContent>
      </Card>
    </div>
  )
}
