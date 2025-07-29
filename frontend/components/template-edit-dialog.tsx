"use client"

import { useState } from "react"
import { useApiClient } from "@/lib/api-client"
import { Button } from "@/components/ui/button"
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogFooter,
  DialogHeader,
  DialogTitle,
} from "@/components/ui/dialog"
import {
  Form,
  FormControl,
  FormDescription,
  FormField,
  FormItem,
  FormLabel,
  FormMessage,
} from "@/components/ui/form"
import { Input } from "@/components/ui/input"
import { Textarea } from "@/components/ui/textarea"
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select"
import { useToast } from "@/hooks/use-toast"
import { zodResolver } from "@hookform/resolvers/zod"
import { useForm } from "react-hook-form"
import * as z from "zod"
import { Loader2, Plus, X } from "lucide-react"
import { ContentTemplatePublic } from "@/types/api"

const formSchema = z.object({
  name: z.string().min(1, "Template name is required").max(100),
  status: z.enum(["active", "archived"]),
  examples: z.array(z.string().min(10, "Example must be at least 10 characters"))
    .min(2, "At least 2 examples are required")
    .max(5, "Maximum 5 examples allowed"),
})

type FormData = z.infer<typeof formSchema>

interface TemplateEditDialogProps {
  template: ContentTemplatePublic
  open: boolean
  onOpenChange: (open: boolean) => void
  onSuccess: () => void
}

export function TemplateEditDialog({ template, open, onOpenChange, onSuccess }: TemplateEditDialogProps) {
  const apiClient = useApiClient()
  const { toast } = useToast()
  const [loading, setLoading] = useState(false)

  const form = useForm<FormData>({
    resolver: zodResolver(formSchema),
    defaultValues: {
      name: template.name,
      status: template.status,
      examples: template.example_content || ["", ""],
    },
  })

  const handleSubmit = async (data: FormData) => {
    try {
      setLoading(true)

      await apiClient.updateTemplate(template.id, {
        name: data.name,
        status: data.status,
        example_content: data.examples.filter(ex => ex.trim().length > 0),
      })

      toast({
        title: "Template updated",
        description: `"${data.name}" has been updated successfully.`,
      })

      onOpenChange(false)
      onSuccess()
    } catch (error) {
      toast({
        title: "Failed to update template",
        description: error instanceof Error ? error.message : "Please try again",
        variant: "destructive",
      })
    } finally {
      setLoading(false)
    }
  }

  const addExample = () => {
    const currentExamples = form.getValues("examples")
    if (currentExamples.length < 5) {
      form.setValue("examples", [...currentExamples, ""])
    }
  }

  const removeExample = (index: number) => {
    const currentExamples = form.getValues("examples")
    if (currentExamples.length > 2) {
      form.setValue("examples", currentExamples.filter((_, i) => i !== index))
    }
  }

  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      <DialogContent className="max-w-3xl max-h-[90vh] overflow-y-auto">
        <DialogHeader>
          <DialogTitle>Edit Template</DialogTitle>
          <div className="text-xs text-muted-foreground mt-2">
            Last updated: {new Date(template.updated_at).toLocaleDateString()}
          </div>
        </DialogHeader>

        <Form {...form}>
          <form onSubmit={form.handleSubmit(handleSubmit)} className="space-y-6">
            <FormField
              control={form.control}
              name="name"
              render={({ field }) => (
                <FormItem>
                  <FormLabel>Template Name</FormLabel>
                  <FormControl>
                    <Input {...field} />
                  </FormControl>
                  <FormMessage />
                </FormItem>
              )}
            />

            <FormField
              control={form.control}
              name="status"
              render={({ field }) => (
                <FormItem>
                  <FormLabel>Status</FormLabel>
                  <FormDescription>
                    Archived templates won't appear in content generation options
                  </FormDescription>
                  <Select onValueChange={field.onChange} defaultValue={field.value}>
                    <FormControl>
                      <SelectTrigger>
                        <SelectValue />
                      </SelectTrigger>
                    </FormControl>
                    <SelectContent>
                      <SelectItem value="active">Active</SelectItem>
                      <SelectItem value="archived">Archived</SelectItem>
                    </SelectContent>
                  </Select>
                  <FormMessage />
                </FormItem>
              )}
            />

            <div className="space-y-4">
              <div className="flex items-center justify-between">
                <div>
                  <FormLabel>Content Examples</FormLabel>
                  <p className="text-sm text-muted-foreground mt-1">
                    Update or add examples to improve quality. Remember: Your examples should be similar in structure and style.
                  </p>
                </div>
                {form.watch("examples").length < 5 && (
                  <Button
                    type="button"
                    variant="outline"
                    size="sm"
                    onClick={addExample}
                  >
                    <Plus className="h-4 w-4 mr-1" />
                    Add Example
                  </Button>
                )}
              </div>

              {form.watch("examples").map((_, index) => (
                <FormField
                  key={index}
                  control={form.control}
                  name={`examples.${index}`}
                  render={({ field }) => (
                    <FormItem>
                      <div className="flex items-start gap-2">
                        <div className="flex-1">
                          <FormLabel>Example {index + 1}</FormLabel>
                          <FormControl>
                            <Textarea
                              placeholder="Paste or type an example of this content type..."
                              rows={6}
                              {...field}
                            />
                          </FormControl>
                          <FormMessage />
                        </div>
                        {form.watch("examples").length > 2 && (
                          <Button
                            type="button"
                            variant="ghost"
                            size="icon"
                            onClick={() => removeExample(index)}
                            className="mt-6"
                          >
                            <X className="h-4 w-4" />
                          </Button>
                        )}
                      </div>
                    </FormItem>
                  )}
                />
              ))}
            </div>

            <DialogFooter>
              <Button
                type="button"
                variant="outline"
                onClick={() => onOpenChange(false)}
                disabled={loading}
              >
                Cancel
              </Button>
              <Button type="submit" disabled={loading}>
                {loading ? (
                  <>
                    <Loader2 className="mr-2 h-4 w-4 animate-spin" />
                    Updating...
                  </>
                ) : (
                  "Save Changes"
                )}
              </Button>
            </DialogFooter>
          </form>
        </Form>
      </DialogContent>
    </Dialog>
  )
}