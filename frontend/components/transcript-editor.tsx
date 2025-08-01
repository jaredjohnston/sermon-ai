"use client"

import { useState, useRef, useEffect } from "react"
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card"
import { Button } from "@/components/ui/button"
import { Badge } from "@/components/ui/badge"
import { Alert, AlertDescription } from "@/components/ui/alert"
import {
  FileText,
  Edit3,
  Save,
  X,
  Sparkles,
  Clock,
  CheckCircle2,
  AlertCircle,
  Copy,
  Download,
  Undo,
  Redo,
  Bold,
  Italic,
  List,
  ListOrdered,
  AlignLeft,
  AlignCenter,
  AlignRight,
  Heart,
  MessageCircle,
} from "lucide-react"
import { useToast } from "@/hooks/use-toast"
import { generateContent } from "@/lib/api"
import type { ContentSource, ContentResponse } from "@/types/api"

interface TranscriptEditorProps {
  content: ContentSource
  onContentGenerated: (contentId: string, contentResponse: ContentResponse) => void
  onBack: () => void
}

export function TranscriptEditor({ content, onContentGenerated, onBack }: TranscriptEditorProps) {
  const transcriptText = content.transcript?.content?.full_transcript || ""
  const [transcript, setTranscript] = useState(transcriptText)
  const [originalTranscript] = useState(transcriptText)
  const isTranscriptReady = Boolean(content.transcript?.content?.full_transcript)
  const isProcessing = content.status === 'preparing' || content.status === 'processing' || content.status === 'transcribing'
  const [isEditing, setIsEditing] = useState(false) // Read-only mode since editing is no longer needed
  const [isGenerating, setIsGenerating] = useState(false)
  const [hasUnsavedChanges, setHasUnsavedChanges] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const [undoStack, setUndoStack] = useState<string[]>([])
  const [redoStack, setRedoStack] = useState<string[]>([])
  const editorRef = useRef<HTMLDivElement>(null)
  const { toast } = useToast()
  const [selectedContentTypes, setSelectedContentTypes] = useState({
    summary: true,
    devotional: true,
    discussion_questions: true,
  })

  // Track changes for undo/redo
  useEffect(() => {
    if (transcript !== originalTranscript) {
      setHasUnsavedChanges(true)
    } else {
      setHasUnsavedChanges(false)
    }
  }, [transcript, originalTranscript])

  // Initialize editor with content
  useEffect(() => {
    if (editorRef.current) {
      editorRef.current.innerHTML = transcript
    }
  }, [])

  // Handle editor content changes
  const handleEditorChange = () => {
    if (editorRef.current) {
      const content = editorRef.current.innerHTML
      setTranscript(content)
      setUndoStack((prev) => [...prev, transcript])
      setRedoStack([])
    }
  }

  // Transcript editing removed - transcripts are read-only

  const handleCancel = () => {
    const originalText = content.transcript?.content?.full_transcript || ""
    if (editorRef.current) {
      editorRef.current.innerHTML = originalText
    }
    setTranscript(originalText)
    setHasUnsavedChanges(false)
    setUndoStack([])
    setRedoStack([])
  }

  const handleUndo = () => {
    if (undoStack.length > 0) {
      const previousState = undoStack[undoStack.length - 1]
      setRedoStack((prev) => [transcript, ...prev])
      setUndoStack((prev) => prev.slice(0, -1))
      setTranscript(previousState)
      if (editorRef.current) {
        editorRef.current.innerHTML = previousState
      }
    }
  }

  const handleRedo = () => {
    if (redoStack.length > 0) {
      const nextState = redoStack[0]
      setUndoStack((prev) => [...prev, transcript])
      setRedoStack((prev) => prev.slice(1))
      setTranscript(nextState)
      if (editorRef.current) {
        editorRef.current.innerHTML = nextState
      }
    }
  }

  const handleGenerateContent = async () => {
    if (!transcript.trim()) {
      toast({
        title: "No Transcript",
        description: "Please add a transcript before generating content.",
        variant: "destructive",
      })
      return
    }

    // Get selected content types
    const contentTypesToGenerate = Object.entries(selectedContentTypes)
      .filter(([_, isSelected]) => isSelected)
      .map(([type]) => type)

    if (contentTypesToGenerate.length === 0) {
      toast({
        title: "No Content Types Selected",
        description: "Please select at least one content type to generate.",
        variant: "destructive",
      })
      return
    }

    setIsGenerating(true)
    setError(null)

    try {
      // TODO: Update to use template-based generation when templates are available
      // For now, this will need to be updated to work with the new template system
      throw new Error('Content generation needs to be updated for template system')
      // const response = await generateContent(sermon.transcript?.transcript_id || '', templateId, customInstructions)
      // onContentGenerated(sermon.id, response)
      toast({
        title: "Content Generated",
        description: "New content has been generated from your transcript!",
      })
    } catch (error) {
      const errorMessage = error instanceof Error ? error.message : "Content generation failed"
      setError(errorMessage)
      toast({
        title: "Generation Failed",
        description: errorMessage,
        variant: "destructive",
      })
    } finally {
      setIsGenerating(false)
    }
  }

  const copyToClipboard = async () => {
    try {
      await navigator.clipboard.writeText(transcript)
      toast({
        title: "Copied to Clipboard",
        description: "Transcript copied successfully.",
      })
    } catch (error) {
      toast({
        title: "Copy Failed",
        description: "Unable to copy to clipboard.",
        variant: "destructive",
      })
    }
  }

  const downloadTranscript = () => {
    const blob = new Blob([transcript], { type: "text/plain" })
    const url = URL.createObjectURL(blob)
    const a = document.createElement("a")
    a.href = url
    a.download = `${content.filename}_transcript.txt`
    document.body.appendChild(a)
    a.click()
    document.body.removeChild(a)
    URL.revokeObjectURL(url)
  }

  const formatDate = (dateString: string) => {
    return new Date(dateString).toLocaleDateString("en-US", {
      year: "numeric",
      month: "long",
      day: "numeric",
      hour: "2-digit",
      minute: "2-digit",
    })
  }

  // Text formatting functions
  const formatText = (command: string) => {
    document.execCommand(command, false)
    handleEditorChange()
  }

  const handleContentTypeChange = (contentType: string) => {
    setSelectedContentTypes((prev) => ({
      ...prev,
      [contentType]: !prev[contentType as keyof typeof prev],
    }))
  }

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-3xl font-black text-warm-gray-900">TRANSCRIPT EDITOR</h1>
          <p className="text-warm-gray-600 font-medium">Edit your sermon transcript before generating content</p>
        </div>
        <Button variant="outline" onClick={onBack} className="font-bold bg-transparent">
          ← BACK TO LIBRARY
        </Button>
      </div>

      {/* File Info Card */}
      <Card className="zorp-card">
        <CardHeader className="border-b-2 border-warm-gray-800 bg-warm-gray-50">
          <CardTitle className="flex items-center">
            <div>
              <span className="font-black">{content.filename}</span>
              <div className="flex items-center space-x-4 text-sm text-warm-gray-600 mt-1">
                <span>Uploaded: {formatDate(content.uploadedAt)}</span>
                {isTranscriptReady ? (
                  <Badge className="bg-green-100 text-green-800">
                    <CheckCircle2 className="h-3 w-3 mr-1" />
                    Transcribed
                  </Badge>
                ) : isProcessing ? (
                  <Badge className="bg-orange-100 text-orange-800">
                    <Clock className="h-3 w-3 mr-1" />
                    Processing...
                  </Badge>
                ) : (
                  <Badge className="bg-red-100 text-red-800">
                    <AlertCircle className="h-3 w-3 mr-1" />
                    Not Ready
                  </Badge>
                )}
                {hasUnsavedChanges && (
                  <Badge className="bg-orange-100 text-orange-800">
                    <Clock className="h-3 w-3 mr-1" />
                    Unsaved Changes
                  </Badge>
                )}
              </div>
            </div>
          </CardTitle>
        </CardHeader>
      </Card>

      {/* Transcript Editor Card */}
      <Card className="zorp-card">
        <CardHeader className="border-b-2 border-warm-gray-800 bg-warm-gray-50">
          <div className="flex items-center justify-between">
            <CardTitle className="flex items-center space-x-3">
              <Edit3 className="h-5 w-5" />
              <span className="font-black">TRANSCRIPT</span>
            </CardTitle>
            <div className="flex items-center space-x-2">
              <div className="flex space-x-2">
                <Button variant="outline" size="sm" onClick={handleUndo} disabled={undoStack.length === 0}>
                  <Undo className="h-4 w-4" />
                </Button>
                <Button variant="outline" size="sm" onClick={handleRedo} disabled={redoStack.length === 0}>
                  <Redo className="h-4 w-4" />
                </Button>
                <Button variant="outline" size="sm" onClick={copyToClipboard}>
                  <Copy className="h-4 w-4" />
                </Button>
                <Button variant="outline" size="sm" onClick={downloadTranscript}>
                  <Download className="h-4 w-4" />
                </Button>
                <Button variant="outline" size="sm" onClick={handleCancel} disabled={!hasUnsavedChanges}>
                  <X className="h-4 w-4" />
                </Button>
                {/* Save button removed - transcripts are read-only */}
              </div>
            </div>
          </div>
        </CardHeader>
        <CardContent className="p-6">
          {!isTranscriptReady ? (
            <div className="min-h-[400px] flex items-center justify-center">
              <div className="text-center space-y-4">
                {isProcessing ? (
                  <>
                    <Clock className="h-12 w-12 text-orange-500 mx-auto animate-pulse" />
                    <h3 className="text-lg font-bold text-warm-gray-900">Transcript Processing</h3>
                    <p className="text-warm-gray-600">Your sermon is being transcribed. This may take a few minutes...</p>
                    <Button variant="outline" onClick={onBack} className="mt-4">
                      ← Back to Library
                    </Button>
                  </>
                ) : (
                  <>
                    <AlertCircle className="h-12 w-12 text-red-500 mx-auto" />
                    <h3 className="text-lg font-bold text-warm-gray-900">Transcript Not Available</h3>
                    <p className="text-warm-gray-600">The transcript for this sermon is not ready yet.</p>
                    <Button variant="outline" onClick={onBack} className="mt-4">
                      ← Back to Library
                    </Button>
                  </>
                )}
              </div>
            </div>
          ) : (
            <div className="space-y-4">
              {/* Text formatting toolbar */}
              <div className="flex flex-wrap gap-2 p-2 bg-warm-gray-50 border-2 border-warm-gray-200">
                <Button variant="ghost" size="sm" onClick={() => formatText("bold")}>
                  <Bold className="h-4 w-4" />
                </Button>
                <Button variant="ghost" size="sm" onClick={() => formatText("italic")}>
                  <Italic className="h-4 w-4" />
                </Button>
                <Button variant="ghost" size="sm" onClick={() => formatText("insertUnorderedList")}>
                  <List className="h-4 w-4" />
                </Button>
                <Button variant="ghost" size="sm" onClick={() => formatText("insertOrderedList")}>
                  <ListOrdered className="h-4 w-4" />
                </Button>
                <Button variant="ghost" size="sm" onClick={() => formatText("justifyLeft")}>
                  <AlignLeft className="h-4 w-4" />
                </Button>
                <Button variant="ghost" size="sm" onClick={() => formatText("justifyCenter")}>
                  <AlignCenter className="h-4 w-4" />
                </Button>
                <Button variant="ghost" size="sm" onClick={() => formatText("justifyRight")}>
                  <AlignRight className="h-4 w-4" />
                </Button>
              </div>

              {/* Editable content area */}
              <div
                ref={editorRef}
                contentEditable
                className="min-h-[400px] p-6 border-2 border-warm-gray-200 focus:outline-none font-mono text-sm leading-relaxed"
                style={{ borderColor: editorRef.current === document.activeElement ? "#0000ee" : undefined }}
                onInput={handleEditorChange}
                dangerouslySetInnerHTML={{ __html: transcript }}
              />
            </div>
          )}
        </CardContent>
      </Card>

      {/* Content Generation Section - Only show when transcript is ready */}
      {isTranscriptReady && (
        <Card
        className="bg-gradient-to-br from-blue-50 to-indigo-50 border-2 shadow-lg"
        style={{ borderColor: "#0000ee" }}
      >
        <CardHeader
          className="border-b-2 bg-gradient-to-r from-blue-100 to-indigo-100"
          style={{ borderColor: "#0000ee" }}
        >
          <CardTitle className="flex items-center space-x-3">
            <div className="p-2 text-white rounded-lg shadow-md" style={{ backgroundColor: "#0000ee" }}>
              <Sparkles className="h-5 w-5" />
            </div>
            <div>
              <span className="font-black" style={{ color: "#0000ee" }}>
                AI CONTENT GENERATION
              </span>
              <p className="text-sm font-medium mt-1" style={{ color: "#0000ee" }}>
                Transform your transcript into engaging content
              </p>
            </div>
          </CardTitle>
        </CardHeader>
        <CardContent className="p-8">
          <div className="space-y-6">
            {/* Content type selection */}
            <div className="bg-white/80 p-6 rounded-lg border" style={{ borderColor: "#0000ee" }}>
              <h3 className="font-bold mb-4" style={{ color: "#0000ee" }}>
                Select Content Types to Generate:
              </h3>

              <div className="grid grid-cols-1 md:grid-cols-3 gap-4 mb-6">
                <div
                  className={`flex items-center space-x-3 p-4 bg-white rounded-lg border-2 cursor-pointer transition-all hover:bg-blue-50 ${
                    selectedContentTypes.summary ? "bg-blue-50" : ""
                  }`}
                  style={{
                    borderColor: selectedContentTypes.summary ? "#0000ee" : "#e5e7eb",
                    backgroundColor: selectedContentTypes.summary ? "#f0f0ff" : "white",
                  }}
                  onClick={() => handleContentTypeChange("summary")}
                >
                  <div className="p-2 bg-blue-100 rounded-full">
                    <FileText className="h-4 w-4 text-blue-600" />
                  </div>
                  <p className="font-bold text-sm text-gray-900">SUMMARY</p>
                </div>

                <div
                  className={`flex items-center space-x-3 p-4 bg-white rounded-lg border-2 cursor-pointer transition-all hover:bg-blue-50 ${
                    selectedContentTypes.devotional ? "bg-blue-50" : ""
                  }`}
                  style={{
                    borderColor: selectedContentTypes.devotional ? "#0000ee" : "#e5e7eb",
                    backgroundColor: selectedContentTypes.devotional ? "#f0f0ff" : "white",
                  }}
                  onClick={() => handleContentTypeChange("devotional")}
                >
                  <div className="p-2 rounded-full" style={{ backgroundColor: "#f0f0ff" }}>
                    <Heart className="h-4 w-4" style={{ color: "#0000ee" }} />
                  </div>
                  <p className="font-bold text-sm text-gray-900">DEVOTIONAL</p>
                </div>

                <div
                  className={`flex items-center space-x-3 p-4 bg-white rounded-lg border-2 cursor-pointer transition-all hover:bg-blue-50 ${
                    selectedContentTypes.discussion_questions ? "bg-blue-50" : ""
                  }`}
                  style={{
                    borderColor: selectedContentTypes.discussion_questions ? "#0000ee" : "#e5e7eb",
                    backgroundColor: selectedContentTypes.discussion_questions ? "#f0f0ff" : "white",
                  }}
                  onClick={() => handleContentTypeChange("discussion_questions")}
                >
                  <div className="p-2 bg-green-100 rounded-full">
                    <MessageCircle className="h-4 w-4 text-green-600" />
                  </div>
                  <p className="font-bold text-sm text-gray-900">DISCUSSION</p>
                </div>
              </div>

              <p className="font-medium text-center mb-4" style={{ color: "#0000ee" }}>
                Generate AI-powered content from your sermon transcript
              </p>

              {error && (
                <Alert variant="destructive" className="mb-4 border-red-300 bg-red-50">
                  <AlertCircle className="h-4 w-4" />
                  <AlertDescription className="font-bold text-red-800">{error.toUpperCase()}</AlertDescription>
                </Alert>
              )}

              <div className="flex flex-col items-center space-y-4">
                <Button
                  className="text-white font-bold py-3 px-8 rounded-lg shadow-lg transform transition-all duration-200 hover:scale-105 disabled:opacity-50 disabled:transform-none"
                  style={{
                    background: `linear-gradient(to right, #0000ee, #4040ff)`,
                  }}
                  onClick={handleGenerateContent}
                  disabled={isGenerating || !transcript.trim() || hasUnsavedChanges}
                  size="lg"
                >
                  {isGenerating ? (
                    <>
                      <Clock className="h-5 w-5 mr-3 animate-spin" />
                      GENERATING CONTENT...
                    </>
                  ) : (
                    <>
                      <Sparkles className="h-5 w-5 mr-3" />
                      GENERATE AI CONTENT
                    </>
                  )}
                </Button>

                {hasUnsavedChanges && (
                  <div className="flex items-center space-x-2 text-amber-700 bg-amber-50 px-4 py-2 rounded-lg border border-amber-200">
                    <AlertCircle className="h-4 w-4" />
                    <p className="text-sm font-medium">Save your transcript changes before generating content</p>
                  </div>
                )}

                {!transcript.trim() && (
                  <div className="flex items-center space-x-2 text-gray-600 bg-gray-50 px-4 py-2 rounded-lg border border-warm-gray-200">
                    <FileText className="h-4 w-4" />
                    <p className="text-sm font-medium">Add a transcript to enable content generation</p>
                  </div>
                )}
              </div>

              {isGenerating && (
                <div
                  className="mt-6 bg-gradient-to-r from-blue-100 to-indigo-100 p-6 rounded-lg border-2"
                  style={{ borderColor: "#0000ee" }}
                >
                  <div className="flex items-center space-x-4">
                    <div className="relative">
                      <div
                        className="w-12 h-12 rounded-full flex items-center justify-center"
                        style={{ backgroundColor: "#0000ee" }}
                      >
                        <Sparkles className="h-6 w-6 text-white animate-pulse" />
                      </div>
                      <div
                        className="absolute inset-0 w-12 h-12 border-4 rounded-full animate-spin border-t-transparent"
                        style={{ borderColor: "#0000ee" }}
                      ></div>
                    </div>
                    <div>
                      <p className="font-bold text-lg" style={{ color: "#0000ee" }}>
                        AI IS WORKING ITS MAGIC...
                      </p>
                      <p className="text-sm font-medium" style={{ color: "#0000ee" }}>
                        Analyzing your transcript and generating personalized content. This may take a few moments.
                      </p>
                    </div>
                  </div>
                </div>
              )}
            </div>
          </div>
        </CardContent>
      </Card>
      )}
    </div>
  )
}
