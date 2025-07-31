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
import { transformContentGenerationResponse } from "@/lib/data-transformers"
import type { ContentSource, ContentResponse, ContentTemplatePublic, ContentGenerationRequest } from "@/types/api"

interface ContentViewerProps {
  content: ContentSource
  onContentGenerated: (contentId: string, contentResponse: ContentResponse) => void
  onBack: () => void
}

export function ContentViewer({ content, onContentGenerated, onBack }: ContentViewerProps) {
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
      // Validate we have transcript ID
      const transcriptId = content.id // ContentSource.id is the transcript_id
      if (!transcriptId) {
        throw new Error("No transcript ID available")
      }

      let successCount = 0
      const errors: string[] = []

      // Generate content for each selected template
      for (const templateId of selectedTemplates) {
        const template = templates.find(t => t.id === templateId)
        if (!template) continue

        toast({
          title: "Generating content",
          description: `Creating ${template.name}...`,
        })

        try {
          // Prepare the request
          const request: ContentGenerationRequest = {
            transcript_id: transcriptId,
            template_id: templateId,
            custom_instructions: customInstructions || undefined
          }

          // Call the API
          const response = await apiClient.generateContent(request)
          
          // Transform the response to match frontend expectations
          const transformedContent = transformContentGenerationResponse(
            response,
            transcriptId,
            templateId,
            template.name
          )
          
          // Transform response to ContentResponse format
          const contentResponse: ContentResponse = {
            id: response.id,
            content: response.content,
            metadata: {
              generated_at: new Date().toISOString(),
              model_used: "gpt-4o",
              content_type: "template-generated",
              template_id: template.id,
              template_name: template.name,
              generation_cost_cents: response.generation_cost_cents,
              generation_duration_ms: response.generation_duration_ms,
            },
          }
          
          // Notify parent component
          onContentGenerated(content.id, contentResponse)
          successCount++
        } catch (error) {
          const errorMessage = error instanceof Error ? error.message : 'Unknown error'
          errors.push(`${template.name}: ${errorMessage}`)
          console.error(`Failed to generate content for template ${template.name}:`, error)
        }
      }

      // Show results
      if (successCount > 0 && errors.length === 0) {
        toast({
          title: "Content generated successfully",
          description: `Created ${successCount} content piece${successCount > 1 ? 's' : ''}`,
        })
      } else if (successCount > 0 && errors.length > 0) {
        toast({
          title: "Partial success",
          description: `Generated ${successCount} of ${selectedTemplates.size} templates. Some failed.`,
          variant: "default",
        })
      } else if (errors.length > 0) {
        throw new Error(errors.join('; '))
      }
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
      <div>
        <Button variant="ghost" onClick={onBack} className="gap-2 mb-4">
          <ArrowLeft className="h-4 w-4" />
          Go back
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