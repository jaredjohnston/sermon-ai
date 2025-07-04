-- Add user_profiles table for extended user information
-- This keeps Supabase auth clean while storing additional profile data

CREATE TABLE public.user_profiles (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id UUID NOT NULL REFERENCES auth.users(id) ON DELETE CASCADE,
    first_name TEXT CHECK (char_length(first_name) BETWEEN 1 AND 50),
    last_name TEXT CHECK (char_length(last_name) BETWEEN 1 AND 50),
    country TEXT CHECK (char_length(country) BETWEEN 2 AND 100),
    phone TEXT,
    bio TEXT,
    avatar_url TEXT,
    deleted_at TIMESTAMP WITH TIME ZONE,
    deleted_by UUID REFERENCES auth.users(id),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT TIMEZONE('utc', NOW()),
    created_by UUID NOT NULL REFERENCES auth.users(id),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT TIMEZONE('utc', NOW()),
    updated_by UUID NOT NULL REFERENCES auth.users(id),
    
    -- Ensure one profile per user
    UNIQUE(user_id)
);

-- Enable Row Level Security
ALTER TABLE public.user_profiles ENABLE ROW LEVEL SECURITY;

-- Create audit trigger for user_profiles
CREATE TRIGGER handle_user_profiles_audit
    BEFORE INSERT OR UPDATE ON public.user_profiles
    FOR EACH ROW
    EXECUTE FUNCTION public.handle_audit_fields();

-- RLS Policies for user_profiles
CREATE POLICY "Users can view their own profile"
    ON public.user_profiles FOR SELECT
    USING (user_id = (SELECT auth.uid()));

CREATE POLICY "Users can update their own profile"
    ON public.user_profiles FOR UPDATE
    USING (user_id = (SELECT auth.uid()));

CREATE POLICY "Users can insert their own profile"
    ON public.user_profiles FOR INSERT
    WITH CHECK (user_id = (SELECT auth.uid()));

-- Client members can view each other's basic profile info (for team collaboration)
CREATE POLICY "Client members can view teammate profiles"
    ON public.user_profiles FOR SELECT
    USING (
        user_id IN (
            SELECT cu.user_id 
            FROM public.client_users cu
            WHERE cu.client_id IN (
                SELECT client_id 
                FROM public.client_users 
                WHERE user_id = (SELECT auth.uid())
                AND deleted_at IS NULL
            )
            AND cu.deleted_at IS NULL
        )
    );

-- Add performance index
CREATE INDEX idx_user_profiles_user_id ON public.user_profiles(user_id);
CREATE INDEX idx_user_profiles_active ON public.user_profiles(user_id) WHERE deleted_at IS NULL;