"use client"

import { useState, useCallback } from "react"
import { useDropzone } from "react-dropzone"
import { Upload, AlertCircle, CheckCircle2 } from "lucide-react"
import { Card, CardContent } from "@/components/ui/card"
import { Button } from "@/components/ui/button"
import { Progress } from "@/components/ui/progress"
import { Alert, AlertDescription } from "@/components/ui/alert"
import { uploadSermon } from "@/lib/api"
import type { TranscriptionResponse } from "@/types/api"

interface UploadZoneProps {
  onUploadSuccess: (data: TranscriptionResponse) => void
  onUploadStart: () => void
  onUploadError: (error: string) => void
}

const SUPPORTED_FORMATS = [
  "audio/mpeg",
  "audio/wav",
  "audio/mp3",
  "audio/m4a",
  "video/mp4",
  "video/avi",
  "video/mov",
  "video/wmv",
]

const SUPPORTED_EXTENSIONS = ["mp3", "wav", "m4a", "mp4", "avi", "mov", "wmv"]

export function UploadZone({ onUploadSuccess, onUploadStart, onUploadError }: UploadZoneProps) {
  const [uploading, setUploading] = useState(false)
  const [progress, setProgress] = useState(0)
  const [error, setError] = useState<string | null>(null)
  const [success, setSuccess] = useState(false)

  const onDrop = useCallback(
    async (acceptedFiles: File[]) => {
      const file = acceptedFiles[0]
      if (!file) return

      // Validate file type
      if (
        !SUPPORTED_FORMATS.includes(file.type) &&
        !SUPPORTED_EXTENSIONS.some((ext) => file.name.toLowerCase().endsWith(`.${ext}`))
      ) {
        setError("Unsupported file format. Please upload an audio or video file.")
        return
      }

      // Validate file size (100MB limit)
      if (file.size > 100 * 1024 * 1024) {
        setError("File size too large. Please upload a file smaller than 100MB.")
        return
      }

      setError(null)
      setSuccess(false)
      setUploading(true)
      setProgress(0)
      onUploadStart()

      try {
        // Simulate progress for better UX
        const progressInterval = setInterval(() => {
          setProgress((prev) => {
            if (prev >= 90) {
              clearInterval(progressInterval)
              return 90
            }
            return prev + Math.random() * 10
          })
        }, 500)

        const result = await uploadSermon(file)

        clearInterval(progressInterval)
        setProgress(100)
        setSuccess(true)
        setUploading(false)

        setTimeout(() => {
          onUploadSuccess(result)
        }, 1000)
      } catch (error) {
        setUploading(false)
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
      "audio/*": [".mp3", ".wav", ".m4a"],
      "video/*": [".mp4", ".avi", ".mov", ".wmv"],
    },
    multiple: false,
    disabled: uploading,
  })

  return (
    <div className="w-full max-w-2xl mx-auto space-y-4">
      <Card className="zorp-card">
        <CardContent className="p-8">
          <div
            {...getRootProps()}
            className={`
              border-4 border-dashed p-8 text-center cursor-pointer transition-colors
              ${isDragActive ? "border-blue-600 bg-blue-50" : "border-gray-400 hover:border-blue-600"}
              ${uploading ? "cursor-not-allowed opacity-50" : ""}
            `}
            style={isDragActive ? { borderColor: "#0000ee", backgroundColor: "#f0f0ff" } : {}}
          >
            <input {...getInputProps()} />

            <div className="flex flex-col items-center space-y-6">
              {uploading ? (
                <Upload className="h-16 w-16 animate-pulse" style={{ color: "#0000ee" }} />
              ) : success ? (
                <CheckCircle2 className="h-16 w-16 text-green-600" />
              ) : (
                <Upload className="h-16 w-16 text-gray-400" />
              )}

              <div className="text-center">
                <h3 className="text-2xl font-black mb-2">
                  {uploading ? "UPLOADING..." : success ? "UPLOAD COMPLETE!" : "UPLOAD SERMON FILE"}
                </h3>
                <p className="text-gray-600 font-medium">
                  {uploading
                    ? "Please wait while we process your file"
                    : success
                      ? "Your sermon has been uploaded successfully"
                      : isDragActive
                        ? "Drop your file here"
                        : "Drag and drop your audio or video file here, or click to browse"}
                </p>
              </div>

              {!uploading && !success && (
                <div className="text-center p-4 bg-gray-50 zorp-border">
                  <p className="font-bold mb-2">SUPPORTED FORMATS:</p>
                  <p className="font-medium mb-2">{SUPPORTED_EXTENSIONS.join(", ").toUpperCase()}</p>
                  <p className="text-sm font-medium text-gray-600">Maximum file size: 100MB</p>
                </div>
              )}

              {uploading && (
                <div className="w-full max-w-xs space-y-3">
                  <Progress value={progress} className="w-full h-3" />
                  <p className="text-sm font-bold text-center">{Math.round(progress)}% COMPLETE</p>
                </div>
              )}

              {!uploading && !success && (
                <Button className="zorp-button text-lg px-8 py-3">
                  <Upload className="h-5 w-5 mr-2" />
                  CHOOSE FILE
                </Button>
              )}
            </div>
          </div>
        </CardContent>
      </Card>

      {error && (
        <Alert variant="destructive" className="zorp-border bg-red-50">
          <AlertCircle className="h-4 w-4" />
          <AlertDescription className="flex items-center justify-between font-medium">
            <span>{error}</span>
            <Button
              className="zorp-button-orange ml-4"
              size="sm"
              onClick={() => {
                setError(null)
                setSuccess(false)
                setProgress(0)
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
