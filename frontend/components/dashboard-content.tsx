"use client"

import { Card, CardContent } from "@/components/ui/card"
import { Button } from "@/components/ui/button"
import { Upload, Sparkles, BookOpen, Zap, Video, Edit3 } from "lucide-react"
import { UploadZone } from "./upload-zone"
import type { SermonData, TranscriptionResponse } from "@/types/api"

interface DashboardContentProps {
  sermons: SermonData[]
  onViewChange: (view: string) => void
  onUploadStart: () => void
  onUploadSuccess: (data: TranscriptionResponse) => void
  onUploadError: (error: string) => void
  onTranscriptEdit: (sermon: SermonData) => void
  onContentEdit: (sermon: SermonData) => void
}

// Modern Church Logo - Simple Cross with Rays
function ModernChurchLogo() {
  return (
    <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="currentColor" className="h-8 w-8">
      {/* Central Cross */}
      <rect x="11" y="6" width="2" height="12" rx="1" />
      <rect x="7" y="10" width="10" height="2" rx="1" />

      {/* Radiating Light Rays */}
      <rect x="11.5" y="2" width="1" height="2" rx="0.5" opacity="0.7" />
      <rect x="11.5" y="20" width="1" height="2" rx="0.5" opacity="0.7" />
      <rect x="2" y="11.5" width="2" height="1" rx="0.5" opacity="0.7" />
      <rect x="20" y="11.5" width="2" height="1" rx="0.5" opacity="0.7" />

      {/* Diagonal rays */}
      <rect x="5.5" y="5.5" width="1.4" height="1.4" rx="0.7" opacity="0.5" transform="rotate(45 6.2 6.2)" />
      <rect x="17.1" y="5.5" width="1.4" height="1.4" rx="0.7" opacity="0.5" transform="rotate(45 17.8 6.2)" />
      <rect x="5.5" y="17.1" width="1.4" height="1.4" rx="0.7" opacity="0.5" transform="rotate(45 6.2 17.8)" />
      <rect x="17.1" y="17.1" width="1.4" height="1.4" rx="0.7" opacity="0.5" transform="rotate(45 17.8 17.8)" />
    </svg>
  )
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
      {/* Header */}
      <div className="text-center space-y-4">
        <div className="flex justify-center items-center gap-3">
          <div
            className="flex h-12 w-12 items-center justify-center text-white zorp-border"
            style={{ backgroundColor: "#0000ee" }}
          >
            <ModernChurchLogo />
          </div>
          <h1 className="text-5xl font-black zorp-text-blue">SERMON AI</h1>
        </div>
        <p className="text-lg text-warm-gray-600 max-w-2xl mx-auto font-medium">
          Create engaging content from your sermons that inspires and connects with your church throughout the week
        </p>
      </div>

      {/* Upload Section */}
      <div className="space-y-6">
        <h2 className="text-3xl font-black text-warm-gray-900">UPLOAD NEW SERMON</h2>
        <UploadZone onUploadStart={onUploadStart} onUploadSuccess={onUploadSuccess} onUploadError={onUploadError} />
      </div>

      {/* How It Works */}
      <div className="space-y-6">
        <div className="flex items-center">
          <h2 className="text-3xl font-black text-warm-gray-900">HOW IT WORKS</h2>
          <div className="ml-4 h-1 flex-1 bg-warm-gray-200"></div>
        </div>
        <div className="grid gap-8 md:grid-cols-3">
          <div className="text-center space-y-4">
            <div className="w-16 h-16 bg-warm-gray-800 text-white zorp-border flex items-center justify-center mx-auto">
              <Upload className="h-8 w-8" />
            </div>
            <h3 className="font-black text-xl text-warm-gray-900">1. UPLOAD</h3>
            <p className="text-warm-gray-600 font-medium">Upload your sermon audio or video file</p>
          </div>

          <div className="text-center space-y-4">
            <div className="w-16 h-16 bg-warm-gray-800 text-white zorp-border flex items-center justify-center mx-auto">
              <Edit3 className="h-8 w-8" />
            </div>
            <h3 className="font-black text-xl text-warm-gray-900">2. EDIT TRANSCRIPT</h3>
            <p className="text-warm-gray-600 font-medium">Review and edit the transcript before generating content</p>
          </div>

          <div className="text-center space-y-4">
            <div className="w-16 h-16 bg-warm-gray-800 text-white zorp-border flex items-center justify-center mx-auto">
              <Sparkles className="h-8 w-8" />
            </div>
            <h3 className="font-black text-xl text-warm-gray-900">3. GENERATE & SHARE</h3>
            <p className="text-warm-gray-600 font-medium">Generate AI content and share with your church</p>
          </div>
        </div>
      </div>

      {/* Recent Sermons */}
      {sermons.length > 0 && (
        <div className="space-y-6">
          <div className="flex items-center">
            <h2 className="text-3xl font-black text-warm-gray-900">RECENTLY CREATED</h2>
            <div className="ml-4 h-1 flex-1 bg-warm-gray-200"></div>
            <Button className="zorp-button ml-4" onClick={() => onViewChange("library")}>
              VIEW ALL
            </Button>
          </div>
          <div className="space-y-4">
            {sermons.slice(0, 3).map((sermon) => (
              <Card key={sermon.id} className="zorp-card zorp-hover">
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
                        <Button className="zorp-button" size="sm" onClick={() => onContentEdit(sermon)}>
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
            className="zorp-card zorp-hover cursor-pointer overflow-hidden transform transition-all duration-300 hover:shadow-xl hover:-translate-y-1"
            onClick={() => onViewChange("library")}
          >
            <div className="h-2" style={{ backgroundColor: "#0000ee" }}></div>
            <CardContent className="p-0">
              <div className="flex flex-col h-full">
                <div className="bg-warm-gray-50 p-6 flex items-center justify-center">
                  <div className="p-4 text-white zorp-border rounded-full" style={{ backgroundColor: "#0000ee" }}>
                    <BookOpen className="h-10 w-10" />
                  </div>
                </div>
                <div className="p-6 text-center">
                  <h3 className="font-black text-2xl mb-3 text-warm-gray-900">RECENTLY CREATED</h3>
                  <p className="text-warm-gray-600 font-medium">Browse and manage your recently created content</p>
                  <Button
                    className="zorp-button mt-4 w-full"
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
            className="zorp-card zorp-hover cursor-pointer overflow-hidden transform transition-all duration-300 hover:shadow-xl hover:-translate-y-1"
            onClick={() => onViewChange("assistant")}
          >
            <div className="h-2" style={{ backgroundColor: "#0000ee" }}></div>
            <CardContent className="p-0">
              <div className="flex flex-col h-full">
                <div className="bg-warm-gray-50 p-6 flex items-center justify-center">
                  <div className="p-4 text-white zorp-border rounded-full" style={{ backgroundColor: "#0000ee" }}>
                    <Zap className="h-10 w-10" />
                  </div>
                </div>
                <div className="p-6 text-center">
                  <h3 className="font-black text-2xl mb-3 text-warm-gray-900">AI ASSISTANT</h3>
                  <p className="text-warm-gray-600 font-medium">Get intelligent help with sermon content preparation</p>
                  <Button
                    className="zorp-button mt-4 w-full"
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
            className="zorp-card zorp-hover cursor-pointer overflow-hidden transform transition-all duration-300 hover:shadow-xl hover:-translate-y-1 sm:col-span-2 lg:col-span-1"
            onClick={() => onViewChange("video-clips")}
          >
            <div className="h-2" style={{ backgroundColor: "#0000ee" }}></div>
            <CardContent className="p-0">
              <div className="flex flex-col h-full">
                <div className="bg-warm-gray-50 p-6 flex items-center justify-center">
                  <div className="p-4 text-white zorp-border rounded-full" style={{ backgroundColor: "#0000ee" }}>
                    <Video className="h-10 w-10" />
                  </div>
                </div>
                <div className="p-6 text-center">
                  <h3 className="font-black text-2xl mb-3 text-warm-gray-900">CREATE SOCIAL CLIPS</h3>
                  <p className="text-warm-gray-600 font-medium">Create engaging social media clips from your sermons</p>
                  <Button
                    className="zorp-button mt-4 w-full"
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
