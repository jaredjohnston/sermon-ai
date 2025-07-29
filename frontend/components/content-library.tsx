"use client"

import { useState } from "react"
import { Card, CardContent } from "@/components/ui/card"
import { Button } from "@/components/ui/button"
import { Badge } from "@/components/ui/badge"
import { Input } from "@/components/ui/input"
import { DropdownMenu, DropdownMenuContent, DropdownMenuItem, DropdownMenuTrigger } from "@/components/ui/dropdown-menu"
import {
  FileText,
  Search,
  Filter,
  MoreHorizontal,
  Eye,
  Download,
  Trash2,
  CheckCircle2,
  Clock,
  AlertCircle,
  Calendar,
  Edit3,
  Sparkles,
} from "lucide-react"
import type { ContentSource } from "@/types/api"

interface ContentLibraryProps {
  contents: ContentSource[]
  onContentSelect: (content: ContentSource) => void
  onContentDelete: (contentId: string) => void
  onTranscriptEdit: (content: ContentSource) => void
  onContentEdit: (content: ContentSource) => void
}

const STATUS_CONFIG = {
  completed: {
    icon: CheckCircle2,
    color: "bg-green-100 text-green-800",
    label: "Ready",
  },
  uploading: {
    icon: Clock,
    color: "bg-blue-100 text-blue-800",
    label: "Uploading",
  },
  transcribing: {
    icon: Clock,
    color: "bg-orange-100 text-orange-800",
    label: "Transcribing",
  },
  generating: {
    icon: Clock,
    color: "bg-purple-100 text-purple-800",
    label: "Generating",
  },
  error: {
    icon: AlertCircle,
    color: "bg-red-100 text-red-800",
    label: "Error",
  },
  idle: {
    icon: Clock,
    color: "bg-gray-100 text-gray-800",
    label: "Idle",
  },
}

export function ContentLibrary({
  contents,
  onContentSelect,
  onContentDelete,
  onTranscriptEdit,
  onContentEdit,
}: ContentLibraryProps) {
  const [searchTerm, setSearchTerm] = useState("")
  const [statusFilter, setStatusFilter] = useState<string>("all")

  const filteredContents = contents.filter((content) => {
    const matchesSearch = content.filename.toLowerCase().includes(searchTerm.toLowerCase())
    const matchesStatus = statusFilter === "all" || content.status === statusFilter
    return matchesSearch && matchesStatus
  })

  const formatDate = (dateString: string) => {
    return new Date(dateString).toLocaleDateString("en-US", {
      year: "numeric",
      month: "short",
      day: "numeric",
    })
  }

  return (
    <div className="space-y-6">
      {/* Header */}
      <div>
        <h1 className="text-3xl font-black text-warm-gray-900">CREATE CONTENT</h1>
        <p className="text-warm-gray-600 font-medium">Create and manage content from sermon uploads</p>
      </div>

      {/* Filters */}
      <Card>
        <CardContent className="p-4">
          <div className="flex flex-col sm:flex-row gap-4">
            <div className="relative flex-1">
              <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 h-4 w-4 text-muted-foreground" />
              <Input
                placeholder="Search sermons..."
                value={searchTerm}
                onChange={(e) => setSearchTerm(e.target.value)}
                className="pl-10"
              />
            </div>
            <DropdownMenu>
              <DropdownMenuTrigger asChild>
                <Button variant="outline" className="flex items-center gap-2 bg-transparent">
                  <Filter className="h-4 w-4" />
                  Status:{" "}
                  {statusFilter === "all" ? "All" : STATUS_CONFIG[statusFilter as keyof typeof STATUS_CONFIG]?.label}
                </Button>
              </DropdownMenuTrigger>
              <DropdownMenuContent align="end">
                <DropdownMenuItem onClick={() => setStatusFilter("all")}>All Statuses</DropdownMenuItem>
                {Object.entries(STATUS_CONFIG).map(([status, config]) => (
                  <DropdownMenuItem key={status} onClick={() => setStatusFilter(status)}>
                    <config.icon className="h-4 w-4 mr-2" />
                    {config.label}
                  </DropdownMenuItem>
                ))}
              </DropdownMenuContent>
            </DropdownMenu>
          </div>
        </CardContent>
      </Card>

      {/* Sermons List */}
      {filteredContents.length === 0 ? (
        <Card>
          <CardContent className="p-12 text-center">
            <FileText className="h-12 w-12 text-muted-foreground mx-auto mb-4" />
            <h3 className="text-lg font-black mb-2 text-warm-gray-900">NO CONTENT FOUND</h3>
            <p className="text-warm-gray-600 font-medium">
              {searchTerm || statusFilter !== "all"
                ? "Try adjusting your search or filter criteria"
                : "Create your first content to get started"}
            </p>
          </CardContent>
        </Card>
      ) : (
        <div className="space-y-4">
          {filteredContents.map((content) => {
            const statusConfig = STATUS_CONFIG[content.status]
            const StatusIcon = statusConfig.icon
            const hasContent = Boolean(content.content)
            const isTranscribing = content.status === 'transcribing'
            const isReady = content.status === 'completed' && !hasContent
            const isNew = new Date(content.uploadedAt).getTime() > Date.now() - 24 * 60 * 60 * 1000 // Within 24 hours

            return (
              <Card key={content.id} className={`hover:shadow-md transition-shadow ${isNew ? 'ring-2 ring-primary/50' : ''}`}>
                <CardContent className="p-6">
                  <div className="flex flex-col md:flex-row md:items-center justify-between gap-4">
                    <div className="flex items-center flex-1 min-w-0">
                      <div className="flex-1 min-w-0">
                        <h3 className="font-semibold truncate">{content.filename}</h3>
                        <div className="flex items-center space-x-4 text-sm text-muted-foreground mt-1">
                          <div className="flex items-center space-x-1">
                            <Calendar className="h-3 w-3" />
                            <span>{formatDate(content.uploadedAt)}</span>
                          </div>
                          <Badge className={statusConfig.color}>
                            <StatusIcon className={`h-3 w-3 mr-1 ${isTranscribing ? 'animate-spin' : ''}`} />
                            {isTranscribing ? 'Transcribing...' : isReady ? 'Ready' : statusConfig.label}
                          </Badge>
                          {isNew && (
                            <Badge className="bg-blue-100 text-blue-800">
                              <span className="font-semibold">NEW</span>
                            </Badge>
                          )}
                        </div>
                      </div>
                    </div>

                    <div className="flex items-center space-x-3">
                      {/* Dynamic action buttons based on sermon state */}
                      <Button
                        variant="outline"
                        size="sm"
                        onClick={() => onTranscriptEdit(content)}
                        className="whitespace-nowrap"
                        disabled={isTranscribing}
                      >
                        <Edit3 className="h-4 w-4 mr-2" />
                        {isTranscribing ? 'Transcribing...' : 'Edit Transcript'}
                      </Button>

                      {hasContent ? (
                        <Button
                          className="zorp-button whitespace-nowrap"
                          size="sm"
                          onClick={() => onContentEdit(content)}
                        >
                          <Sparkles className="h-4 w-4 mr-2" />
                          Review Content
                        </Button>
                      ) : (
                        <Button 
                          variant="outline" 
                          size="sm" 
                          disabled={isTranscribing}
                          className="whitespace-nowrap bg-transparent"
                          onClick={() => !isTranscribing && onTranscriptEdit(content)}
                        >
                          <Sparkles className="h-4 w-4 mr-2" />
                          {isTranscribing ? 'Transcribing...' : 'Generate Content'}
                        </Button>
                      )}

                      <DropdownMenu>
                        <DropdownMenuTrigger asChild>
                          <Button variant="ghost" size="sm">
                            <MoreHorizontal className="h-4 w-4" />
                          </Button>
                        </DropdownMenuTrigger>
                        <DropdownMenuContent align="end">
                          <DropdownMenuItem onClick={() => onContentSelect(content)}>
                            <Eye className="h-4 w-4 mr-2" />
                            View Details
                          </DropdownMenuItem>
                          {hasContent && (
                            <DropdownMenuItem>
                              <Download className="h-4 w-4 mr-2" />
                              Export Content
                            </DropdownMenuItem>
                          )}
                          <DropdownMenuItem onClick={() => onContentDelete(content.id)} className="text-red-600">
                            <Trash2 className="h-4 w-4 mr-2" />
                            Delete
                          </DropdownMenuItem>
                        </DropdownMenuContent>
                      </DropdownMenu>
                    </div>
                  </div>
                </CardContent>
              </Card>
            )
          })}
        </div>
      )}
    </div>
  )
}
