"use client"

import { Card, CardContent } from "@/components/ui/card"
import { Button } from "@/components/ui/button"
import { Bot, Users, BookOpen, Wand2, Download } from "lucide-react"

export function AIAssistant() {
  return (
    <div className="space-y-8">
      {/* Header */}
      <div>
        <h1 className="text-3xl font-black text-warm-gray-900">AI RESEARCH</h1>
        <p className="text-warm-gray-600 font-medium">Get intelligent help with your sermon content and preparation</p>
      </div>

      {/* Coming Soon Card */}
      <Card className="bg-gradient-to-br from-blue-50 to-indigo-50 border-none">
        <CardContent className="p-8 text-center">
          <div className="rounded-full bg-blue-100 p-4 w-16 h-16 mx-auto mb-4">
            <Bot className="h-8 w-8" style={{ color: "#0000ee" }} />
          </div>
          <h2 className="text-2xl font-black mb-2 text-warm-gray-900">AI RESEARCH COMING SOON</h2>
          <p className="text-warm-gray-600 font-medium max-w-lg mx-auto mb-6">
            Your AI thought-partner for sermon preparation. Get outlines, openers, and biblical references while
            maintaining your unique voice and style.
          </p>
          <Button disabled>
            <Bot className="h-4 w-4 mr-2" />
            Coming Soon
          </Button>
        </CardContent>
      </Card>

      {/* Planned Features */}
      <div>
        <h2 className="text-xl font-black mb-4 text-warm-gray-900">PLANNED FEATURES</h2>
        <div className="grid gap-4 md:grid-cols-2">
          <Card>
            <CardContent className="p-6 flex items-start gap-4">
              <div className="p-3 rounded-lg bg-blue-50">
                <Users className="h-6 w-6" style={{ color: "#0000ee" }} />
              </div>
              <div>
                <h3 className="font-black text-warm-gray-900 mb-2 uppercase">A Writing Partner</h3>
                <p className="text-warm-gray-600 font-medium">
                  Researches topics, creates outlines, and suggests scripture all on the side so you can stay in the
                  flow.
                </p>
              </div>
            </CardContent>
          </Card>

          <Card>
            <CardContent className="p-6 flex items-start gap-4">
              <div className="p-3 rounded-lg bg-blue-50">
                <BookOpen className="h-6 w-6" style={{ color: "#0000ee" }} />
              </div>
              <div>
                <h3 className="font-black text-warm-gray-900 mb-2 uppercase">Biblical References</h3>
                <p className="text-warm-gray-600 font-medium">
                  Get sermon biblical references and insights from published theological and academic sources.
                </p>
              </div>
            </CardContent>
          </Card>

          <Card>
            <CardContent className="p-6 flex items-start gap-4">
              <div className="p-3 rounded-lg bg-blue-50">
                <Wand2 className="h-6 w-6" style={{ color: "#0000ee" }} />
              </div>
              <div>
                <h3 className="font-black text-warm-gray-900 mb-2 uppercase">Add Polish & Fancy Stuff</h3>
                <p className="text-warm-gray-600 font-medium">
                  Get help creating hooks, metaphors, memorable story-arcs, and powerful openers.
                </p>
              </div>
            </CardContent>
          </Card>

          <Card>
            <CardContent className="p-6 flex items-start gap-4">
              <div className="p-3 rounded-lg bg-blue-50">
                <Download className="h-6 w-6" style={{ color: "#0000ee" }} />
              </div>
              <div>
                <h3 className="font-black text-warm-gray-900 mb-2 uppercase">Export</h3>
                <p className="text-warm-gray-600 font-medium">
                  Tell it to export your sermon using a preferred format or structure for Sunday's service.
                </p>
              </div>
            </CardContent>
          </Card>
        </div>
      </div>
    </div>
  )
}
