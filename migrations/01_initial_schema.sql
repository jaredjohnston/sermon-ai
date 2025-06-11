-- Enable UUID extension
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- Create ENUMs
CREATE TYPE user_role AS ENUM ('owner', 'member');
CREATE TYPE subscription_status AS ENUM ('active', 'inactive', 'trial');
CREATE TYPE transcript_status AS ENUM ('processing', 'completed', 'failed');

-- Create audit trigger function
CREATE OR REPLACE FUNCTION public.handle_audit_fields()
RETURNS TRIGGER AS $$
BEGIN
    IF (TG_OP = 'UPDATE') THEN
        NEW.updated_at = TIMEZONE('utc', NOW());
        NEW.updated_by = auth.uid();
        -- Handle soft delete
        IF (NEW.deleted_at IS NOT NULL AND OLD.deleted_at IS NULL) THEN
            NEW.deleted_by = auth.uid();
        END IF;
        RETURN NEW;
    ELSIF (TG_OP = 'INSERT') THEN
        NEW.created_at = TIMEZONE('utc', NOW());
        NEW.updated_at = TIMEZONE('utc', NOW());
        NEW.created_by = auth.uid();
        NEW.updated_by = auth.uid();
        RETURN NEW;
    END IF;
    RETURN NULL;
END;
$$ LANGUAGE plpgsql;

-- Create clients table
CREATE TABLE public.clients (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    name TEXT NOT NULL CHECK (char_length(name) BETWEEN 2 AND 100),
    subscription_status subscription_status NOT NULL DEFAULT 'trial',
    deleted_at TIMESTAMP WITH TIME ZONE,
    deleted_by UUID REFERENCES auth.users(id),
    created_at TIMESTAMP WITH TIME ZONE,
    created_by UUID NOT NULL REFERENCES auth.users(id),
    updated_at TIMESTAMP WITH TIME ZONE,
    updated_by UUID NOT NULL REFERENCES auth.users(id)
);

-- Create client_users table (links users to clients)
CREATE TABLE public.client_users (
    client_id UUID REFERENCES public.clients(id) ON DELETE CASCADE,
    user_id UUID REFERENCES auth.users(id) ON DELETE CASCADE,
    role user_role NOT NULL DEFAULT 'member',
    deleted_at TIMESTAMP WITH TIME ZONE,
    deleted_by UUID REFERENCES auth.users(id),
    created_at TIMESTAMP WITH TIME ZONE,
    created_by UUID NOT NULL REFERENCES auth.users(id),
    updated_at TIMESTAMP WITH TIME ZONE,
    updated_by UUID NOT NULL REFERENCES auth.users(id),
    PRIMARY KEY (client_id, user_id)
);

-- Create videos table
CREATE TABLE public.videos (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    client_id UUID NOT NULL REFERENCES public.clients(id) ON DELETE CASCADE,
    user_id UUID NOT NULL REFERENCES auth.users(id),
    filename TEXT NOT NULL CHECK (char_length(filename) BETWEEN 1 AND 255),
    storage_path TEXT NOT NULL CHECK (char_length(storage_path) BETWEEN 1 AND 512),
    content_type TEXT NOT NULL CHECK (content_type ~ '^(video|audio)/[\w-]+$'),
    size_bytes BIGINT NOT NULL CHECK (size_bytes > 0),
    deleted_at TIMESTAMP WITH TIME ZONE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT TIMEZONE('utc', NOW()),
    metadata JSONB DEFAULT '{}'::jsonb,
    created_by UUID NOT NULL REFERENCES auth.users(id),
    updated_by UUID REFERENCES auth.users(id),
    UNIQUE (storage_path)
);

-- Create transcripts table
CREATE TABLE public.transcripts (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    client_id UUID NOT NULL REFERENCES public.clients(id) ON DELETE CASCADE,
    video_id UUID NOT NULL REFERENCES public.videos(id) ON DELETE CASCADE,
    user_id UUID NOT NULL REFERENCES auth.users(id),
    raw_transcript JSONB,
    processed_transcript JSONB,
    status transcript_status NOT NULL DEFAULT 'processing',
    error_message TEXT,
    request_id TEXT,
    deleted_at TIMESTAMP WITH TIME ZONE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT TIMEZONE('utc', NOW()),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT TIMEZONE('utc', NOW()),
    created_by UUID NOT NULL REFERENCES auth.users(id),
    updated_by UUID REFERENCES auth.users(id)
);

-- Create updated_at trigger function
CREATE OR REPLACE FUNCTION public.handle_updated_at()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = TIMEZONE('utc', NOW());
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

-- Create triggers for updated_at
CREATE TRIGGER handle_clients_updated_at
    BEFORE UPDATE ON public.clients
    FOR EACH ROW
    EXECUTE FUNCTION public.handle_updated_at();

CREATE TRIGGER handle_transcripts_updated_at
    BEFORE UPDATE ON public.transcripts
    FOR EACH ROW
    EXECUTE FUNCTION public.handle_updated_at();

-- Enable Row Level Security on all tables
ALTER TABLE public.clients ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.client_users ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.videos ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.transcripts ENABLE ROW LEVEL SECURITY;

-- Create audit triggers
CREATE TRIGGER handle_clients_audit
    BEFORE INSERT OR UPDATE ON public.clients
    FOR EACH ROW
    EXECUTE FUNCTION public.handle_audit_fields();

CREATE TRIGGER handle_client_users_audit
    BEFORE INSERT OR UPDATE ON public.client_users
    FOR EACH ROW
    EXECUTE FUNCTION public.handle_audit_fields();

CREATE TRIGGER handle_videos_audit
    BEFORE INSERT OR UPDATE ON public.videos
    FOR EACH ROW
    EXECUTE FUNCTION public.handle_audit_fields();

CREATE TRIGGER handle_transcripts_audit
    BEFORE INSERT OR UPDATE ON public.transcripts
    FOR EACH ROW
    EXECUTE FUNCTION public.handle_audit_fields();

-- Updated RLS Policies

-- Clients policies
CREATE POLICY "Users can view active clients they belong to"
    ON public.clients FOR SELECT
    USING (
        id IN (
            SELECT client_id 
            FROM public.client_users 
            WHERE user_id = auth.uid()
            AND deleted_at IS NULL
        )
        AND deleted_at IS NULL
    );

-- Client users policies
CREATE POLICY "Users can view active members of their active client"
    ON public.client_users FOR SELECT
    USING (
        client_id IN (
            SELECT client_id 
            FROM public.client_users 
            WHERE user_id = auth.uid()
            AND deleted_at IS NULL
        )
        AND deleted_at IS NULL
    );

CREATE POLICY "Client owners can manage users"
    ON public.client_users FOR ALL
    USING (
        EXISTS (
            SELECT 1 
            FROM public.client_users 
            WHERE client_id = client_users.client_id 
            AND user_id = auth.uid() 
            AND role = 'owner'
            AND deleted_at IS NULL
        )
        AND deleted_at IS NULL
    );

-- Videos policies
CREATE POLICY "Users can view active videos from their active client"
    ON public.videos FOR SELECT
    USING (
        client_id IN (
            SELECT client_id 
            FROM public.client_users 
            WHERE user_id = auth.uid()
            AND deleted_at IS NULL
        )
        AND deleted_at IS NULL
    );

CREATE POLICY "Users can manage their own videos"
    ON public.videos FOR ALL
    USING (
        client_id IN (
            SELECT client_id 
            FROM public.client_users 
            WHERE user_id = auth.uid()
            AND deleted_at IS NULL
        )
        AND created_by = auth.uid()
        AND deleted_at IS NULL
    );

-- Transcripts policies
CREATE POLICY "Users can view active transcripts from their active client"
    ON public.transcripts FOR SELECT
    USING (
        client_id IN (
            SELECT client_id 
            FROM public.client_users 
            WHERE user_id = auth.uid()
            AND deleted_at IS NULL
        )
        AND deleted_at IS NULL
    );

CREATE POLICY "Users can manage their own transcripts"
    ON public.transcripts FOR ALL
    USING (
        client_id IN (
            SELECT client_id 
            FROM public.client_users 
            WHERE user_id = auth.uid()
            AND deleted_at IS NULL
        )
        AND created_by = auth.uid()
        AND deleted_at IS NULL
    );

-- Create indexes for performance
CREATE INDEX idx_client_users_user_id ON public.client_users(user_id);
CREATE INDEX idx_client_users_client_id ON public.client_users(client_id);
CREATE INDEX idx_videos_client_id ON public.videos(client_id);
CREATE INDEX idx_videos_user_id ON public.videos(user_id);
CREATE INDEX idx_transcripts_client_id ON public.transcripts(client_id);
CREATE INDEX idx_transcripts_video_id ON public.transcripts(video_id);
CREATE INDEX idx_transcripts_user_id ON public.transcripts(user_id);

-- Optimized indexes for common queries
CREATE INDEX idx_active_videos ON public.videos(client_id) WHERE deleted_at IS NULL;
CREATE INDEX idx_active_transcripts ON public.transcripts(client_id) WHERE deleted_at IS NULL;
CREATE INDEX idx_transcripts_status ON public.transcripts(status) WHERE deleted_at IS NULL; 