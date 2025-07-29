"use client"

import { useState, useEffect } from "react"
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card"
import { Button } from "@/components/ui/button"
import { Badge } from "@/components/ui/badge"
import { Alert, AlertDescription } from "@/components/ui/alert"
import { Textarea } from "@/components/ui/textarea"
import { Checkbox } from "@/components/ui/checkbox"
import { Label } from "@/components/ui/label"
import { ScrollArea } from "@/components/ui/scroll-area"
import {
  FileText,
  Sparkles,
  Clock,
  CheckCircle2,
  AlertCircle,
  Copy,
  Download,
  ArrowLeft,
  BookOpen,
  Info,
} from "lucide-react"
import { useToast } from "@/hooks/use-toast"
import { useApiClient } from "@/lib/api-client"
import type { ContentSource, ContentResponse, ContentTemplatePublic } from "@/types/api"

interface TranscriptViewerProps {
  content: ContentSource
  onContentGenerated: (contentId: string, contentResponse: ContentResponse) => void
  onBack: () => void
}

export function TranscriptViewer({ content, onContentGenerated, onBack }: TranscriptViewerProps) {
  const transcriptText = content.transcript?.content?.full_transcript || ""
  const apiClient = useApiClient()
  const { toast } = useToast()
  
  const [templates, setTemplates] = useState<ContentTemplatePublic[]>([])
  const [selectedTemplates, setSelectedTemplates] = useState<Set<string>>(new Set())
  const [customInstructions, setCustomInstructions] = useState("")
  const [isGenerating, setIsGenerating] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const [loadingTemplates, setLoadingTemplates] = useState(true)

  // Load available templates
  useEffect(() => {
    loadTemplates()
  }, [])

  const loadTemplates = async () => {
    try {
      setLoadingTemplates(true)
      const data = await apiClient.listContentTemplates()
      // Only show active templates
      setTemplates(data.filter(t => t.status === "active"))
    } catch (error) {
      toast({
        title: "Failed to load templates",
        description: error instanceof Error ? error.message : "Please try again",
        variant: "destructive",
      })
    } finally {
      setLoadingTemplates(false)
    }
  }

  const handleTemplateToggle = (templateId: string) => {
    setSelectedTemplates(prev => {
      const newSet = new Set(prev)
      if (newSet.has(templateId)) {
        newSet.delete(templateId)
      } else {
        newSet.add(templateId)
      }
      return newSet
    })
  }

  const handleGenerate = async () => {
    if (selectedTemplates.size === 0) {
      toast({
        title: "No templates selected",
        description: "Please select at least one template to generate content",
        variant: "destructive",
      })
      return
    }

    setIsGenerating(true)
    setError(null)

    try {
      // Generate content for each selected template
      for (const templateId of selectedTemplates) {
        const template = templates.find(t => t.id === templateId)
        if (!template) continue

        // TODO: Call the actual content generation API
        // For now, we need to update the API to support template-based generation
        toast({
          title: "Generating content",
          description: `Creating ${template.name}...`,
        })

        // Placeholder for actual API call
        // const response = await apiClient.generateContent(
        //   sermon.transcript?.transcript_id || '',
        //   templateId,
        //   customInstructions
        // )
        // onContentGenerated(sermon.id, response)
      }

      toast({
        title: "Content generated successfully",
        description: "Your content has been created from the selected templates",
      })
      
      // TODO: Navigate to content view after generation
    } catch (error) {
      const errorMessage = error instanceof Error ? error.message : "Content generation failed"
      setError(errorMessage)
      toast({
        title: "Generation failed",
        description: errorMessage,
        variant: "destructive",
      })
    } finally {
      setIsGenerating(false)
    }
  }

  const handleCopyTranscript = () => {
    navigator.clipboard.writeText(transcriptText)
    toast({
      title: "Copied to clipboard",
      description: "Transcript has been copied to your clipboard",
    })
  }

  const getTranscriptStats = () => {
    const words = transcriptText.split(/\s+/).length
    const readingTime = Math.ceil(words / 200) // Average reading speed
    return { words, readingTime }
  }

  const { words, readingTime } = getTranscriptStats()

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-4">
          <Button variant="ghost" onClick={onBack} className="gap-2">
            <ArrowLeft className="h-4 w-4" />
            Back to Library
          </Button>
          <div>
            <h1 className="text-2xl font-bold">{content.filename}</h1>
            <div className="flex items-center gap-4 mt-1 text-sm text-muted-foreground">
              <span className="flex items-center gap-1">
                <Clock className="h-3 w-3" />
                {readingTime} min read
              </span>
              <span>{words.toLocaleString()} words</span>
            </div>
          </div>
        </div>
        <Button onClick={handleCopyTranscript} variant="outline" className="gap-2">
          <Copy className="h-4 w-4" />
          Copy Transcript
        </Button>
      </div>

      <div className="grid gap-6 lg:grid-cols-3">
        {/* Transcript Display */}
        <div className="lg:col-span-2">
          <Card>
            <CardHeader>
              <CardTitle className="flex items-center gap-2">
                <FileText className="h-5 w-5" />
                Transcript
              </CardTitle>
            </CardHeader>
            <CardContent>
              <ScrollArea className="h-[600px] pr-4">
                <div className="whitespace-pre-wrap text-sm leading-relaxed">
                  {transcriptText}
                </div>
              </ScrollArea>
            </CardContent>
          </Card>
        </div>

        {/* Content Generation Panel */}
        <div className="space-y-6">
          {/* Template Selection */}
          <Card>
            <CardHeader>
              <CardTitle className="flex items-center gap-2">
                <BookOpen className="h-5 w-5" />
                Select Templates
              </CardTitle>
            </CardHeader>
            <CardContent>
              {loadingTemplates ? (
                <div className="flex items-center justify-center py-8">
                  <div className="text-center">
                    <BookOpen className="h-8 w-8 text-muted-foreground mx-auto mb-2 animate-pulse" />
                    <p className="text-sm text-muted-foreground">Loading templates...</p>
                  </div>
                </div>
              ) : templates.length === 0 ? (
                <Alert>
                  <AlertCircle className="h-4 w-4" />
                  <AlertDescription>
                    No templates available. Please create templates first in the Templates section.
                  </AlertDescription>
                </Alert>
              ) : (
                <div className="space-y-3">
                  {templates.map((template) => (
                    <div key={template.id} className="flex items-start space-x-3">
                      <Checkbox
                        id={template.id}
                        checked={selectedTemplates.has(template.id)}
                        onCheckedChange={() => handleTemplateToggle(template.id)}
                      />
                      <div className="flex-1">
                        <Label
                          htmlFor={template.id}
                          className="text-sm font-medium cursor-pointer"
                        >
                          {template.name}
                        </Label>
                        {template.description && (
                          <p className="text-xs text-muted-foreground mt-1">
                            {template.description}
                          </p>
                        )}
                      </div>
                    </div>
                  ))}
                </div>
              )}
            </CardContent>
          </Card>

          {/* Custom Instructions */}
          <Card>
            <CardHeader>
              <CardTitle className="flex items-center gap-2">
                <Info className="h-5 w-5" />
                Custom Instructions (Optional)
              </CardTitle>
            </CardHeader>
            <CardContent>
              <Textarea
                placeholder="Add any specific context or instructions for content generation..."
                value={customInstructions}
                onChange={(e) => setCustomInstructions(e.target.value)}
                rows={4}
                className="resize-none"
              />
              <p className="text-xs text-muted-foreground mt-2">
                Provide additional context about your church, congregation, or specific requirements
              </p>
            </CardContent>
          </Card>

          {/* Error Display */}
          {error && (
            <Alert variant="destructive">
              <AlertCircle className="h-4 w-4" />
              <AlertDescription>{error}</AlertDescription>
            </Alert>
          )}

          {/* Generate Button */}
          <Button
            onClick={handleGenerate}
            disabled={isGenerating || selectedTemplates.size === 0}
            className="w-full gap-2"
            size="lg"
          >
            {isGenerating ? (
              <>
                <Clock className="h-4 w-4 animate-spin" />
                Generating Content...
              </>
            ) : (
              <>
                <Sparkles className="h-4 w-4" />
                Generate Content ({selectedTemplates.size} template{selectedTemplates.size !== 1 ? 's' : ''})
              </>
            )}
          </Button>
        </div>
      </div>
    </div>
  )
}