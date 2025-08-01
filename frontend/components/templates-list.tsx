"use client"

import { useState, useEffect } from "react"
import { useApiClient } from "@/lib/api-client"
import { Button } from "@/components/ui/button"
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card"
import { Badge } from "@/components/ui/badge"
import { Plus, BookOpen, Edit, Trash2, Archive, RotateCcw } from "lucide-react"
import { useToast } from "@/hooks/use-toast"
import { ContentTemplatePublic } from "@/types/api"
import { TemplateCreateDialog } from "./template-create-dialog"
import { TemplateEditDialog } from "./template-edit-dialog"
import {
  AlertDialog,
  AlertDialogAction,
  AlertDialogCancel,
  AlertDialogContent,
  AlertDialogDescription,
  AlertDialogFooter,
  AlertDialogHeader,
  AlertDialogTitle,
} from "@/components/ui/alert-dialog"

export function TemplatesList() {
  const apiClient = useApiClient()
  const { toast } = useToast()
  const [templates, setTemplates] = useState<ContentTemplatePublic[]>([])
  const [loading, setLoading] = useState(true)
  const [createDialogOpen, setCreateDialogOpen] = useState(false)
  const [editingTemplate, setEditingTemplate] = useState<ContentTemplatePublic | null>(null)
  const [deletingTemplate, setDeletingTemplate] = useState<ContentTemplatePublic | null>(null)

  // Load templates on mount
  useEffect(() => {
    loadTemplates()
  }, [])

  const loadTemplates = async () => {
    try {
      setLoading(true)
      const data = await apiClient.listContentTemplates()
      setTemplates(data)
    } catch (error) {
      toast({
        title: "Failed to load templates",
        description: error instanceof Error ? error.message : "Please try again",
        variant: "destructive",
      })
    } finally {
      setLoading(false)
    }
  }

  const handleDelete = async () => {
    if (!deletingTemplate) return

    try {
      await apiClient.deleteTemplate(deletingTemplate.id)
      toast({
        title: "Template deleted",
        description: `"${deletingTemplate.name}" has been deleted.`,
      })
      loadTemplates()
    } catch (error) {
      toast({
        title: "Failed to delete template",
        description: error instanceof Error ? error.message : "Please try again",
        variant: "destructive",
      })
    } finally {
      setDeletingTemplate(null)
    }
  }

  const handleArchive = async (template: ContentTemplatePublic) => {
    try {
      await apiClient.updateTemplate(template.id, {
        status: template.status === "archived" ? "active" : "archived",
      })
      toast({
        title: template.status === "archived" ? "Template restored" : "Template archived",
        description: `"${template.name}" has been ${template.status === "archived" ? "restored" : "archived"}.`,
      })
      loadTemplates()
    } catch (error) {
      toast({
        title: "Failed to update template",
        description: error instanceof Error ? error.message : "Please try again",
        variant: "destructive",
      })
    }
  }

  const activeTemplates = templates.filter(t => t.status === "active")
  const archivedTemplates = templates.filter(t => t.status === "archived")

  if (loading) {
    return (
      <div className="flex items-center justify-center py-12">
        <div className="text-center">
          <BookOpen className="h-12 w-12 text-muted-foreground mx-auto mb-4 animate-pulse" />
          <p className="text-muted-foreground">Loading templates...</p>
        </div>
      </div>
    )
  }

  return (
    <div className="space-y-8">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-3xl font-black text-warm-gray-900">CONTENT TEMPLATES</h1>
          <p className="text-warm-gray-600 font-medium">
            Create custom templates by providing examples of your desired content
          </p>
        </div>
        <Button onClick={() => setCreateDialogOpen(true)} className="gap-2 rounded-xl">
          <Plus className="h-4 w-4" />
          Create Template
        </Button>
      </div>

      {/* Active Templates */}
      <div className="space-y-4">
        <h2 className="text-lg font-semibold text-warm-gray-900">Active Templates</h2>
        {activeTemplates.length === 0 ? (
          <Card className="border-dashed">
            <CardContent className="flex flex-col items-center justify-center py-12">
              <BookOpen className="h-12 w-12 text-muted-foreground mb-4" />
              <h3 className="text-lg font-semibold mb-2">No templates yet</h3>
              <p className="text-muted-foreground text-center mb-4 max-w-md">
                Create your first template by providing examples of the content you want to generate
              </p>
              <Button onClick={() => setCreateDialogOpen(true)} variant="outline" className="gap-2 rounded-xl">
                <Plus className="h-4 w-4" />
                Create Your First Template
              </Button>
            </CardContent>
          </Card>
        ) : (
          <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-3">
            {activeTemplates.map((template) => (
              <Card key={template.id} className="relative border-0 shadow-lg hover:shadow-xl transition-shadow transform transition-all duration-200 hover:-translate-y-0.5">
                <CardHeader>
                  <div className="flex items-start justify-between">
                    <div className="space-y-1">
                      <CardTitle className="text-lg">{template.name}</CardTitle>
                      <CardDescription>
                        Created by: {template.creator_name || "Unknown"}
                      </CardDescription>
                    </div>
                    <Badge variant="secondary">Active</Badge>
                  </div>
                </CardHeader>
                <CardContent>
                  <div className="flex gap-2">
                    <Button
                      variant="outline"
                      size="sm"
                      onClick={() => setEditingTemplate(template)}
                      className="flex-1 rounded-xl"
                    >
                      <Edit className="h-4 w-4 mr-1" />
                      Edit
                    </Button>
                    <Button
                      variant="outline"
                      size="sm"
                      onClick={() => handleArchive(template)}
                      className="flex-1 rounded-xl"
                    >
                      <Archive className="h-4 w-4 mr-1" />
                      Archive
                    </Button>
                    <Button
                      variant="outline"
                      size="sm"
                      onClick={() => setDeletingTemplate(template)}
                      className="text-destructive hover:text-destructive rounded-xl"
                    >
                      <Trash2 className="h-4 w-4" />
                    </Button>
                  </div>
                </CardContent>
              </Card>
            ))}
          </div>
        )}
      </div>

      {/* Archived Templates */}
      {archivedTemplates.length > 0 && (
        <div className="space-y-4">
          <h2 className="text-lg font-semibold text-warm-gray-900">Archived Templates</h2>
          <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-3 opacity-60">
            {archivedTemplates.map((template) => (
              <Card key={template.id} className="relative border-0 shadow-lg hover:shadow-xl transition-shadow transform transition-all duration-200 hover:-translate-y-0.5">
                <CardHeader>
                  <div className="flex items-start justify-between">
                    <div className="space-y-1">
                      <CardTitle className="text-lg">{template.name}</CardTitle>
                      <CardDescription>
                        Created by: {template.creator_name || "Unknown"}
                      </CardDescription>
                    </div>
                    <Badge variant="outline">Archived</Badge>
                  </div>
                </CardHeader>
                <CardContent>
                  <div className="flex gap-2">
                    <Button
                      variant="outline"
                      size="sm"
                      onClick={() => handleArchive(template)}
                      className="flex-1 rounded-xl"
                    >
                      <RotateCcw className="h-4 w-4 mr-1" />
                      Restore
                    </Button>
                    <Button
                      variant="outline"
                      size="sm"
                      onClick={() => setDeletingTemplate(template)}
                      className="text-destructive hover:text-destructive rounded-xl"
                    >
                      <Trash2 className="h-4 w-4" />
                    </Button>
                  </div>
                </CardContent>
              </Card>
            ))}
          </div>
        </div>
      )}

      {/* Create Dialog */}
      <TemplateCreateDialog
        open={createDialogOpen}
        onOpenChange={setCreateDialogOpen}
        onSuccess={loadTemplates}
      />

      {/* Edit Dialog */}
      {editingTemplate && (
        <TemplateEditDialog
          template={editingTemplate}
          open={!!editingTemplate}
          onOpenChange={(open) => !open && setEditingTemplate(null)}
          onSuccess={loadTemplates}
        />
      )}

      {/* Delete Confirmation */}
      <AlertDialog open={!!deletingTemplate} onOpenChange={(open) => !open && setDeletingTemplate(null)}>
        <AlertDialogContent>
          <AlertDialogHeader>
            <AlertDialogTitle>Delete Template</AlertDialogTitle>
            <AlertDialogDescription>
              Are you sure you want to delete "{deletingTemplate?.name}"? This action cannot be undone.
            </AlertDialogDescription>
          </AlertDialogHeader>
          <AlertDialogFooter>
            <AlertDialogCancel>Cancel</AlertDialogCancel>
            <AlertDialogAction onClick={handleDelete} className="bg-destructive text-destructive-foreground hover:bg-destructive/90">
              Delete
            </AlertDialogAction>
          </AlertDialogFooter>
        </AlertDialogContent>
      </AlertDialog>
    </div>
  )
}