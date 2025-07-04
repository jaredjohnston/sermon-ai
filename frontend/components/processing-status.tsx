"use client"

import { useState, useEffect } from "react"
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card"
import { Button } from "@/components/ui/button"
import { Progress } from "@/components/ui/progress"
import { Alert, AlertDescription } from "@/components/ui/alert"
import { Upload, FileText, Sparkles, CheckCircle2, AlertCircle, X, RotateCcw } from "lucide-react"
import type { ProcessingStage } from "@/types/api"

interface ProcessingStatusProps {
  stage: ProcessingStage
  progress?: number
  filename?: string
  error?: string
  onCancel?: () => void
  onRetry?: () => void
}

const STAGE_CONFIG = {
  idle: {
    icon: Upload,
    title: "READY TO UPLOAD",
    description: "Select a sermon file to begin processing",
    progress: 0,
  },
  uploading: {
    icon: Upload,
    title: "UPLOADING FILE",
    description: "Transferring your sermon file to our servers",
    progress: 25,
  },
  transcribing: {
    icon: FileText,
    title: "TRANSCRIBING AUDIO",
    description: "Converting speech to text using AI technology",
    progress: 60,
  },
  generating: {
    icon: Sparkles,
    title: "GENERATING CONTENT",
    description: "Creating summary, devotional, and discussion questions",
    progress: 90,
  },
  completed: {
    icon: CheckCircle2,
    title: "PROCESSING COMPLETE",
    description: "Your sermon content is ready to view",
    progress: 100,
  },
  error: {
    icon: AlertCircle,
    title: "PROCESSING FAILED",
    description: "An error occurred during processing",
    progress: 0,
  },
}

export function ProcessingStatus({ stage, progress, filename, error, onCancel, onRetry }: ProcessingStatusProps) {
  const [animatedProgress, setAnimatedProgress] = useState(0)
  const config = STAGE_CONFIG[stage]
  const Icon = config.icon
  const currentProgress = progress ?? config.progress

  useEffect(() => {
    const timer = setTimeout(() => {
      setAnimatedProgress(currentProgress)
    }, 100)
    return () => clearTimeout(timer)
  }, [currentProgress])

  const isProcessing = ["uploading", "transcribing", "generating"].includes(stage)
  const showActions = stage === "error" || (isProcessing && onCancel)

  return (
    <div className="w-full max-w-2xl mx-auto">
      <Card className="zorp-card">
        <CardHeader className="border-b-2 border-black bg-gray-50">
          <CardTitle className="flex items-center space-x-3">
            <div className="p-2 bg-gray-800 text-white zorp-border">
              <Icon className={`h-5 w-5 ${isProcessing ? "animate-pulse" : ""}`} />
            </div>
            <span className="font-black">{config.title}</span>
          </CardTitle>
        </CardHeader>
        <CardContent className="p-6 space-y-6">
          <div className="space-y-3">
            <p className="text-gray-600 font-medium text-lg">{config.description}</p>
            {filename && (
              <div className="p-3 bg-gray-50 zorp-border">
                <p className="font-bold">FILE: {filename}</p>
              </div>
            )}
          </div>

          {stage !== "idle" && stage !== "error" && (
            <div className="space-y-3">
              <div className="flex justify-between font-bold">
                <span>PROGRESS</span>
                <span style={{ color: "#0000ee" }}>{Math.round(animatedProgress)}%</span>
              </div>
              <Progress value={animatedProgress} className="w-full h-4" />
            </div>
          )}

          {stage === "completed" && (
            <Alert className="zorp-border bg-green-50">
              <CheckCircle2 className="h-4 w-4 text-green-600" />
              <AlertDescription className="font-bold text-green-800">
                YOUR SERMON HAS BEEN SUCCESSFULLY PROCESSED! YOU CAN NOW VIEW THE GENERATED CONTENT.
              </AlertDescription>
            </Alert>
          )}

          {stage === "error" && error && (
            <Alert variant="destructive" className="zorp-border bg-red-50">
              <AlertCircle className="h-4 w-4" />
              <AlertDescription className="font-bold">{error.toUpperCase()}</AlertDescription>
            </Alert>
          )}

          {showActions && (
            <div className="flex space-x-3 pt-4">
              {stage === "error" && onRetry && (
                <Button onClick={onRetry} className="zorp-button">
                  <RotateCcw className="h-4 w-4 mr-2" />
                  RETRY
                </Button>
              )}
              {isProcessing && onCancel && (
                <Button onClick={onCancel} className="zorp-button-orange">
                  <X className="h-4 w-4 mr-2" />
                  CANCEL
                </Button>
              )}
            </div>
          )}

          {isProcessing && (
            <div className="p-3 bg-gray-50 zorp-border">
              <p className="text-sm font-bold text-gray-600">
                THIS MAY TAKE A FEW MINUTES DEPENDING ON THE LENGTH OF YOUR SERMON.
              </p>
            </div>
          )}
        </CardContent>
      </Card>
    </div>
  )
}
