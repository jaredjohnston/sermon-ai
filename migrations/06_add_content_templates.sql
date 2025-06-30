-- Migration: Add content templates for AI-powered content generation
-- Purpose: Store organization-specific content templates and structured prompts
-- Date: 2025-06-30
-- Related to: Smart content generation with custom organization styles
-- GitHub Issue: https://github.com/jaredjohnston/sermon-ai-backend/issues/6

-- Step 1: Create template_status ENUM
CREATE TYPE template_status AS ENUM ('draft', 'active', 'archived');

-- Step 2: Create content_templates table
CREATE TABLE public.content_templates (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    client_id UUID NOT NULL REFERENCES public.clients(id) ON DELETE CASCADE,
    
    -- Template identification
    name TEXT NOT NULL CHECK (char_length(name) BETWEEN 2 AND 100),
    description TEXT CHECK (char_length(description) <= 500),
    content_type_name TEXT NOT NULL CHECK (char_length(content_type_name) BETWEEN 2 AND 50),
    
    -- AI-generated structured prompt (core of the template)
    structured_prompt TEXT NOT NULL CHECK (char_length(structured_prompt) BETWEEN 50 AND 5000),
    
    -- Optional: Store original examples for future pattern refinement
    example_content JSONB DEFAULT '[]'::jsonb,
    
    -- Template configuration
    status template_status NOT NULL DEFAULT 'active',
    model_settings JSONB DEFAULT '{
        "temperature": 0.7,
        "max_tokens": 2000,
        "model": "gpt-4o"
    }'::jsonb,
    
    -- Audit fields (following existing schema pattern)
    deleted_at TIMESTAMP WITH TIME ZONE,
    deleted_by UUID REFERENCES auth.users(id),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT TIMEZONE('utc', NOW()),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT TIMEZONE('utc', NOW()),
    created_by UUID NOT NULL REFERENCES auth.users(id),
    updated_by UUID NOT NULL REFERENCES auth.users(id),
    
    -- Constraints
    UNIQUE(client_id, content_type_name, deleted_at) -- Allow same content type per client, but not when active
);

-- Step 3: Create generated_content table (track what's been generated)
CREATE TABLE public.generated_content (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    client_id UUID NOT NULL REFERENCES public.clients(id) ON DELETE CASCADE,
    transcript_id UUID NOT NULL REFERENCES public.transcripts(id) ON DELETE CASCADE,
    template_id UUID NOT NULL REFERENCES public.content_templates(id) ON DELETE CASCADE,
    
    -- Generated content
    content TEXT NOT NULL,
    content_metadata JSONB DEFAULT '{}'::jsonb,
    
    -- Generation tracking
    generation_settings JSONB DEFAULT '{}'::jsonb,
    generation_cost_cents INTEGER, -- Track API costs
    generation_duration_ms INTEGER, -- Track performance
    
    -- User customization tracking
    user_edits_count INTEGER DEFAULT 0,
    last_edited_at TIMESTAMP WITH TIME ZONE,
    
    -- Audit fields
    deleted_at TIMESTAMP WITH TIME ZONE,
    deleted_by UUID REFERENCES auth.users(id),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT TIMEZONE('utc', NOW()),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT TIMEZONE('utc', NOW()),
    created_by UUID NOT NULL REFERENCES auth.users(id),
    updated_by UUID NOT NULL REFERENCES auth.users(id)
);

-- Step 4: Enable Row Level Security
ALTER TABLE public.content_templates ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.generated_content ENABLE ROW LEVEL SECURITY;

-- Step 5: Create audit triggers (following existing pattern)
CREATE TRIGGER handle_content_templates_audit
    BEFORE INSERT OR UPDATE ON public.content_templates
    FOR EACH ROW
    EXECUTE FUNCTION public.handle_audit_fields();

CREATE TRIGGER handle_generated_content_audit
    BEFORE INSERT OR UPDATE ON public.generated_content
    FOR EACH ROW
    EXECUTE FUNCTION public.handle_audit_fields();

-- Step 6: Row Level Security Policies

-- Content Templates Policies
CREATE POLICY "Users can view active templates from their client"
    ON public.content_templates FOR SELECT
    USING (
        client_id IN (
            SELECT client_id 
            FROM public.client_users 
            WHERE user_id = (SELECT auth.uid())
            AND deleted_at IS NULL
        )
        AND deleted_at IS NULL
    );

CREATE POLICY "Users can manage templates for their client"
    ON public.content_templates FOR ALL
    USING (
        client_id IN (
            SELECT client_id 
            FROM public.client_users 
            WHERE user_id = (SELECT auth.uid())
            AND deleted_at IS NULL
        )
        AND deleted_at IS NULL
    );

-- Generated Content Policies  
CREATE POLICY "Users can view generated content from their client"
    ON public.generated_content FOR SELECT
    USING (
        client_id IN (
            SELECT client_id 
            FROM public.client_users 
            WHERE user_id = (SELECT auth.uid())
            AND deleted_at IS NULL
        )
        AND deleted_at IS NULL
    );

CREATE POLICY "Users can manage generated content for their client"
    ON public.generated_content FOR ALL
    USING (
        client_id IN (
            SELECT client_id 
            FROM public.client_users 
            WHERE user_id = (SELECT auth.uid())
            AND deleted_at IS NULL
        )
        AND deleted_at IS NULL
    );

-- Step 7: Performance indexes
CREATE INDEX idx_content_templates_client_id ON public.content_templates(client_id);
CREATE INDEX idx_content_templates_client_type ON public.content_templates(client_id, content_type_name) WHERE deleted_at IS NULL;
CREATE INDEX idx_content_templates_status ON public.content_templates(status) WHERE deleted_at IS NULL;

CREATE INDEX idx_generated_content_client_id ON public.generated_content(client_id);
CREATE INDEX idx_generated_content_transcript_id ON public.generated_content(transcript_id);
CREATE INDEX idx_generated_content_template_id ON public.generated_content(template_id);
CREATE INDEX idx_generated_content_created_at ON public.generated_content(created_at) WHERE deleted_at IS NULL;

-- Step 8: Add helpful comments
COMMENT ON TABLE public.content_templates IS 'Organization-specific content templates with AI-learned structured prompts';
COMMENT ON COLUMN public.content_templates.structured_prompt IS 'AI-extracted prompt that captures organization style, tone, and structure';
COMMENT ON COLUMN public.content_templates.example_content IS 'JSON array of original examples used to learn the pattern';
COMMENT ON COLUMN public.content_templates.model_settings IS 'AI model configuration (temperature, max_tokens, etc.)';

COMMENT ON TABLE public.generated_content IS 'Generated content instances from transcripts using templates';
COMMENT ON COLUMN public.generated_content.content IS 'The actual generated content (sermon guide, devotional, etc.)';
COMMENT ON COLUMN public.generated_content.generation_cost_cents IS 'API cost tracking in cents for analytics';
COMMENT ON COLUMN public.generated_content.user_edits_count IS 'Number of times user edited the generated content';

-- Migration completed successfully
-- Next steps: 
-- 1. Update backend models to include ContentTemplate and GeneratedContent schemas
-- 2. Create API endpoints for template management (/api/v1/content/templates/)
-- 3. Create pattern extraction service for learning from examples
-- 4. Update content generation service to use custom templates instead of hard-coded prompts