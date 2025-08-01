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
import { useToast } from "@/hooks/use-toast"
import { zodResolver } from "@hookform/resolvers/zod"
import { useForm } from "react-hook-form"
import * as z from "zod"
import { Loader2, Plus, X } from "lucide-react"

const formSchema = z.object({
  name: z.string().min(1, "Template name is required").max(100),
  examples: z.array(z.string().min(10, "Example must be at least 10 characters"))
    .min(2, "At least 2 examples are required")
    .max(5, "Maximum 5 examples allowed"),
})

type FormData = z.infer<typeof formSchema>

interface TemplateCreateDialogProps {
  open: boolean
  onOpenChange: (open: boolean) => void
  onSuccess: () => void
}

export function TemplateCreateDialog({ open, onOpenChange, onSuccess }: TemplateCreateDialogProps) {
  const apiClient = useApiClient()
  const { toast } = useToast()
  const [loading, setLoading] = useState(false)

  const form = useForm<FormData>({
    resolver: zodResolver(formSchema),
    defaultValues: {
      name: "",
      examples: ["", ""],
    },
  })

  const handleSubmit = async (data: FormData) => {
    try {
      setLoading(true)

      // First, extract patterns from examples
      const patternResponse = await apiClient.extractTemplatePatterns({
        content_type_name: data.name,
        examples: data.examples,
      })

      // Validate before creating template
      console.log("Pattern response:", patternResponse)
      
      if (!patternResponse.structured_prompt || patternResponse.structured_prompt.length < 50) {
        throw new Error("Generated prompt is too short. Please provide more detailed examples.")
      }

      const createData = {
        name: data.name.trim(),
        content_type_name: data.name.trim(),
        structured_prompt: patternResponse.structured_prompt,
        example_content: data.examples.filter(ex => ex.trim().length > 0),
      }

      console.log("Creating template with:", createData)

      // Then create the template with the extracted pattern
      await apiClient.createTemplate(createData)

      toast({
        title: "Template created successfully",
        description: `"${data.name}" is now available for content generation.`,
      })

      onOpenChange(false)
      onSuccess()
      form.reset()
    } catch (error) {
      let errorMessage = "Please try again"
      let errorTitle = "Failed to create template"
      
      console.error("Template creation error:", error)
      
      if (error instanceof Error) {
        if (error.message.includes("confidence too low")) {
          errorTitle = "Examples need more consistency"
          errorMessage = "The AI couldn't find clear patterns in your examples. Try making them more similar in structure, length, and style, or add 1-2 more examples."
        } else if (error.message.includes("422") || error.message.includes("validation")) {
          errorTitle = "Invalid template data"
          errorMessage = "Please check that your template name is 2-100 characters and examples are detailed enough."
        } else {
          errorMessage = error.message
        }
      }
      
      toast({
        title: errorTitle,
        description: errorMessage,
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
          <DialogTitle>Create Content Template</DialogTitle>
          <DialogDescription>
            Create a custom template by providing examples of the content you want to generate.
            Churchable's AI will learn the formatting, style and tone of voice from your examples.
          </DialogDescription>
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
                    <Input
                      placeholder="e.g., Youth Group Discussion Guide"
                      {...field}
                    />
                  </FormControl>
                  <FormMessage />
                </FormItem>
              )}
            />

            <div className="space-y-4">
              <div className="flex items-center justify-between">
                <div>
                  <FormLabel>Content Examples</FormLabel>
                  <p className="text-sm text-muted-foreground mt-1">
                    Provide 2-5 examples of this content type. For better results, try to use examples which are similar in structure and format.
                  </p>
                </div>
                {form.watch("examples").length < 5 && (
                  <Button
                    type="button"
                    variant="outline"
                    size="sm"
                    onClick={addExample}
                    className="rounded-xl"
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
                            className="mt-6 rounded-xl"
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
                className="rounded-xl"
              >
                Cancel
              </Button>
              <Button type="submit" disabled={loading} className="rounded-xl">
                {loading ? (
                  <>
                    <Loader2 className="mr-2 h-4 w-4 animate-spin" />
                    Creating Template...
                  </>
                ) : (
                  "Create Template"
                )}
              </Button>
            </DialogFooter>
          </form>
        </Form>
      </DialogContent>
    </Dialog>
  )
}