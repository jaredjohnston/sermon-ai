"use client"

import { Card, CardContent } from "@/components/ui/card"
import { Button } from "@/components/ui/button"
import { Upload, Sparkles, BookOpen, Zap, Video, Edit3 } from "lucide-react"
import { UploadZone } from "./upload-zone"
import Image from "next/image"
import type { ContentSource, TranscriptionResponse } from "@/types/api"

interface DashboardContentProps {
  sermons: ContentSource[]
  onViewChange: (view: string) => void
  onUploadStart: () => void
  onUploadSuccess: (data: TranscriptionResponse) => void
  onUploadError: (error: string) => void
  onTranscriptEdit: (sermon: ContentSource) => void
  onContentEdit: (sermon: ContentSource) => void
}


export function DashboardContent({
  sermons,
  onViewChange,
  onUploadStart,
  onUploadSuccess,
  onUploadError,
  onTranscriptEdit,
  onContentEdit,
}: DashboardContentProps) {
  return (
    <div className="space-y-12">
      {/* Upload Section */}
      <div className="space-y-6">
        <h2 className="text-3xl font-black text-warm-gray-900">UPLOAD NEW SERMON</h2>
        <UploadZone onUploadStart={onUploadStart} onUploadSuccess={onUploadSuccess} onUploadError={onUploadError} />
      </div>

      {/* How It Works */}
      <div className="space-y-8">
        <div className="flex items-center">
          <h2 className="text-3xl font-black text-warm-gray-900">HOW IT WORKS</h2>
          <div className="ml-4 h-1 flex-1 bg-warm-gray-200"></div>
        </div>
        
        <div className="grid gap-8 md:grid-cols-3">
          {/* Step 1 */}
          <div className="flex flex-col items-start space-y-4">
            <div className="w-14 h-14 bg-primary text-white rounded-full flex items-center justify-center font-black text-xl">
              1
            </div>
            <div>
              <h3 className="font-black text-xl text-warm-gray-900 mb-3">UPLOAD</h3>
              <p className="text-warm-gray-600 font-medium">Build your templates then upload your sermon. We support all major file formats.</p>
            </div>
          </div>

          {/* Step 2 */}
          <div className="flex flex-col items-start space-y-4">
            <div className="w-14 h-14 bg-primary text-white rounded-full flex items-center justify-center font-black text-xl">
              2
            </div>
            <div>
              <h3 className="font-black text-xl text-warm-gray-900 mb-3">GENERATE</h3>
              <p className="text-warm-gray-600 font-medium">Provide additional custom instructions before generating your content.</p>
            </div>
          </div>

          {/* Step 3 */}
          <div className="flex flex-col items-start space-y-4">
            <div className="w-14 h-14 bg-primary text-white rounded-full flex items-center justify-center font-black text-xl">
              3
            </div>
            <div>
              <h3 className="font-black text-xl text-warm-gray-900 mb-3">REVIEW</h3>
              <p className="text-warm-gray-600 font-medium">Make any edits or finishing touches before sharing with your church.</p>
            </div>
          </div>
        </div>
      </div>

      {/* Recent Sermons */}
      {sermons.length > 0 && (
        <div className="space-y-6">
          <div className="flex items-center">
            <h2 className="text-3xl font-black text-warm-gray-900">RECENTLY CREATED</h2>
            <div className="ml-4 h-1 flex-1 bg-warm-gray-200"></div>
            <Button className="ml-4 px-4 rounded-full" onClick={() => onViewChange("library")}>
              VIEW ALL
            </Button>
          </div>
          <div className="space-y-4">
            {sermons.slice(0, 3).map((sermon) => (
              <Card key={sermon.id} className="border border-gray-200 rounded-2xl shadow-lg hover:shadow-xl transition-shadow">
                <CardContent className="p-6">
                  <div className="flex flex-col md:flex-row md:items-center justify-between gap-4">
                    <div className="flex items-center">
                      <div>
                        <p className="font-bold text-lg text-warm-gray-900">{sermon.filename}</p>
                        <p className="text-warm-gray-600 font-medium">
                          {new Date(sermon.uploadedAt).toLocaleDateString()}
                        </p>
                      </div>
                    </div>
                    <div className="flex items-center gap-3">
                      <Button variant="outline" size="sm" onClick={() => onViewChange("transcript-editor")}>
                        <Edit3 className="h-4 w-4 mr-2" />
                        Edit Transcript
                      </Button>

                      {sermon.content ? (
                        <Button className="px-4 rounded-full" size="sm" onClick={() => onContentEdit(sermon)}>
                          <Sparkles className="h-4 w-4 mr-2" />
                          Review Content
                        </Button>
                      ) : (
                        <Button variant="outline" size="sm" disabled>
                          <Sparkles className="h-4 w-4 mr-2" />
                          No Content Yet
                        </Button>
                      )}
                    </div>
                  </div>
                </CardContent>
              </Card>
            ))}
          </div>
        </div>
      )}

      {/* Quick Actions - Redesigned */}
      <div className="space-y-8">
        <div className="flex items-center">
          <h2 className="text-3xl font-black text-warm-gray-900">QUICK ACTIONS</h2>
          <div className="ml-4 h-1 flex-1 bg-warm-gray-200"></div>
        </div>

        <div className="grid gap-8 sm:grid-cols-2 lg:grid-cols-3">
          {/* Recently Created Card */}
          <Card
            className="border border-gray-200 rounded-2xl shadow-lg hover:shadow-xl transition-shadow cursor-pointer transform transition-all duration-300 hover:shadow-xl hover:-translate-y-1 overflow-hidden"
            onClick={() => onViewChange("library")}
          >
            <CardContent className="p-0">
              <div className="flex flex-col h-full">
                <div className="p-6 pb-8">
                  <BookOpen className="h-10 w-10 text-primary mb-4" />
                  <h3 className="font-black text-2xl mb-3 text-warm-gray-900">CREATE CONTENT</h3>
                  <p className="text-warm-gray-600 font-medium mb-6">Browse and generate content from your sermons</p>
                  <Button
                    className="px-8 rounded-full hover:brightness-110 hover:scale-[1.02] transition-all duration-200"
                    onClick={(e) => {
                      e.stopPropagation()
                      onViewChange("library")
                    }}
                  >
                    VIEW CONTENT
                  </Button>
                </div>
              </div>
            </CardContent>
          </Card>

          {/* AI Assistant Card */}
          <Card
            className="border border-gray-200 rounded-2xl shadow-lg hover:shadow-xl transition-shadow cursor-pointer transform transition-all duration-300 hover:shadow-xl hover:-translate-y-1 overflow-hidden"
            onClick={() => onViewChange("assistant")}
          >
            <CardContent className="p-0">
              <div className="flex flex-col h-full">
                <div className="p-6 pb-8">
                  <Zap className="h-10 w-10 text-primary mb-4" />
                  <h3 className="font-black text-2xl mb-3 text-warm-gray-900">AI RESEARCH</h3>
                  <p className="text-warm-gray-600 font-medium mb-6">Ask AI to research a topic and help prepare your sermon</p>
                  <Button
                    className="px-8 rounded-full hover:brightness-110 hover:scale-[1.02] transition-all duration-200"
                    onClick={(e) => {
                      e.stopPropagation()
                      onViewChange("assistant")
                    }}
                  >
                    OPEN ASSISTANT
                  </Button>
                </div>
              </div>
            </CardContent>
          </Card>

          {/* Create Social Clips Card */}
          <Card
            className="border border-gray-200 rounded-2xl shadow-lg hover:shadow-xl transition-shadow cursor-pointer transform transition-all duration-300 hover:shadow-xl hover:-translate-y-1 sm:col-span-2 lg:col-span-1 overflow-hidden"
            onClick={() => onViewChange("video-clips")}
          >
            <CardContent className="p-0">
              <div className="flex flex-col h-full">
                <div className="p-6 pb-8">
                  <Video className="h-10 w-10 text-primary mb-4" />
                  <h3 className="font-black text-2xl mb-3 text-warm-gray-900">CREATE SOCIAL CLIPS</h3>
                  <p className="text-warm-gray-600 font-medium mb-6">Create engaging social media clips from your sermons</p>
                  <Button
                    className="px-8 rounded-full hover:brightness-110 hover:scale-[1.02] transition-all duration-200"
                    onClick={(e) => {
                      e.stopPropagation()
                      onViewChange("video-clips")
                    }}
                  >
                    CREATE CLIPS
                  </Button>
                </div>
              </div>
            </CardContent>
          </Card>
        </div>
      </div>
    </div>
  )
}
