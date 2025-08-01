"use client"

import { useState, useCallback, useEffect } from "react"
import { useDropzone } from "react-dropzone"
import { Upload, AlertCircle, CheckCircle2 } from "lucide-react"
import { Card, CardContent } from "@/components/ui/card"
import { Button } from "@/components/ui/button"
import { Alert, AlertDescription } from "@/components/ui/alert"
import { uploadSermon } from "@/lib/api"
import type { TranscriptionResponse } from "@/types/api"

interface UploadZoneProps {
  onUploadSuccess: (data: TranscriptionResponse) => void
  onUploadStart: () => void
  onUploadError: (error: string) => void
  transcriptionComplete?: boolean
  onTranscriptionAcknowledged?: () => void
}

const SUPPORTED_FORMATS = [
  "audio/mpeg",
  "audio/wav",
  "audio/mp3",
  "video/mp4",
  "application/pdf",
  "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
]

const SUPPORTED_EXTENSIONS = ["mp3", "wav", "mp4", "pdf", "docx"]

type UploadState = "idle" | "uploading" | "transcribing" | "complete" | "error"

export function UploadZone({ 
  onUploadSuccess, 
  onUploadStart, 
  onUploadError,
  transcriptionComplete,
  onTranscriptionAcknowledged 
}: UploadZoneProps) {
  const [uploadState, setUploadState] = useState<UploadState>("idle")
  const [progress, setProgress] = useState(0)
  const [error, setError] = useState<string | null>(null)
  const [currentFile, setCurrentFile] = useState<string | null>(null)

  // Reset function for when user navigates to Create Content
  const resetUploadState = () => {
    setUploadState("idle")
    setProgress(0)
    setCurrentFile(null)
    onTranscriptionAcknowledged?.()
  }

  // Expose reset function via callback (we'll need to modify the props later)
  useEffect(() => {
    if (uploadState === "complete" && onTranscriptionAcknowledged) {
      // Store the reset function in a way the parent can access it
      (window as any).__uploadZoneReset = resetUploadState
    }
  }, [uploadState, onTranscriptionAcknowledged])

  // Update state when transcription completes
  useEffect(() => {
    if (transcriptionComplete && uploadState === "transcribing") {
      setUploadState("complete")
      // Don't auto-reset anymore - let user click Create Content to reset
    }
  }, [transcriptionComplete, uploadState])

  const onDrop = useCallback(
    async (acceptedFiles: File[]) => {
      const file = acceptedFiles[0]
      if (!file) return

      // Validate file type
      if (
        !SUPPORTED_FORMATS.includes(file.type) &&
        !SUPPORTED_EXTENSIONS.some((ext) => file.name.toLowerCase().endsWith(`.${ext}`))
      ) {
        setError("Unsupported file format. Please upload an audio, video, PDF, or Word document file.")
        return
      }

      // Validate file size (10GB limit)
      if (file.size > 10 * 1024 * 1024 * 1024) {
        setError("File size too large. Please upload a file smaller than 10GB.")
        return
      }

      setError(null)
      setUploadState("uploading")
      setProgress(0)
      setCurrentFile(file.name)
      onUploadStart()

      try {
        const result = await uploadSermon(file, setProgress)

        // Upload complete, now transcribing
        setProgress(100)
        setUploadState("transcribing")
        
        // Start polling for transcription status
        setTimeout(() => {
          onUploadSuccess(result)
          // We'll keep showing transcribing state
          // Dashboard will handle polling and update us when complete
        }, 500)
      } catch (error) {
        setUploadState("error")
        setProgress(0)
        const errorMessage = error instanceof Error ? error.message : "Upload failed"
        setError(errorMessage)
        onUploadError(errorMessage)
      }
    },
    [onUploadSuccess, onUploadStart, onUploadError],
  )

  const { getRootProps, getInputProps, isDragActive } = useDropzone({
    onDrop,
    accept: {
      "audio/*": [".mp3", ".wav"],
      "video/*": [".mp4"],
      "application/pdf": [".pdf"],
      "application/vnd.openxmlformats-officedocument.wordprocessingml.document": [".docx"],
    },
    multiple: false,
    disabled: uploadState === "uploading" || uploadState === "transcribing",
  })

  return (
    <div className="w-full space-y-4">
      <Card className="border-0 rounded-2xl shadow-lg">
        <CardContent className="p-8">
          <div
            {...getRootProps()}
            className={`
              ${uploadState === "idle" ? "border-4 border-dashed" : "border-2 border-solid"} p-8 text-center cursor-pointer transition-colors
              ${isDragActive ? "border-blue-600 bg-blue-50" : "border-gray-400 hover:border-blue-600"}
              ${uploadState === "uploading" || uploadState === "transcribing" ? "cursor-not-allowed opacity-50" : ""}
              ${uploadState === "complete" ? "cursor-default" : ""}
            `}
            style={isDragActive ? { borderColor: "#0000ee", backgroundColor: "#f0f0ff" } : {}}
          >
            <input {...getInputProps()} />

            <div className="flex flex-col items-center space-y-6">
              {uploadState === "uploading" ? (
                <Upload className="h-16 w-16 animate-pulse" style={{ color: "#0000ee" }} />
              ) : uploadState === "transcribing" ? (
                <Upload className="h-16 w-16" style={{ color: "#0000ee" }} />
              ) : uploadState === "complete" ? (
                <CheckCircle2 className="h-16 w-16 text-green-600" />
              ) : (
                <Upload className="h-16 w-16 text-gray-400" />
              )}

              <div className="text-center">
                <h3 className="text-2xl font-black mb-2">
                  {uploadState === "uploading" ? "UPLOADING..." : 
                   uploadState === "transcribing" ? "TRANSCRIBING..." : 
                   uploadState === "complete" ? "TRANSCRIPTION COMPLETE!" : 
                   "UPLOAD SERMON FILE"}
                </h3>
                <p className="text-gray-600 font-medium">
                  {uploadState === "uploading"
                    ? "Hold tight. We're uploading your file - we'll send you an email when it's done."
                    : uploadState === "transcribing"
                      ? "Transcribing your sermon. This usually takes a few moments."
                    : uploadState === "complete"
                      ? "Go to Create Content to generate content using your templates."
                      : isDragActive
                        ? "Drop your file here"
                        : "Drag and drop your audio, video, or document here, or click to browse"}
                </p>
              </div>

              {uploadState === "idle" && (
                <div className="text-center p-4 bg-gray-50 border-2 border-gray-300">
                  <p className="font-bold mb-2">FORMATS:</p>
                  <p className="font-medium mb-2">{SUPPORTED_EXTENSIONS.join(", ").toUpperCase()}</p>
                  <p className="text-sm font-medium text-gray-600">Maximum file size: 10GB</p>
                </div>
              )}

              {uploadState === "uploading" && (
                <div className="w-full max-w-xs space-y-3">
                  <div className="w-full h-3 bg-gray-200 rounded-full overflow-hidden">
                    <div 
                      className="h-full bg-blue-600 transition-all duration-300 ease-out"
                      style={{ width: `${progress}%` }}
                    />
                  </div>
                  <p className="text-sm font-bold text-center">{Math.round(progress)}% COMPLETE</p>
                </div>
              )}

              {uploadState === "idle" && (
                <Button 
                  className="text-lg px-8 py-3 rounded-full hover:scale-[1.02] transition-all duration-200 text-white"
                  style={{ 
                    backgroundColor: "#0000ee"
                  }}
                  onMouseEnter={(e) => (e.currentTarget.style.backgroundColor = "#0000cc")}
                  onMouseLeave={(e) => (e.currentTarget.style.backgroundColor = "#0000ee")}
                >
                  <Upload className="h-5 w-5 mr-2" />
                  CHOOSE FILE
                </Button>
              )}
            </div>
          </div>
        </CardContent>
      </Card>

      {error && (
        <Alert variant="destructive" className="border-2 border-gray-300 bg-red-50">
          <AlertCircle className="h-4 w-4" />
          <AlertDescription className="flex items-center justify-between font-medium">
            <span>{error}</span>
            <Button
              className="bg-orange-500 hover:bg-orange-600 text-white px-4 py-2 rounded-full font-semibold transition-colors ml-4"
              size="sm"
              onClick={() => {
                setError(null)
                setUploadState("idle")
                setProgress(0)
                setCurrentFile(null)
              }}
            >
              TRY AGAIN
            </Button>
          </AlertDescription>
        </Alert>
      )}
    </div>
  )
}
