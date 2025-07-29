"use client"

import { useState, useEffect } from "react"
import { SidebarProvider, SidebarInset, SidebarTrigger } from "@/components/ui/sidebar"
import { useAuth } from "@/components/providers/AuthProvider"
import { Button } from "@/components/ui/button"
import { 
  DropdownMenu, 
  DropdownMenuContent, 
  DropdownMenuItem, 
  DropdownMenuTrigger 
} from "@/components/ui/dropdown-menu"
import { Avatar, AvatarFallback } from "@/components/ui/avatar"
import { LogOut, User } from "lucide-react"
import { AppSidebar } from "./app-sidebar"
import { ProcessingStatus } from "./processing-status"
import { GeneratedContent } from "./generated-content"
import { DashboardContent } from "./dashboard-content"
import { ContentLibrary } from "./content-library"
import { AIAssistant } from "./ai-assistant"
import { ContentViewer } from "./content-viewer"
import { VideoClips } from "./video-clips"
import { TemplatesList } from "./templates-list"
import type { ContentSource, ProcessingStage, TranscriptionResponse, ContentGenerationResponse, GeneratedContentModel } from "@/types/api"
import { useToast } from "@/hooks/use-toast"
import { useApiClient } from "@/lib/api-client"
import { transformTranscriptListToContentSources, needsTranscriptData, transformContentGenerationResponse } from "@/lib/data-transformers"

// Sample sermon data for testing
const SAMPLE_SERMONS: ContentSource[] = [
  {
    id: "sample-1",
    filename: "The Good Shepherd - John 10.mp3",
    transcript: {
      transcript_id: "transcript-1",
      video: {
        id: "video-1",
        filename: "The Good Shepherd - John 10.mp3",
        duration_seconds: 1800,
        size_bytes: 86000000,
        content_type: "audio/mpeg",
      },
      status: "completed",
      content: {
        full_transcript: `Welcome everyone to our service today. Let's turn to John chapter 10, where Jesus speaks about being the Good Shepherd.

"I am the good shepherd. The good shepherd lays down his life for the sheep. The hired hand is not the shepherd and does not own the sheep. So when he sees the wolf coming, he abandons the sheep and runs away. Then the wolf attacks the flock and scatters it."

This passage teaches us about the heart of Jesus for His people. Unlike a hired hand who works for wages, Jesus cares for us with genuine love. He knows each of us by name, just as a shepherd knows his sheep.

When we face difficulties in life - the wolves that threaten to scatter us - Jesus doesn't abandon us. He stands between us and danger. He protects us, guides us, and provides for our needs.

The beautiful truth is that Jesus not only protects us, but He laid down His life for us. This is the ultimate expression of love - sacrificial love that puts others before self.

As we go through this week, remember that you are known, loved, and protected by the Good Shepherd. He will never leave you nor forsake you.

Let us pray together...`,
        utterances: [
          {
            speaker: 1,
            text: "Welcome everyone to our service today. Let's turn to John chapter 10, where Jesus speaks about being the Good Shepherd.",
            start: 0,
            end: 5.2,
            confidence: 0.95,
          },
          {
            speaker: 1,
            text: "I am the good shepherd. The good shepherd lays down his life for the sheep.",
            start: 5.5,
            end: 12.1,
            confidence: 0.98,
          },
        ],
        confidence: 0.96,
      },
      created_at: "2024-01-15T10:30:00Z",
      updated_at: "2024-01-15T10:35:00Z",
      completed_at: "2024-01-15T10:35:00Z",
      request_id: "req-123",
    },
    uploadedAt: "2024-01-15T10:30:00Z",
    status: "completed",
    content: [
      {
        id: "content-1",
        client_id: "client-1",
        transcript_id: "transcript-1",
        template_id: "template-summary",
        content: "This sermon explores Jesus as the Good Shepherd from John 10, emphasizing His sacrificial love, protection, and personal care for believers. Unlike hired hands who abandon sheep in danger, Jesus stands firm against threats and laid down His life for His flock.",
        content_metadata: { template_name: "Summary" },
        generation_settings: { model: "gpt-4o", temperature: 0.7 },
        generation_cost_cents: 45,
        generation_duration_ms: 2300,
        user_edits_count: 0,
        created_at: "2024-01-15T10:35:00Z",
        created_by: "user-1",
        updated_at: "2024-01-15T10:35:00Z",
        updated_by: "user-1",
      },
      {
        id: "content-2",
        client_id: "client-1",
        transcript_id: "transcript-1",
        template_id: "template-devotional",
        content: "Take a moment today to reflect on Jesus as your Good Shepherd. In what areas of your life do you need His protection and guidance? Remember that He knows you by name and cares for you personally. When you face the 'wolves' of worry, fear, or uncertainty, trust that your Shepherd is watching over you with love.",
        content_metadata: { template_name: "Devotional" },
        generation_settings: { model: "gpt-4o", temperature: 0.7 },
        generation_cost_cents: 38,
        generation_duration_ms: 2100,
        user_edits_count: 0,
        created_at: "2024-01-15T10:36:00Z",
        created_by: "user-1",
        updated_at: "2024-01-15T10:36:00Z",
        updated_by: "user-1",
      },
    ],
  },
]

export function Dashboard() {
  const [contents, setContents] = useState<ContentSource[]>([])
  const [currentStage, setCurrentStage] = useState<ProcessingStage>("idle")
  const [currentContent, setCurrentContent] = useState<ContentSource | null>(null)
  const [currentView, setCurrentView] = useState("dashboard")
  const [error, setError] = useState<string | null>(null)
  const [loading, setLoading] = useState(true)
  const [pollingTranscriptIds, setPollingTranscriptIds] = useState<Set<string>>(new Set())
  const { toast } = useToast()
  const { user, signOut } = useAuth()
  const apiClient = useApiClient()

  const handleSignOut = async () => {
    try {
      await signOut()
      toast({
        title: "Signed out",
        description: "You have been successfully signed out.",
      })
    } catch (error) {
      toast({
        variant: "destructive",
        title: "Error",
        description: "Failed to sign out. Please try again.",
      })
    }
  }

  // Load transcripts from API on mount
  useEffect(() => {
    loadTranscripts()
  }, [])

  // Poll for transcription status
  useEffect(() => {
    if (pollingTranscriptIds.size === 0) return

    const pollInterval = setInterval(async () => {
      for (const transcriptId of pollingTranscriptIds) {
        try {
          const status = await apiClient.getTranscriptionStatus(transcriptId)
          
          if (status.status === 'completed') {
            // Fetch full transcript data
            const fullTranscript = await apiClient.getFullTranscript(transcriptId)
            
            // Update content with completed transcript
            setContents(prev => prev.map(content => 
              content.id === transcriptId 
                ? { ...content, transcript: fullTranscript, status: 'completed' }
                : content
            ))
            
            // Update current content if it's the one we're polling
            if (currentContent?.id === transcriptId) {
              setCurrentContent(prev => prev ? { ...prev, transcript: fullTranscript, status: 'completed' } : null)
            }
            
            // Stop polling this transcript
            setPollingTranscriptIds(prev => {
              const newSet = new Set(prev)
              newSet.delete(transcriptId)
              return newSet
            })
            
            // Show completion notification
            toast({
              title: "Transcription Complete!",
              description: "Your content is now ready for generation.",
            })
          } else if (status.status === 'failed') {
            // Handle transcription failure
            setContents(prev => prev.map(content => 
              content.id === transcriptId 
                ? { ...content, status: 'error' }
                : content
            ))
            
            // Stop polling this transcript
            setPollingTranscriptIds(prev => {
              const newSet = new Set(prev)
              newSet.delete(transcriptId)
              return newSet
            })
            
            // Show error notification
            toast({
              title: "Transcription Failed",
              description: "Please contact support if this persists.",
              variant: "destructive",
            })
          }
        } catch (error) {
          console.error(`Failed to check transcription status for ${transcriptId}:`, error)
        }
      }
    }, 5000) // Poll every 5 seconds

    return () => clearInterval(pollInterval)
  }, [pollingTranscriptIds, currentContent?.id, apiClient, toast])

  const loadTranscripts = async () => {
    try {
      setLoading(true)
      setError(null)
      
      // Fetch transcripts from API
      const response = await apiClient.listTranscripts(50, 0, 'completed')
      
      // Transform backend data to frontend format
      const contentSources = transformTranscriptListToContentSources(response.transcripts)
      
      setContents(contentSources)
      
      // If no transcripts found, show sample data temporarily
      if (contentSources.length === 0) {
        setContents(SAMPLE_SERMONS)
      }
      
    } catch (error) {
      console.error('Failed to load transcripts:', error)
      setError(error instanceof Error ? error.message : 'Failed to load transcripts')
      
      // Fallback to sample data on error
      setContents(SAMPLE_SERMONS)
      
      toast({
        title: "Failed to load transcripts",
        description: "Using sample data. Check your connection and try again.",
        variant: "destructive",
      })
    } finally {
      setLoading(false)
    }
  }

  const handleUploadStart = () => {
    setCurrentStage("uploading")
    setError(null)
  }

  const handleUploadSuccess = async (data: TranscriptionResponse) => {
    const transcriptId = data.transcript_id
    const newContent: ContentSource = {
      id: transcriptId,
      filename: data.filename,
      transcript: undefined, // Transcript will be populated when transcription completes
      uploadedAt: data.created_at,
      status: "transcribing",
    }

    setCurrentContent(newContent)
    setContents((prev) => [newContent, ...prev])

    // Start polling for this transcript
    setPollingTranscriptIds(prev => new Set(prev).add(transcriptId))

    // Immediately go to transcript editor after upload
    setCurrentView("transcript-editor")
    setCurrentStage("idle")

    toast({
      title: "Upload Complete",
      description: "Now transcribing your audio. This usually takes 30-60 seconds.",
    })
  }

  const handleUploadError = (errorMessage: string) => {
    setError(errorMessage)
    setCurrentStage("error")
  }

  const handleRetry = () => {
    setCurrentStage("idle")
    setCurrentContent(null)
    setError(null)
    setCurrentView("dashboard")
    
    // Also retry loading transcripts if there was an API error
    if (error && error.includes('Failed to load transcripts')) {
      loadTranscripts()
    }
  }

  const handleViewChange = (view: string) => {
    setCurrentView(view)
    if (view === "dashboard") {
      setCurrentStage("idle")
      setCurrentContent(null)
      setError(null)
    }
  }

  const handleContentSelect = (content: ContentSource) => {
    setCurrentContent(content)
    if (content.content) {
      setCurrentView("content")
      setCurrentStage("completed")
    } else {
      setCurrentView("transcript-editor")
    }
  }

  const handleContentDelete = (contentId: string) => {
    setContents((prev) => prev.filter((s) => s.id !== contentId))
    if (currentContent?.id === contentId) {
      setCurrentContent(null)
      setCurrentStage("idle")
      setCurrentView("dashboard")
    }
    toast({
      title: "Content Deleted",
      description: "The content has been removed from your library.",
    })
  }

  const handleTranscriptEdit = (content: ContentSource) => {
    setCurrentContent(content)
    setCurrentView("transcript-editor")
  }

  const handleContentEdit = (content: ContentSource) => {
    setCurrentContent(content)
    setCurrentView("content")
  }

  // Transcript editing removed - transcripts are 99% accurate from Deepgram

  const handleContentGenerated = async (contentId: string, contentResponse: ContentGenerationResponse) => {
    try {
      // Fetch the generated content details to get full data
      const generatedContent = await apiClient.getGeneratedContent(contentResponse.id)
      
      // Update the contents state with the new generated content
      setContents((prev) =>
        prev.map((content) => 
          content.id === contentId 
            ? { ...content, content: [...(content.content || []), generatedContent], status: "completed" }
            : content
        ),
      )
      
      // Update current content if it's the one being generated
      if (currentContent?.id === contentId) {
        setCurrentContent({ 
          ...currentContent, 
          content: [...(currentContent.content || []), generatedContent], 
          status: "completed" 
        })
        // Navigate to content view after successful generation
        setCurrentView("content")
        setCurrentStage("completed")
      }
    } catch (error) {
      console.error('Failed to fetch generated content details:', error)
      toast({
        title: "Error loading generated content",
        description: "Content was generated but failed to load details",
        variant: "destructive",
      })
    }
  }

  const renderContent = () => {
    // Show loading state while fetching initial transcript data
    if (loading && currentView === "dashboard") {
      return (
        <div className="flex items-center justify-center py-12">
          <div className="text-center">
            <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-warm-gray-900 mx-auto mb-4"></div>
            <p className="text-warm-gray-600">Loading your content...</p>
          </div>
        </div>
      )
    }

    // Show processing status if currently processing
    if (["uploading", "transcribing", "generating", "error"].includes(currentStage)) {
      return (
        <ProcessingStatus stage={currentStage} filename={currentContent?.filename} error={error || undefined} onRetry={handleRetry} />
      )
    }

    switch (currentView) {
      case "content":
        if (currentContent?.content) {
          return (
            <GeneratedContent
              content={currentContent.content}
              generatedAt={currentContent.uploadedAt}
              filename={currentContent.filename}
              onBack={() => setCurrentView("library")}
            />
          )
        }
        return (
          <div className="text-center py-12">
            <h2 className="text-xl font-semibold mb-2 text-warm-gray-900">No Content Selected</h2>
            <p className="text-warm-gray-600">Select a completed sermon to view its generated content</p>
          </div>
        )

      case "library":
        return (
          <ContentLibrary
            contents={contents}
            onContentSelect={handleContentSelect}
            onContentDelete={handleContentDelete}
            onTranscriptEdit={handleTranscriptEdit}
            onContentEdit={handleContentEdit}
          />
        )

      case "transcript-editor":
        if (currentContent) {
          return (
            <ContentViewer
              content={currentContent}
              onContentGenerated={handleContentGenerated}
              onBack={() => setCurrentView("library")}
            />
          )
        }
        return null

      case "assistant":
        return <AIAssistant />

      case "video-clips":
        return <VideoClips />

      case "voice-style":
        return <TemplatesList />

      case "settings":
        return (
          <div className="space-y-8">
            {/* Header */}
            <div>
              <h1 className="text-3xl font-black text-warm-gray-900">SETTINGS</h1>
              <p className="text-warm-gray-600 font-medium">Configure your preferences and account settings</p>
            </div>
            
            {/* Coming Soon */}
            <div className="text-center py-12">
              <p className="text-warm-gray-600">Settings panel coming soon...</p>
            </div>
          </div>
        )

      case "help":
        return (
          <div className="space-y-8">
            {/* Header */}
            <div>
              <h1 className="text-3xl font-black text-warm-gray-900">HELP & SUPPORT</h1>
              <p className="text-warm-gray-600 font-medium">Get help with using Churchable</p>
            </div>
            
            {/* Coming Soon */}
            <div className="text-center py-12">
              <p className="text-warm-gray-600">Help documentation coming soon...</p>
            </div>
          </div>
        )
      case "voice-style":
        return (
          <div className="space-y-8">
            {/* Header */}
            <div>
              <h1 className="text-3xl font-black text-warm-gray-900">TEMPLATES</h1>
              <p className="text-warm-gray-600 font-medium">Manage or build custom templates for content generation</p>
            </div>
            
            {/* Coming Soon */}
            <div className="text-center py-12">
              <p className="text-warm-gray-600">Template builder coming soon...</p>
            </div>
          </div>
        )

      default:
        return (
          <DashboardContent
            contents={contents}
            onViewChange={handleViewChange}
            onUploadStart={handleUploadStart}
            onUploadSuccess={handleUploadSuccess}
            onUploadError={handleUploadError}
            onTranscriptEdit={handleTranscriptEdit}
            onContentEdit={handleContentEdit}
          />
        )
    }
  }

  return (
    <SidebarProvider>
      <AppSidebar
        contents={contents}
        currentView={currentView}
        onViewChange={handleViewChange}
        onContentSelect={handleContentSelect}
      />
      <SidebarInset>
        <header className="flex h-16 shrink-0 items-center gap-2 border-b border-warm-gray-200 bg-white px-4">
          <SidebarTrigger className="-ml-1" />
          <div className="ml-auto flex items-center space-x-4">
            <DropdownMenu>
              <DropdownMenuTrigger asChild>
                <Button variant="ghost" className="relative h-10 w-10 rounded-full">
                  <Avatar className="h-10 w-10">
                    <AvatarFallback>
                      {user?.email?.substring(0, 2).toUpperCase() || 'U'}
                    </AvatarFallback>
                  </Avatar>
                </Button>
              </DropdownMenuTrigger>
              <DropdownMenuContent className="w-56" align="end" forceMount>
                <DropdownMenuItem className="flex-col items-start">
                  <div className="flex items-center">
                    <User className="mr-2 h-4 w-4" />
                    <span>Account</span>
                  </div>
                  <p className="text-xs text-muted-foreground mt-1">
                    {user?.email}
                  </p>
                </DropdownMenuItem>
                <DropdownMenuItem onClick={handleSignOut}>
                  <LogOut className="mr-2 h-4 w-4" />
                  <span>Sign out</span>
                </DropdownMenuItem>
              </DropdownMenuContent>
            </DropdownMenu>
          </div>
        </header>
        <div className="flex flex-1 flex-col bg-warm-white">
          <div className="min-h-[100vh] flex-1 p-4 md:p-8">{renderContent()}</div>
        </div>
      </SidebarInset>
    </SidebarProvider>
  )
}
