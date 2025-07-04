"use client"

import { useState } from "react"
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card"
import { Button } from "@/components/ui/button"
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs"
import { Copy, FileText, Heart, MessageCircle, CheckCircle2, ArrowLeft } from "lucide-react"
import type { ContentResponse } from "@/types/api"
import { useToast } from "@/hooks/use-toast"

interface GeneratedContentProps {
  content: ContentResponse["content"]
  generatedAt: string
  filename?: string
  onBack?: () => void
}

const CONTENT_TYPES = {
  summary: {
    label: "Summary",
    icon: FileText,
    description: "Key points and main themes",
    color: "bg-blue-100 text-blue-800",
  },
  devotional: {
    label: "Devotional",
    icon: Heart,
    description: "Personal reflection and application",
    color: "bg-blue-100 text-blue-800",
  },
  discussion_questions: {
    label: "Discussion",
    icon: MessageCircle,
    description: "Questions for group study",
    color: "bg-blue-100 text-blue-800",
  },
}

export function GeneratedContent({ content, generatedAt, filename, onBack }: GeneratedContentProps) {
  const [copiedSection, setCopiedSection] = useState<string | null>(null)
  const { toast } = useToast()

  const copyToClipboard = async (text: string, section: string) => {
    try {
      await navigator.clipboard.writeText(text)
      setCopiedSection(section)
      toast({
        title: "Copied to clipboard",
        description: `${CONTENT_TYPES[section as keyof typeof CONTENT_TYPES]?.label} copied successfully`,
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
      <div
        className="bg-gradient-to-br from-blue-50 to-indigo-50 p-8 rounded-lg border-2"
        style={{ borderColor: "#0000ee" }}
      >
        <Tabs defaultValue="summary" className="w-full">
          <TabsList
            className="grid w-full grid-cols-3 bg-white/70 border max-w-2xl mx-auto"
            style={{ borderColor: "#0000ee" }}
          >
            {Object.entries(CONTENT_TYPES).map(([key, config]) => {
              const Icon = config.icon
              return (
                <TabsTrigger
                  key={key}
                  value={key}
                  className="flex items-center space-x-2 data-[state=active]:bg-blue-100"
                  style={{
                    color: "#0000ee",
                  }}
                >
                  <Icon className="h-4 w-4" />
                  <span>{config.label}</span>
                </TabsTrigger>
              )
            })}
          </TabsList>

          {Object.entries(CONTENT_TYPES).map(([key, config]) => {
            const Icon = config.icon
            const contentText = content[key as keyof typeof content]
            const isCopied = copiedSection === key

            return (
              <TabsContent key={key} value={key} className="mt-8">
                <Card className="bg-white/80 border shadow-sm max-w-5xl mx-auto" style={{ borderColor: "#0000ee" }}>
                  <CardHeader className="border-b bg-white/50" style={{ borderColor: "#0000ee" }}>
                    <div className="flex items-center justify-between">
                      <div className="flex items-center space-x-3">
                        <div
                          className={`p-2 rounded-full ${
                            key === "summary" ? "bg-blue-100" : key === "devotional" ? "bg-blue-100" : "bg-green-100"
                          }`}
                        >
                          <Icon className={`h-4 w-4 text-blue-600`} style={{ color: "#0000ee" }} />
                        </div>
                        <div>
                          <CardTitle className="text-gray-900">{config.label}</CardTitle>
                          <p className="text-sm text-gray-600 font-medium">{config.description}</p>
                        </div>
                      </div>
                      <div className="flex items-center space-x-2">
                        <Button
                          variant="outline"
                          size="sm"
                          onClick={() => copyToClipboard(contentText, key)}
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
                      {key === "discussion_questions" ? (
                        <ol className="space-y-4">
                          {contentText
                            .split("\n")
                            .filter((q) => q.trim())
                            .map((question, index) => (
                              <li key={index} className="text-base leading-relaxed text-gray-700">
                                {question.replace(/^\d+\.\s*/, "")}
                              </li>
                            ))}
                        </ol>
                      ) : (
                        <div className="whitespace-pre-wrap text-base leading-relaxed text-gray-700">{contentText}</div>
                      )}
                    </div>
                  </CardContent>
                </Card>
              </TabsContent>
            )
          })}
        </Tabs>
      </div>
    </div>
  )
}
