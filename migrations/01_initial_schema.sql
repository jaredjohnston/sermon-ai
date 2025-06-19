-- Enable UUID extension
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- Create ENUMs
CREATE TYPE user_role AS ENUM ('owner', 'member');
CREATE TYPE subscription_status AS ENUM ('active', 'inactive', 'trial');
CREATE TYPE transcript_status AS ENUM ('processing', 'completed', 'failed');

-- Create audit trigger function
CREATE OR REPLACE FUNCTION public.handle_audit_fields()
RETURNS TRIGGER
LANGUAGE plpgsql
SECURITY INVOKER
SET search_path = public
AS $$
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
$$;

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

-- Clients policies
CREATE POLICY "Users can view active clients they belong to"
    ON public.clients FOR SELECT
    USING (
        id IN (
            SELECT client_id 
            FROM public.client_users 
            WHERE user_id = (SELECT auth.uid())
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
            WHERE user_id = (SELECT auth.uid())
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
            AND user_id = (SELECT auth.uid())
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
            WHERE user_id = (SELECT auth.uid())
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
            WHERE user_id = (SELECT auth.uid())
            AND deleted_at IS NULL
        )
        AND created_by = (SELECT auth.uid())
        AND deleted_at IS NULL
    );

-- Transcripts policies
CREATE POLICY "Users can view active transcripts from their active client"
    ON public.transcripts FOR SELECT
    USING (
        client_id IN (
            SELECT client_id 
            FROM public.client_users 
            WHERE user_id = (SELECT auth.uid())
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
            WHERE user_id = (SELECT auth.uid())
            AND deleted_at IS NULL
        )
        AND created_by = (SELECT auth.uid())
        AND deleted_at IS NULL
    );

-- Create indexes for performance
-- Optimizes RLS policies: find clients user belongs to
CREATE INDEX idx_client_users_user_id ON public.client_users(user_id);
-- Optimizes client management: find all users in a client
CREATE INDEX idx_client_users_client_id ON public.client_users(client_id);
-- Optimizes video listings: find all videos for a client
CREATE INDEX idx_videos_client_id ON public.videos(client_id);
-- Optimizes RLS policies: find videos by uploader
CREATE INDEX idx_videos_user_id ON public.videos(user_id);
-- Optimizes transcript listings: find all transcripts for a client
CREATE INDEX idx_transcripts_client_id ON public.transcripts(client_id);
-- Optimizes job tracking: find transcript by external request ID
CREATE INDEX idx_transcripts_request_id ON public.transcripts(request_id);
-- Optimizes video detail pages: find transcript for specific video
CREATE INDEX idx_transcripts_video_id ON public.transcripts(video_id);
-- Optimizes RLS policies: find transcripts by creator
CREATE INDEX idx_transcripts_user_id ON public.transcripts(user_id);

-- Optimized indexes for common queries
-- CRITICAL: Optimizes RLS policies for active videos only
CREATE INDEX idx_active_videos ON public.videos(client_id) WHERE deleted_at IS NULL;
-- CRITICAL: Optimizes RLS policies for active transcripts only
CREATE INDEX idx_active_transcripts ON public.transcripts(client_id) WHERE deleted_at IS NULL;
-- Optimizes job monitoring: find transcripts by status (active only)
CREATE INDEX idx_transcripts_status ON public.transcripts(status) WHERE deleted_at IS NULL;

-- CRITICAL: Optimizes client lookups in RLS policies
CREATE INDEX idx_clients_active ON public.clients(id) WHERE deleted_at IS NULL;
-- Optimizes billing operations: filter by subscription tier
CREATE INDEX idx_clients_subscription_status ON public.clients(subscription_status) WHERE deleted_at IS NULL;
-- Optimizes admin functions: find clients by creator
CREATE INDEX idx_clients_created_by ON public.clients(created_by) WHERE deleted_at IS NULL; 

-- Updated schema pasted directly from supabase
-- WARNING: This schema is for context only and is not meant to be run.
-- Table order and constraints may not be valid for execution.

CREATE TABLE public.client_users (
  client_id uuid NOT NULL,
  user_id uuid NOT NULL,
  deleted_at timestamp with time zone,
  deleted_by uuid,
  created_by uuid NOT NULL,
  updated_by uuid NOT NULL,
  role USER-DEFINED NOT NULL DEFAULT 'member'::user_role,
  created_at timestamp with time zone DEFAULT timezone('utc'::text, now()),
  updated_at timestamp with time zone DEFAULT timezone('utc'::text, now()),
  CONSTRAINT client_users_pkey PRIMARY KEY (client_id, user_id),
  CONSTRAINT client_users_created_by_fkey FOREIGN KEY (created_by) REFERENCES auth.users(id),
  CONSTRAINT client_users_user_id_fkey FOREIGN KEY (user_id) REFERENCES auth.users(id),
  CONSTRAINT client_users_deleted_by_fkey FOREIGN KEY (deleted_by) REFERENCES auth.users(id),
  CONSTRAINT client_users_client_id_fkey FOREIGN KEY (client_id) REFERENCES public.clients(id),
  CONSTRAINT client_users_updated_by_fkey FOREIGN KEY (updated_by) REFERENCES auth.users(id)
);
CREATE TABLE public.clients (
  name text NOT NULL CHECK (char_length(name) >= 2 AND char_length(name) <= 100),
  deleted_at timestamp with time zone,
  deleted_by uuid,
  created_by uuid NOT NULL,
  updated_by uuid NOT NULL,
  id uuid NOT NULL DEFAULT uuid_generate_v4(),
  subscription_status USER-DEFINED NOT NULL DEFAULT 'trial'::subscription_status,
  created_at timestamp with time zone DEFAULT timezone('utc'::text, now()),
  updated_at timestamp with time zone DEFAULT timezone('utc'::text, now()),
  CONSTRAINT clients_pkey PRIMARY KEY (id),
  CONSTRAINT clients_deleted_by_fkey FOREIGN KEY (deleted_by) REFERENCES auth.users(id),
  CONSTRAINT clients_created_by_fkey FOREIGN KEY (created_by) REFERENCES auth.users(id),
  CONSTRAINT clients_updated_by_fkey FOREIGN KEY (updated_by) REFERENCES auth.users(id)
);
CREATE TABLE public.transcripts (
  client_id uuid NOT NULL,
  video_id uuid NOT NULL,
  raw_transcript jsonb,
  processed_transcript jsonb,
  error_message text,
  deleted_at timestamp with time zone,
  deleted_by uuid,
  created_by uuid NOT NULL,
  updated_by uuid NOT NULL,
  id uuid NOT NULL DEFAULT uuid_generate_v4(),
  status USER-DEFINED NOT NULL DEFAULT 'processing'::transcript_status,
  created_at timestamp with time zone DEFAULT timezone('utc'::text, now()),
  updated_at timestamp with time zone DEFAULT timezone('utc'::text, now()),
  request_id text,
  user_id uuid NOT NULL,
  CONSTRAINT transcripts_pkey PRIMARY KEY (id),
  CONSTRAINT transcripts_deleted_by_fkey FOREIGN KEY (deleted_by) REFERENCES auth.users(id),
  CONSTRAINT transcripts_created_by_fkey FOREIGN KEY (created_by) REFERENCES auth.users(id),
  CONSTRAINT transcripts_updated_by_fkey FOREIGN KEY (updated_by) REFERENCES auth.users(id),
  CONSTRAINT transcripts_user_id_fkey FOREIGN KEY (user_id) REFERENCES auth.users(id),
  CONSTRAINT transcripts_client_id_fkey FOREIGN KEY (client_id) REFERENCES public.clients(id),
  CONSTRAINT transcripts_video_id_fkey FOREIGN KEY (video_id) REFERENCES public.videos(id)
);
CREATE TABLE public.user_profiles (
  user_id uuid NOT NULL UNIQUE,
  first_name text CHECK (char_length(first_name) >= 1 AND char_length(first_name) <= 50),
  last_name text CHECK (char_length(last_name) >= 1 AND char_length(last_name) <= 50),
  country text CHECK (char_length(country) >= 2 AND char_length(country) <= 100),
  phone text,
  bio text,
  avatar_url text,
  deleted_at timestamp with time zone,
  deleted_by uuid,
  created_by uuid NOT NULL,
  updated_by uuid NOT NULL,
  id uuid NOT NULL DEFAULT uuid_generate_v4(),
  created_at timestamp with time zone DEFAULT timezone('utc'::text, now()),
  updated_at timestamp with time zone DEFAULT timezone('utc'::text, now()),
  CONSTRAINT user_profiles_pkey PRIMARY KEY (id),
  CONSTRAINT user_profiles_user_id_fkey FOREIGN KEY (user_id) REFERENCES auth.users(id),
  CONSTRAINT user_profiles_updated_by_fkey FOREIGN KEY (updated_by) REFERENCES auth.users(id),
  CONSTRAINT user_profiles_deleted_by_fkey FOREIGN KEY (deleted_by) REFERENCES auth.users(id),
  CONSTRAINT user_profiles_created_by_fkey FOREIGN KEY (created_by) REFERENCES auth.users(id)
);
CREATE TABLE public.videos (
  client_id uuid NOT NULL,
  filename text NOT NULL CHECK (char_length(filename) >= 1 AND char_length(filename) <= 255),
  storage_path text NOT NULL UNIQUE CHECK (char_length(storage_path) >= 1 AND char_length(storage_path) <= 512),
  content_type text NOT NULL CHECK (content_type ~ '^(video|audio)/[\w-]+$'::text),
  size_bytes bigint NOT NULL CHECK (size_bytes > 0),
  deleted_at timestamp with time zone,
  deleted_by uuid,
  created_by uuid NOT NULL,
  updated_by uuid NOT NULL,
  id uuid NOT NULL DEFAULT uuid_generate_v4(),
  metadata jsonb DEFAULT '{}'::jsonb,
  created_at timestamp with time zone DEFAULT timezone('utc'::text, now()),
  updated_at timestamp with time zone DEFAULT timezone('utc'::text, now()),
  user_id uuid NOT NULL,
  CONSTRAINT videos_pkey PRIMARY KEY (id),
  CONSTRAINT videos_updated_by_fkey FOREIGN KEY (updated_by) REFERENCES auth.users(id),
  CONSTRAINT videos_client_id_fkey FOREIGN KEY (client_id) REFERENCES public.clients(id),
  CONSTRAINT videos_deleted_by_fkey FOREIGN KEY (deleted_by) REFERENCES auth.users(id),
  CONSTRAINT videos_created_by_fkey FOREIGN KEY (created_by) REFERENCES auth.users(id),
  CONSTRAINT videos_user_id_fkey FOREIGN KEY (user_id) REFERENCES auth.users(id)
);