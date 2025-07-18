"use client"

import { useState } from "react"
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card"
import { Button } from "@/components/ui/button"
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs"
import { Copy, FileText, Heart, MessageCircle, CheckCircle2, ArrowLeft, BookOpen, Users, Lightbulb } from "lucide-react"
import type { GeneratedContentModel } from "@/types/api"
import { useToast } from "@/hooks/use-toast"

interface GeneratedContentProps {
  content: GeneratedContentModel[]
  generatedAt: string
  filename?: string
  onBack?: () => void
}

// Dynamic icon mapping based on content type
const getContentTypeIcon = (templateName: string) => {
  const name = templateName.toLowerCase()
  if (name.includes('summary')) return FileText
  if (name.includes('devotional')) return Heart
  if (name.includes('discussion') || name.includes('questions')) return MessageCircle
  if (name.includes('small group') || name.includes('group')) return Users
  if (name.includes('study') || name.includes('bible')) return BookOpen
  return Lightbulb // Default icon
}

const getContentTypeColor = (templateName: string) => {
  const name = templateName.toLowerCase()
  if (name.includes('summary')) return 'bg-blue-100 text-blue-800'
  if (name.includes('devotional')) return 'bg-purple-100 text-purple-800'
  if (name.includes('discussion') || name.includes('questions')) return 'bg-green-100 text-green-800'
  if (name.includes('small group') || name.includes('group')) return 'bg-orange-100 text-orange-800'
  if (name.includes('study') || name.includes('bible')) return 'bg-indigo-100 text-indigo-800'
  return 'bg-gray-100 text-gray-800' // Default color
}

export function GeneratedContent({ content, generatedAt, filename, onBack }: GeneratedContentProps) {
  const [copiedSection, setCopiedSection] = useState<string | null>(null)
  const { toast } = useToast()

  // Create dynamic tabs from the content array
  const contentTabs = content.map(item => ({
    id: item.id,
    key: item.template_id,
    label: item.content_metadata?.template_name || 'Generated Content',
    description: `AI-generated ${item.content_metadata?.template_name?.toLowerCase() || 'content'}`,
    icon: getContentTypeIcon(item.content_metadata?.template_name || ''),
    color: getContentTypeColor(item.content_metadata?.template_name || ''),
    content: item.content
  }))

  const copyToClipboard = async (text: string, contentItem: typeof contentTabs[0]) => {
    try {
      await navigator.clipboard.writeText(text)
      setCopiedSection(contentItem.id)
      toast({
        title: "Copied to clipboard",
        description: `${contentItem.label} copied successfully`,
      })
      setTimeout(() => setCopiedSection(null), 2000)
    } catch (error) {
      toast({
        title: "Copy failed",
        description: "Unable to copy to clipboard",
        variant: "destructive",
      })
    }
  }

  return (
    <div className="w-full max-w-none mx-auto space-y-6">
      {/* Navigation Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-3xl font-black text-warm-gray-900">GENERATED CONTENT</h1>
          <p className="text-warm-gray-600 font-medium">Review and share your AI-generated sermon content</p>
        </div>
        {onBack && (
          <Button variant="outline" onClick={onBack} className="font-bold bg-transparent">
            <ArrowLeft className="h-4 w-4 mr-2" />
            BACK TO LIBRARY
          </Button>
        )}
      </div>

      {/* Header */}
      <Card className="bg-gradient-to-br from-blue-50 to-indigo-50 border-2" style={{ borderColor: "#0000ee" }}>
        <CardHeader
          className="border-b-2 bg-gradient-to-r from-blue-100 to-indigo-100"
          style={{ borderColor: "#0000ee" }}
        >
          <div className="flex items-center justify-between">
            <div>
              <CardTitle className="font-black" style={{ color: "#0000ee" }}>
                {filename || "Sermon Content"}
              </CardTitle>
            </div>
          </div>
          <div className="flex items-center space-x-2 text-sm font-medium" style={{ color: "#0000ee" }}>
            <span>Generated on {new Date(generatedAt).toLocaleString()}</span>
          </div>
        </CardHeader>
      </Card>

      {/* Content Tabs */}
      {contentTabs.length > 0 ? (
      <div
        className="bg-gradient-to-br from-blue-50 to-indigo-50 p-8 rounded-lg border-2"
        style={{ borderColor: "#0000ee" }}
      >
        <Tabs defaultValue={contentTabs[0]?.id} className="w-full">
          <TabsList
            className={`grid w-full bg-white/70 border max-w-4xl mx-auto ${
              contentTabs.length <= 3 ? 'grid-cols-' + contentTabs.length : 'grid-cols-4'
            }`}
            style={{ borderColor: "#0000ee" }}
          >
            {contentTabs.map((tab) => {
              const Icon = tab.icon
              return (
                <TabsTrigger
                  key={tab.id}
                  value={tab.id}
                  className="flex items-center space-x-2 data-[state=active]:bg-blue-100 text-xs sm:text-sm"
                  style={{
                    color: "#0000ee",
                  }}
                >
                  <Icon className="h-4 w-4" />
                  <span className="hidden sm:inline">{tab.label}</span>
                  <span className="sm:hidden">{tab.label.split(' ')[0]}</span>
                </TabsTrigger>
              )
            })}
          </TabsList>

          {contentTabs.map((tab) => {
            const Icon = tab.icon
            const isCopied = copiedSection === tab.id
            const isQuestionType = tab.label.toLowerCase().includes('question') || tab.label.toLowerCase().includes('discussion')

            return (
              <TabsContent key={tab.id} value={tab.id} className="mt-8">
                <Card className="bg-white/80 border shadow-sm max-w-5xl mx-auto" style={{ borderColor: "#0000ee" }}>
                  <CardHeader className="border-b bg-white/50" style={{ borderColor: "#0000ee" }}>
                    <div className="flex items-center justify-between">
                      <div className="flex items-center space-x-3">
                        <div className={`p-2 rounded-full ${tab.color.split(' ')[0]}`}>
                          <Icon className="h-4 w-4" style={{ color: "#0000ee" }} />
                        </div>
                        <div>
                          <CardTitle className="text-gray-900">{tab.label}</CardTitle>
                          <p className="text-sm text-gray-600 font-medium">{tab.description}</p>
                        </div>
                      </div>
                      <div className="flex items-center space-x-2">
                        <Button
                          variant="outline"
                          size="sm"
                          onClick={() => copyToClipboard(tab.content, tab)}
                          disabled={isCopied}
                          className="text-white hover:bg-blue-50"
                          style={{ borderColor: "#0000ee", color: "#0000ee" }}
                        >
                          {isCopied ? (
                            <CheckCircle2 className="h-4 w-4 mr-2 text-green-500" />
                          ) : (
                            <Copy className="h-4 w-4 mr-2" />
                          )}
                          {isCopied ? "Copied!" : "Copy"}
                        </Button>
                      </div>
                    </div>
                  </CardHeader>
                  <CardContent className="p-8">
                    <div className="prose prose-lg max-w-none">
                      {isQuestionType ? (
                        <ol className="space-y-4">
                          {tab.content
                            .split("\n")
                            .filter((q) => q.trim())
                            .map((question, index) => (
                              <li key={index} className="text-base leading-relaxed text-gray-700">
                                {question.replace(/^\d+\.\s*/, "")}
                              </li>
                            ))}
                        </ol>
                      ) : (
                        <div className="whitespace-pre-wrap text-base leading-relaxed text-gray-700">{tab.content}</div>
                      )}
                    </div>
                  </CardContent>
                </Card>
              </TabsContent>
            )
          })}
        </Tabs>
      </div>
      ) : (
        <Card className="bg-gray-50 border-2 border-gray-200">
          <CardContent className="p-12 text-center">
            <FileText className="h-12 w-12 text-gray-400 mx-auto mb-4" />
            <h3 className="text-lg font-semibold text-gray-700 mb-2">No Content Generated</h3>
            <p className="text-gray-500">Generate content from your transcript to see it here.</p>
          </CardContent>
        </Card>
      )}
    </div>
  )
}
