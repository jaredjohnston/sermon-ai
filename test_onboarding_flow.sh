#!/bin/bash

# Test script for onboarding flow
# Replace with your actual API base URL and auth token

API_BASE="http://localhost:8000/api/v1"
AUTH_TOKEN="your-auth-token-here"

echo "🚀 Testing SermonAI Onboarding Flow"
echo "=================================="

# Step 1: Create template from examples
echo "Step 1: Creating template from examples..."
TEMPLATE_RESPONSE=$(curl -s -X POST "$API_BASE/content/onboarding/extract-and-create-template" \
  -H "Authorization: Bearer $AUTH_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "content_type_name": "small group guide",
    "examples": [
      "Welcome to our small group! This week we explored the theme of faith and how it applies to our daily lives. Discussion questions: 1. What does faith mean to you? 2. Share a time when your faith was tested.",
      "Join us as we dive deeper into this weeks message. Key points from the sermon: Trust in Gods timing, Even in uncertainty, we can find peace. Questions for reflection: How can we practice patience in our daily walk?",
      "This weeks study focuses on community and fellowship. Main takeaways: We are stronger together, Supporting one another is biblical. Discussion starters: What does community mean in your life? How can our group better support each other?"
    ],
    "description": "Weekly discussion guides for our young adults small group"
  }'
)

echo "Template Response:"
echo $TEMPLATE_RESPONSE | jq '.'

# Extract template ID for next step
TEMPLATE_ID=$(echo $TEMPLATE_RESPONSE | jq -r '.id')

if [ "$TEMPLATE_ID" = "null" ] || [ -z "$TEMPLATE_ID" ]; then
  echo "❌ Failed to create template. Check the response above."
  exit 1
fi

echo "✅ Template created with ID: $TEMPLATE_ID"
echo ""

# Step 2: Generate demo content
echo "Step 2: Generating demo content..."
DEMO_CONTENT_RESPONSE=$(curl -s -X POST "$API_BASE/content/onboarding/generate-demo-content/$TEMPLATE_ID" \
  -H "Authorization: Bearer $AUTH_TOKEN"
)

echo "Demo Content Response:"
echo $DEMO_CONTENT_RESPONSE | jq '.'

# Check if demo content was generated successfully
DEMO_CONTENT=$(echo $DEMO_CONTENT_RESPONSE | jq -r '.content')

if [ "$DEMO_CONTENT" = "null" ] || [ -z "$DEMO_CONTENT" ]; then
  echo "❌ Failed to generate demo content. Check the response above."
  exit 1
fi

echo ""
echo "✅ Onboarding flow completed successfully!"
echo "📋 Generated Content Preview:"
echo "----------------------------"
echo $DEMO_CONTENT | jq -r '.'