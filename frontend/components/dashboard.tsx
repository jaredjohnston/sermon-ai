"use client"

import { useState, useEffect } from "react"
import { SidebarProvider, SidebarInset, SidebarTrigger } from "@/components/ui/sidebar"
import { AppSidebar } from "./app-sidebar"
import { ProcessingStatus } from "./processing-status"
import { GeneratedContent } from "./generated-content"
import { DashboardContent } from "./dashboard-content"
import { SermonLibrary } from "./sermon-library"
import { AIAssistant } from "./ai-assistant"
import { TranscriptEditor } from "./transcript-editor"
import { VideoClips } from "./video-clips"
import type { SermonData, ProcessingStage, TranscriptionResponse, ContentResponse } from "@/types/api"
import { useToast } from "@/hooks/use-toast"

// Sample sermon data for testing
const SAMPLE_SERMONS: SermonData[] = [
  {
    id: "sample-1",
    filename: "The Good Shepherd - John 10.mp3",
    transcript: `Welcome everyone to our service today. Let's turn to John chapter 10, where Jesus speaks about being the Good Shepherd.

"I am the good shepherd. The good shepherd lays down his life for the sheep. The hired hand is not the shepherd and does not own the sheep. So when he sees the wolf coming, he abandons the sheep and runs away. Then the wolf attacks the flock and scatters it."

This passage teaches us about the heart of Jesus for His people. Unlike a hired hand who works for wages, Jesus cares for us with genuine love. He knows each of us by name, just as a shepherd knows his sheep.

When we face difficulties in life - the wolves that threaten to scatter us - Jesus doesn't abandon us. He stands between us and danger. He protects us, guides us, and provides for our needs.

The beautiful truth is that Jesus not only protects us, but He laid down His life for us. This is the ultimate expression of love - sacrificial love that puts others before self.

As we go through this week, remember that you are known, loved, and protected by the Good Shepherd. He will never leave you nor forsake you.

Let us pray together...`,
    uploadedAt: "2024-01-15T10:30:00Z",
    status: "completed",
    content: {
      summary:
        "This sermon explores Jesus as the Good Shepherd from John 10, emphasizing His sacrificial love, protection, and personal care for believers. Unlike hired hands who abandon sheep in danger, Jesus stands firm against threats and laid down His life for His flock.",
      devotional:
        "Take a moment today to reflect on Jesus as your Good Shepherd. In what areas of your life do you need His protection and guidance? Remember that He knows you by name and cares for you personally. When you face the 'wolves' of worry, fear, or uncertainty, trust that your Shepherd is watching over you with love.",
      discussion_questions:
        "1. What does it mean to you personally that Jesus knows you by name?\n2. How have you experienced Jesus' protection in difficult times?\n3. What are some 'wolves' in our modern world that threaten to scatter believers?\n4. How can we follow Jesus' example of sacrificial love in our relationships?\n5. In what ways can we trust the Good Shepherd's guidance this week?",
    },
  },
  {
    id: "sample-2",
    filename: "Faith Over Fear - Matthew 14.mp4",
    transcript: `Good morning, church family. Today we're looking at Matthew 14, the story of Peter walking on water.

"Shortly before dawn Jesus went out to them, walking on the lake. When the disciples saw him walking on the lake, they were terrified. 'It's a ghost,' they said, and cried out in fear. But Jesus immediately said to them: 'Take courage! It is I. Don't be afraid.'"

Picture this scene: the disciples are in a boat, fighting against strong winds and waves. They're exhausted, afraid, and feeling alone. Then they see Jesus walking toward them on the water.

Peter's response is remarkable: "Lord, if it's you, tell me to come to you on the water." And Jesus simply says, "Come."

Peter steps out of the boat. He actually walks on water! But then he sees the wind and becomes afraid, and he begins to sink.

Here's what I want us to see: Peter's faith wasn't perfect, but it was real. He took the step. He got out of the boat when others stayed inside.

Sometimes we focus on Peter sinking, but let's celebrate that he walked on water! Eleven disciples stayed in the boat, but Peter experienced a miracle.

What boats is God calling you to step out of? What fears are keeping you from experiencing His power in your life?

Faith doesn't mean the absence of fear - it means choosing to trust God despite our fears.`,
    uploadedAt: "2024-01-08T09:15:00Z",
    status: "completed",
  },
  {
    id: "sample-3",
    filename: "Love Your Neighbor - Luke 10.wav",
    transcript: `Let's dive into one of Jesus' most powerful parables today - the Good Samaritan from Luke 10.

A man asked Jesus, "Who is my neighbor?" Jesus responded with this story:

"A man was going down from Jerusalem to Jericho, when he was attacked by robbers. They stripped him of his clothes, beat him and went away, leaving him half dead."

Three people passed by this wounded man. A priest saw him and passed by on the other side. A Levite did the same. But then a Samaritan came along.

Now, this is significant because Jews and Samaritans didn't get along. They had deep cultural and religious differences. Yet this Samaritan stopped, bandaged the man's wounds, took him to an inn, and paid for his care.

Jesus asks, "Which of these three do you think was a neighbor to the man who fell into the hands of robbers?"

The answer is obvious - the one who showed mercy.

Our neighbor isn't just the person who lives next door or looks like us or shares our beliefs. Our neighbor is anyone in need that God places in our path.

Sometimes we're so busy with religious activities that we miss opportunities to show love. The priest and Levite were probably on their way to important religious duties, but they missed the most important thing - loving their neighbor.

How can we be Good Samaritans in our community this week?`,
    uploadedAt: "2024-01-01T11:00:00Z",
    status: "completed",
  },
]

export function Dashboard() {
  const [sermons, setSermons] = useState<SermonData[]>([])
  const [currentStage, setCurrentStage] = useState<ProcessingStage>("idle")
  const [currentSermon, setCurrentSermon] = useState<SermonData | null>(null)
  const [currentView, setCurrentView] = useState("dashboard")
  const [error, setError] = useState<string | null>(null)
  const { toast } = useToast()

  // Load sermons from localStorage on mount
  useEffect(() => {
    const savedSermons = localStorage.getItem("sermon-history")
    if (savedSermons) {
      const parsedSermons = JSON.parse(savedSermons)
      setSermons(parsedSermons)
    } else {
      // If no saved sermons, use sample data
      setSermons(SAMPLE_SERMONS)
      localStorage.setItem("sermon-history", JSON.stringify(SAMPLE_SERMONS))
    }
  }, [])

  // Save sermons to localStorage whenever sermons change
  useEffect(() => {
    localStorage.setItem("sermon-history", JSON.stringify(sermons))
  }, [sermons])

  const handleUploadStart = () => {
    setCurrentStage("uploading")
    setError(null)
  }

  const handleUploadSuccess = async (data: TranscriptionResponse) => {
    const newSermon: SermonData = {
      id: Date.now().toString(),
      filename: data.filename,
      transcript: data.transcript,
      uploadedAt: data.processed_at,
      status: "transcribing",
    }

    setCurrentSermon(newSermon)
    setSermons((prev) => [newSermon, ...prev])

    // Immediately go to transcript editor after upload
    setCurrentView("transcript-editor")
    setCurrentStage("idle")

    toast({
      title: "Upload Complete",
      description: "Your sermon has been uploaded. You can now edit the transcript.",
    })
  }

  const handleUploadError = (errorMessage: string) => {
    setError(errorMessage)
    setCurrentStage("error")
  }

  const handleRetry = () => {
    setCurrentStage("idle")
    setCurrentSermon(null)
    setError(null)
    setCurrentView("dashboard")
  }

  const handleViewChange = (view: string) => {
    setCurrentView(view)
    if (view === "dashboard") {
      setCurrentStage("idle")
      setCurrentSermon(null)
      setError(null)
    }
  }

  const handleSermonSelect = (sermon: SermonData) => {
    setCurrentSermon(sermon)
    if (sermon.content) {
      setCurrentView("content")
      setCurrentStage("completed")
    } else {
      setCurrentView("transcript-editor")
    }
  }

  const handleSermonDelete = (sermonId: string) => {
    setSermons((prev) => prev.filter((s) => s.id !== sermonId))
    if (currentSermon?.id === sermonId) {
      setCurrentSermon(null)
      setCurrentStage("idle")
      setCurrentView("dashboard")
    }
    toast({
      title: "Sermon Deleted",
      description: "The sermon has been removed from your library.",
    })
  }

  const handleTranscriptEdit = (sermon: SermonData) => {
    setCurrentSermon(sermon)
    setCurrentView("transcript-editor")
  }

  const handleContentEdit = (sermon: SermonData) => {
    setCurrentSermon(sermon)
    setCurrentView("content")
  }

  const handleTranscriptUpdate = (sermonId: string, newTranscript: string) => {
    setSermons((prev) =>
      prev.map((sermon) => (sermon.id === sermonId ? { ...sermon, transcript: newTranscript } : sermon)),
    )
    if (currentSermon?.id === sermonId) {
      setCurrentSermon({ ...currentSermon, transcript: newTranscript })
    }
  }

  const handleContentGenerated = (sermonId: string, content: ContentResponse["content"]) => {
    setSermons((prev) =>
      prev.map((sermon) => (sermon.id === sermonId ? { ...sermon, content, status: "completed" } : sermon)),
    )
    if (currentSermon?.id === sermonId) {
      setCurrentSermon({ ...currentSermon, content, status: "completed" })
      setCurrentView("content")
      setCurrentStage("completed")
    }
  }

  const renderContent = () => {
    // Show processing status if currently processing
    if (["uploading", "transcribing", "generating", "error"].includes(currentStage)) {
      return (
        <ProcessingStatus stage={currentStage} filename={currentSermon?.filename} error={error} onRetry={handleRetry} />
      )
    }

    switch (currentView) {
      case "content":
        if (currentSermon?.content) {
          return (
            <GeneratedContent
              content={currentSermon.content}
              generatedAt={currentSermon.uploadedAt}
              filename={currentSermon.filename}
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
          <SermonLibrary
            sermons={sermons}
            onSermonSelect={handleSermonSelect}
            onSermonDelete={handleSermonDelete}
            onTranscriptEdit={handleTranscriptEdit}
            onContentEdit={handleContentEdit}
          />
        )

      case "transcript-editor":
        if (currentSermon) {
          return (
            <TranscriptEditor
              sermon={currentSermon}
              onTranscriptUpdate={handleTranscriptUpdate}
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

      case "settings":
        return (
          <div className="space-y-6">
            <h1 className="text-3xl font-black text-warm-gray-900">SETTINGS</h1>
            <p className="text-warm-gray-600 font-medium">Configure your preferences and account settings</p>
            <div className="text-center py-12">
              <p className="text-warm-gray-600">Settings panel coming soon...</p>
            </div>
          </div>
        )

      case "help":
        return (
          <div className="space-y-6">
            <h1 className="text-3xl font-black text-warm-gray-900">HELP & SUPPORT</h1>
            <p className="text-warm-gray-600 font-medium">Get help with using Sermon AI</p>
            <div className="text-center py-12">
              <p className="text-warm-gray-600">Help documentation coming soon...</p>
            </div>
          </div>
        )
      case "voice-style":
        return (
          <div className="space-y-6">
            <h1 className="text-3xl font-black text-warm-gray-900">VOICE & STYLE</h1>
            <p className="text-warm-gray-600 font-medium">Customize your content voice and style preferences</p>
            <div className="text-center py-12">
              <p className="text-warm-gray-600">Voice & Style customization coming soon...</p>
            </div>
          </div>
        )

      default:
        return (
          <DashboardContent
            sermons={sermons}
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
        sermons={sermons}
        currentView={currentView}
        onViewChange={handleViewChange}
        onSermonSelect={handleSermonSelect}
      />
      <SidebarInset>
        <header className="flex h-16 shrink-0 items-center gap-2 border-b border-warm-gray-200 bg-card">
          <SidebarTrigger className="-ml-1" />
          <div className="ml-auto flex items-center space-x-4">{/* Add any header actions here */}</div>
        </header>
        <div className="flex flex-1 flex-col bg-warm-white">
          <div className="min-h-[100vh] flex-1 p-4 md:p-8">{renderContent()}</div>
        </div>
      </SidebarInset>
    </SidebarProvider>
  )
}
