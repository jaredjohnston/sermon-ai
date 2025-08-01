"use client"

import { Card, CardContent } from "@/components/ui/card"
import { Button } from "@/components/ui/button"
import { Upload, Sparkles, BookOpen, Zap, Video, Edit3 } from "lucide-react"
import { UploadZone } from "./upload-zone"
import Image from "next/image"
import type { ContentSource, TranscriptionResponse } from "@/types/api"

interface DashboardContentProps {
  contents: ContentSource[]
  onViewChange: (view: string) => void
  onUploadStart: () => void
  onUploadSuccess: (data: TranscriptionResponse) => void
  onUploadError: (error: string) => void
  onTranscriptEdit: (content: ContentSource) => void
  onContentEdit: (content: ContentSource) => void
  transcriptionComplete?: boolean
  onTranscriptionAcknowledged?: () => void
}


export function DashboardContent({
  contents,
  onViewChange,
  onUploadStart,
  onUploadSuccess,
  onUploadError,
  onTranscriptEdit,
  onContentEdit,
  transcriptionComplete,
  onTranscriptionAcknowledged,
}: DashboardContentProps) {
  return (
    <div className="space-y-12">
      {/* Header */}
      <div className="mb-8">
        <h2 className="text-3xl font-black text-warm-gray-900">UPLOAD NEW SERMON</h2>
      </div>

      {/* Two-column layout: Upload left, How it Works right */}
      <div className="flex gap-6">
        {/* Left Column - Upload Section (takes most of the width) */}
        <div className="flex-1">
          <UploadZone 
            onUploadStart={onUploadStart} 
            onUploadSuccess={onUploadSuccess} 
            onUploadError={onUploadError}
            transcriptionComplete={transcriptionComplete}
            onTranscriptionAcknowledged={onTranscriptionAcknowledged}
          />
        </div>

        {/* Right Column - How It Works Card (compact width) */}
        <div className="w-80 hidden lg:block">
          <Card className="border-0 rounded-xl shadow-lg hover:shadow-xl transition-shadow transform transition-all duration-200 hover:-translate-y-0.5">
            <CardContent className="p-6">
              <h3 className="text-lg font-bold text-warm-gray-900 mb-4">HOW IT WORKS</h3>
              
              <div className="space-y-4">
                {/* Step 1 */}
                <div className="flex items-start space-x-3">
                  <div className="w-6 h-6 bg-primary text-white rounded-xl flex items-center justify-center font-bold text-xs flex-shrink-0">
                    1
                  </div>
                  <div>
                    <h4 className="font-semibold text-sm text-warm-gray-900 mb-1">UPLOAD</h4>
                    <p className="text-warm-gray-600 text-xs leading-relaxed">Upload your sermon files in any format</p>
                  </div>
                </div>

                {/* Step 2 */}
                <div className="flex items-start space-x-3">
                  <div className="w-6 h-6 bg-primary text-white rounded-xl flex items-center justify-center font-bold text-xs flex-shrink-0">
                    2
                  </div>
                  <div>
                    <h4 className="font-semibold text-sm text-warm-gray-900 mb-1">GENERATE</h4>
                    <p className="text-warm-gray-600 text-xs leading-relaxed">AI creates content from your transcript</p>
                  </div>
                </div>

                {/* Step 3 */}
                <div className="flex items-start space-x-3">
                  <div className="w-6 h-6 bg-primary text-white rounded-xl flex items-center justify-center font-bold text-xs flex-shrink-0">
                    3
                  </div>
                  <div>
                    <h4 className="font-semibold text-sm text-warm-gray-900 mb-1">REVIEW</h4>
                    <p className="text-warm-gray-600 text-xs leading-relaxed">Edit and finalize before sharing</p>
                  </div>
                </div>
              </div>
            </CardContent>
          </Card>
        </div>
      </div>

      {/* Recent Sermons */}
      {contents.length > 0 && (
        <div className="space-y-6">
          <div className="flex items-center">
            <h2 className="text-3xl font-black text-warm-gray-900">RECENTLY CREATED</h2>
            <div className="ml-4 h-1 flex-1 bg-warm-gray-200"></div>
            <Button className="ml-4 px-4 rounded-xl" onClick={() => onViewChange("library")}>
              VIEW ALL
            </Button>
          </div>
          <div className="space-y-4">
            {contents.slice(0, 3).map((content) => (
              <Card key={content.id} className="border-0 rounded-2xl shadow-lg hover:shadow-xl transition-shadow transform transition-all duration-200 hover:-translate-y-0.5">
                <CardContent className="p-6">
                  <div className="flex flex-col md:flex-row md:items-center justify-between gap-4">
                    <div className="flex items-center">
                      <div>
                        <p className="font-bold text-lg text-warm-gray-900">{content.filename}</p>
                        <p className="text-warm-gray-600 font-medium">
                          {new Date(content.uploadedAt).toLocaleDateString()}
                        </p>
                      </div>
                    </div>
                    <div className="flex items-center gap-3">
                      {content.content ? (
                        <Button variant="outline" className="px-4 rounded-xl" size="sm" onClick={() => onContentEdit(content)}>
                          <Edit3 className="h-4 w-4 mr-2" />
                          Review Content
                        </Button>
                      ) : (
                        <Button className="px-4 rounded-xl" size="sm" onClick={() => onTranscriptEdit(content)}>
                          <Sparkles className="h-4 w-4 mr-2" />
                          Generate Content
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
            className="border-0 rounded-2xl shadow-lg hover:shadow-lg transition-shadow cursor-pointer transform transition-all duration-300 hover:shadow-lg hover:-translate-y-1 overflow-hidden"
            onClick={() => onViewChange("library")}
          >
            <CardContent className="p-0">
              <div className="flex flex-col h-full">
                <div className="p-6 pb-8">
                  <BookOpen className="h-10 w-10 text-primary mb-4" />
                  <h3 className="font-black text-2xl mb-3 text-warm-gray-900">CREATE CONTENT</h3>
                  <p className="text-warm-gray-600 font-medium mb-6">Browse and generate content from your sermons</p>
                  <Button
                    className="px-8 rounded-xl hover:brightness-110 hover:scale-[1.02] transition-all duration-200"
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
            className="border-0 rounded-2xl shadow-lg hover:shadow-lg transition-shadow cursor-pointer transform transition-all duration-300 hover:shadow-lg hover:-translate-y-1 overflow-hidden"
            onClick={() => onViewChange("assistant")}
          >
            <CardContent className="p-0">
              <div className="flex flex-col h-full">
                <div className="p-6 pb-8">
                  <Zap className="h-10 w-10 text-primary mb-4" />
                  <h3 className="font-black text-2xl mb-3 text-warm-gray-900">AI RESEARCH</h3>
                  <p className="text-warm-gray-600 font-medium mb-6">Ask AI to research a topic and help prepare your sermon</p>
                  <Button
                    className="px-8 rounded-xl hover:brightness-110 hover:scale-[1.02] transition-all duration-200"
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
            className="border-0 rounded-2xl shadow-lg hover:shadow-lg transition-shadow cursor-pointer transform transition-all duration-300 hover:shadow-lg hover:-translate-y-1 sm:col-span-2 lg:col-span-1 overflow-hidden"
            onClick={() => onViewChange("video-clips")}
          >
            <CardContent className="p-0">
              <div className="flex flex-col h-full">
                <div className="p-6 pb-8">
                  <Video className="h-10 w-10 text-primary mb-4" />
                  <h3 className="font-black text-2xl mb-3 text-warm-gray-900">CREATE SOCIAL CLIPS</h3>
                  <p className="text-warm-gray-600 font-medium mb-6">Create engaging social media clips from your sermons</p>
                  <Button
                    className="px-8 rounded-xl hover:brightness-110 hover:scale-[1.02] transition-all duration-200"
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
