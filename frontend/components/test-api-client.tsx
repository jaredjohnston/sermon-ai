'use client'

import { useState } from 'react'
import { Button } from '@/components/ui/button'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
import { useApiClient } from '@/lib/api-client'
import { ContentTemplatePublic, PatternExtractionResponse } from '@/types/api'

export function TestApiClient() {
  const apiClient = useApiClient()
  const [loading, setLoading] = useState(false)
  const [result, setResult] = useState<string>('')

  const testHealthCheck = async () => {
    setLoading(true)
    try {
      const health = await apiClient.health()
      setResult(`Health check successful: ${JSON.stringify(health, null, 2)}`)
    } catch (error) {
      setResult(`Health check failed: ${error}`)
    } finally {
      setLoading(false)
    }
  }

  const testListTemplates = async () => {
    setLoading(true)
    try {
      const templates = await apiClient.listContentTemplates()
      setResult(`Templates loaded: ${JSON.stringify(templates, null, 2)}`)
    } catch (error) {
      setResult(`Templates failed: ${error}`)
    } finally {
      setLoading(false)
    }
  }

  const testPatternExtraction = async () => {
    setLoading(true)
    try {
      const result = await apiClient.extractTemplatePatterns({
        content_type_name: 'small group guide',
        examples: [
          'Welcome to our study of John 3:16. Begin with prayer and share what God has been teaching you this week.',
          'Today we explore the parable of the lost sheep. Start with worship and discuss how you have experienced God\'s pursuit in your life.'
        ],
        description: 'Small group discussion guides with prayer and reflection'
      })
      setResult(`Pattern extraction: ${JSON.stringify(result, null, 2)}`)
    } catch (error) {
      setResult(`Pattern extraction failed: ${JSON.stringify(error, null, 2)}`)
    } finally {
      setLoading(false)
    }
  }

  const testListTranscripts = async () => {
    setLoading(true)
    try {
      const transcripts = await apiClient.listTranscripts(5, 0)
      setResult(`Transcripts loaded: ${JSON.stringify(transcripts, null, 2)}`)
    } catch (error) {
      setResult(`Transcripts failed: ${error}`)
    } finally {
      setLoading(false)
    }
  }

  return (
    <div className="space-y-4 p-4">
      <Card>
        <CardHeader>
          <CardTitle>API Client Test Suite</CardTitle>
          <CardDescription>
            Test the API client methods to verify backend integration
          </CardDescription>
        </CardHeader>
        <CardContent className="space-y-4">
          <div className="flex flex-wrap gap-2">
            <Button onClick={testHealthCheck} disabled={loading}>
              Test Health Check
            </Button>
            <Button onClick={testListTemplates} disabled={loading}>
              Test List Templates
            </Button>
            <Button onClick={testPatternExtraction} disabled={loading}>
              Test Pattern Extraction
            </Button>
            <Button onClick={testListTranscripts} disabled={loading}>
              Test List Transcripts
            </Button>
          </div>
          
          {loading && (
            <div className="text-sm text-muted-foreground">Loading...</div>
          )}
          
          {result && (
            <div className="mt-4">
              <h4 className="font-semibold mb-2">Result:</h4>
              <pre className="bg-muted p-4 rounded-md text-sm overflow-auto max-h-96">
                {result}
              </pre>
            </div>
          )}
        </CardContent>
      </Card>
    </div>
  )
}